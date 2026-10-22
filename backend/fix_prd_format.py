"""
One-time cleanup: convert PRD / description / task text that was saved as JSON
text into readable plain text (what the frontend and exports expect).

Run from the backend folder, with the backend STOPPED:

    python fix_prd_format.py            # preview only, changes nothing
    python fix_prd_format.py --apply    # backs up specpilot.db, then converts

Only values that are JSON lists/dicts are changed. Plain text, sprint plans
and task dependencies are left alone. Safe to run more than once.
"""

import json
import shutil
import sqlite3
import sys
from datetime import datetime

from app.services.prd_format import to_readable

DB_PATH = "specpilot.db"

PROJECT_FIELDS = [
    "overview", "ai_problem_statement", "proposed_solution", "target_audience",
    "business_value", "major_features", "expected_outcome",
    "product_overview", "prd_problem_statement", "goals_and_objectives",
    "prd_target_users", "functional_requirements", "user_workflows",
    "business_rules", "non_functional_requirements",
    "assumptions_and_dependencies", "acceptance_criteria",
]
TASK_FIELDS = ["description", "acceptance_criteria"]


def is_json_structure(value) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if text[:1] not in ("[", "{"):
        return False
    try:
        return isinstance(json.loads(text), (list, dict))
    except ValueError:
        return False


def convert_table(cur, table, fields, where=""):
    changes = []
    cur.execute(f"SELECT id, {', '.join(fields)} FROM {table} {where}")
    for row in cur.fetchall():
        row_id, values = row[0], row[1:]
        for field, value in zip(fields, values):
            if is_json_structure(value):
                changes.append((table, row_id, field, to_readable(value)))
    return changes


def main():
    apply = "--apply" in sys.argv
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    changes = convert_table(cur, "projects", PROJECT_FIELDS)
    changes += convert_table(cur, "tasks", TASK_FIELDS, "WHERE source = 'ai'")

    print(f"{len(changes)} field(s) contain JSON text.")
    for table, row_id, field, _ in changes[:40]:
        print(f"  {table} id={row_id}: {field}")
    if len(changes) > 40:
        print(f"  ... and {len(changes) - 40} more")

    if not apply:
        print("\nPreview only. Re-run with --apply to convert them.")
        return

    if not changes:
        return

    backup = f"{DB_PATH}.backup-{datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(DB_PATH, backup)
    print(f"\nBackup saved: {backup}")

    for table, row_id, field, text in changes:
        cur.execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", (text, row_id))
    conn.commit()
    print("Done.")


if __name__ == "__main__":
    main()