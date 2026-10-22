"""
Convert structured PRD values (lists / dicts / JSON text) into readable plain
text for the Text columns on Project and Task.

The frontend, the PDF/Word export and the task generator all expect readable
text in these columns (this is what the older /ai/generate-prd path stored),
so structured output from the Generation Manager is formatted here before it
is saved. Empty values become "Not specified", matching the older PRD prompt.
"""

import json

NOT_SPECIFIED = "Not specified"


def _parse(value):
    """Decode JSON stored as text; leave anything else untouched."""
    if isinstance(value, str):
        text = value.strip()
        first = text.lstrip("*-• \t")[:1]

        if first in ("[", "{"):
            try:
                return json.loads(text)
            except ValueError:
                pass

            # several JSON objects, one per line (optionally bulleted)
            items = []
            for line in text.splitlines():
                line = line.strip().lstrip("*-• \t").strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except ValueError:
                    return value  # not JSON lines after all, leave it alone
            if items:
                return items

    return value


def _is_empty(value) -> bool:
    value = _parse(value)
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in ("", "None", NOT_SPECIFIED)
    if isinstance(value, (list, tuple)):
        return all(_is_empty(v) for v in value)
    if isinstance(value, dict):
        return all(_is_empty(v) for v in value.values())
    return False


def _label(key) -> str:
    return str(key).replace("_", " ").capitalize()


def _item_lines(item, pad: str) -> list:
    """Lines for one element of a list."""
    if isinstance(item, dict):
        # Functional requirement: {id, requirement, source}
        if "id" in item and "requirement" in item:
            return [f"{pad}{item['id']}: {item['requirement']}"]

        # Workflow: {name, actor, trigger, steps, expected_result}
        if "name" in item and ("steps" in item or "actor" in item):
            lines = [f"{pad}{item['name']}"]
            for key in ("actor", "trigger"):
                if not _is_empty(item.get(key)):
                    lines.append(f"{pad}   {_label(key)}: {item[key]}")
            steps = _parse(item.get("steps"))
            if isinstance(steps, list) and steps:
                lines.append(f"{pad}   Steps:")
                for number, step in enumerate(steps, start=1):
                    lines.append(f"{pad}     {number}. {step}")
            if not _is_empty(item.get("expected_result")):
                lines.append(f"{pad}   Expected result: {item['expected_result']}")
            return lines

        # Acceptance criteria: {requirement_id, criteria: [...]}
        if "requirement_id" in item and "criteria" in item:
            lines = [f"{pad}{item['requirement_id']}:"]
            criteria = _parse(item.get("criteria"))
            if isinstance(criteria, list):
                lines.extend(f"{pad}   - {c}" for c in criteria if not _is_empty(c))
            elif not _is_empty(criteria):
                lines.append(f"{pad}   - {criteria}")
            return lines

        # Any other dict: its fields, one per line
        return _dict_lines(item, pad)

    return [f"{pad}- {item}"]


def _dict_lines(value: dict, pad: str = "") -> list:
    lines = []
    for key, val in value.items():
        val = _parse(val)
        if _is_empty(val):
            continue
        if isinstance(val, list):
            lines.append(f"{pad}{_label(key)}:")
            for item in val:
                item = _parse(item)
                if not _is_empty(item):
                    lines.extend(_item_lines(item, pad + "  "))
        elif isinstance(val, dict):
            lines.append(f"{pad}{_label(key)}:")
            lines.extend(_dict_lines(val, pad + "  "))
        else:
            lines.append(f"{pad}{_label(key)}: {val}")
    return lines


def to_readable(value) -> str:
    """Readable plain text for any value; empty values give 'Not specified'."""
    try:
        value = _parse(value)

        if _is_empty(value):
            return NOT_SPECIFIED

        if isinstance(value, str):
            return value

        if isinstance(value, list):
            lines = []
            for item in value:
                item = _parse(item)
                if not _is_empty(item):
                    lines.extend(_item_lines(item, ""))
            return "\n".join(lines) if lines else NOT_SPECIFIED

        if isinstance(value, dict):
            lines = _dict_lines(value)
            return "\n".join(lines) if lines else NOT_SPECIFIED

        return str(value)

    except Exception:
        # Never lose data because of an unexpected shape.
        return json.dumps(value, ensure_ascii=False)