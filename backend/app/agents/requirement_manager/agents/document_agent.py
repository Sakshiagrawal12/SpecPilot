
# app/agents/requirement_manager/agents/document_agent.py

import io
import csv
import json as json_lib
import xml.etree.ElementTree as ET
from typing import Dict, Any

import pdfplumber
from docx import Document

from app.agents.shared.json_utils import extract_json
from app.ai.llm import llm


# =========================================================
# CONFIGURATION
# =========================================================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".csv",
    ".xml",
    ".json",
    ".txt",
    ".md",
}

DOCUMENT_MAX_CHARS = 12000


# =========================================================
# INTERVIEW FIELDS
# =========================================================

INTERVIEW_FIELDS = [
    "category",
    "business_objective",
    "target_users",
    "problem_statement",
    "expected_features",
    "technology_preferences",
    "timeline",
    "additional_instructions",
]


FIELD_CONFIDENCE_THRESHOLDS = {
    "category": 0.30,
    "business_objective": 0.55,
    "target_users": 0.45,
    "problem_statement": 0.55,
    "expected_features": 0.50,
    "technology_preferences": 0.35,
    "timeline": 0.30,
    "additional_instructions": 0.00,
}


# =========================================================
# TEXT EXTRACTION
# =========================================================

def extract_text_from_file(
    filename: str,
    file_bytes: bytes
) -> str:

    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        return _extract_pdf(file_bytes)

    if lower_name.endswith(".docx") or lower_name.endswith(".doc"):
        return _extract_docx(file_bytes)

    if lower_name.endswith(".csv"):
        return _extract_csv(file_bytes)

    if lower_name.endswith(".xml"):
        return _extract_xml(file_bytes)

    if lower_name.endswith(".json"):
        return _extract_json_file(file_bytes)

    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        return file_bytes.decode(
            "utf-8",
            errors="ignore"
        )

    raise ValueError(
        f"Unsupported file type: {filename}. "
        f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


# =========================================================
# PDF
# =========================================================

def _extract_pdf(file_bytes: bytes) -> str:

    text_parts = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts).strip()


# =========================================================
# DOCX / DOC
# =========================================================

def _extract_docx(file_bytes: bytes) -> str:

    document = Document(io.BytesIO(file_bytes))

    parts = [
        p.text
        for p in document.paragraphs
        if p.text.strip()
    ]

    for table in document.tables:

        for row in table.rows:

            cells = [
                cell.text.strip()
                for cell in row.cells
            ]

            if any(cells):
                parts.append(" | ".join(cells))

    return "\n".join(parts).strip()


# =========================================================
# CSV
# =========================================================

def _extract_csv(file_bytes: bytes) -> str:

    text = file_bytes.decode(
        "utf-8",
        errors="ignore"
    )

    reader = csv.reader(
        io.StringIO(text)
    )

    rows = [
        ", ".join(row)
        for row in reader
        if any(cell.strip() for cell in row)
    ]

    return "\n".join(rows).strip()


# =========================================================
# XML
# =========================================================

def _extract_xml(file_bytes: bytes) -> str:

    root = ET.fromstring(
        file_bytes.decode(
            "utf-8",
            errors="ignore"
        )
    )

    lines = []

    def walk(element, depth=0):

        text = (
            element.text or ""
        ).strip()

        if text:
            lines.append(
                f"{'  ' * depth}"
                f"{element.tag}: {text}"
            )

        for child in element:
            walk(child, depth + 1)

    walk(root)

    return "\n".join(lines).strip()


# =========================================================
# JSON
# =========================================================

def _extract_json_file(file_bytes: bytes) -> str:

    data = json_lib.loads(
        file_bytes.decode(
            "utf-8",
            errors="ignore"
        )
    )

    return json_lib.dumps(
        data,
        indent=2
    )


# =========================================================
# DOCUMENT REQUIREMENT EXTRACTION
# =========================================================

def extract_requirements_from_document(
    document_text: str,
    existing_requirements: Dict[str, Any]
) -> Dict[str, Any]:

    truncated_text = document_text[:DOCUMENT_MAX_CHARS]

    if len(truncated_text.strip()) < 50:

        return {
            "requirements": existing_requirements,
            "filled_fields": [],
            "document_summary": "",
        }

    field_list = "\n".join(
        f"- {field}"
        for field in INTERVIEW_FIELDS
    )

    prompt = f"""
You are the document requirement extraction component
of SpecPilot.

Your task is to read the uploaded project document and
extract information that is explicitly present.

=========================================================
FIELDS
=========================================================

{field_list}

=========================================================
DOCUMENT CONTENT
=========================================================

{truncated_text}

=========================================================
RULES
=========================================================

1. Only extract information explicitly stated in the document.

2. Do not invent, infer, assume, or add requirements.

3. Distinguish between:
   - clearly stated information
   - partially specified information
   - information not mentioned.

4. Give every extracted field a confidence score from
   0.0 to 1.0.

5. If a field is not mentioned, return:
   value: null
   confidence: 0.0

6. If a field is only partially specified, preserve the
   useful information but use an appropriate confidence score.

7. expected_features should be a list when multiple
   features are explicitly mentioned.

8. technology_preferences should be a list when multiple
   technologies are explicitly mentioned.

9. Do not turn suggestions, possibilities, assumptions,
   or implied information into confirmed requirements.

10. The document will be used later by the conversational
    requirement agent as context.

=========================================================
DOCUMENT SUMMARY
=========================================================

Write a concise 2-3 sentence summary containing:

- what the project is
- what problem it addresses
- who it is for
- important constraints or technologies mentioned

Do not add information that is not present.

=========================================================
RETURN JSON ONLY
=========================================================

{{
    "fields": {{
        "category": {{
            "value": null,
            "confidence": 0.0
        }},
        "business_objective": {{
            "value": null,
            "confidence": 0.0
        }},
        "target_users": {{
            "value": null,
            "confidence": 0.0
        }},
        "problem_statement": {{
            "value": null,
            "confidence": 0.0
        }},
        "expected_features": {{
            "value": null,
            "confidence": 0.0
        }},
        "technology_preferences": {{
            "value": null,
            "confidence": 0.0
        }},
        "timeline": {{
            "value": null,
            "confidence": 0.0
        }},
        "additional_instructions": {{
            "value": null,
            "confidence": 0.0
        }}
    }},
    "document_summary": ""
}}
"""

    response = llm.generate(prompt)

    result = extract_json(response)

    extracted_fields = result.get(
        "fields",
        {}
    )

    filled_fields = []

    for field in INTERVIEW_FIELDS:

        field_result = extracted_fields.get(
            field,
            {}
        )

        value = field_result.get("value")

        try:
            confidence = float(
                field_result.get(
                    "confidence",
                    0.0
                ) or 0.0
            )
        except (TypeError, ValueError):
            confidence = 0.0

        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        threshold = FIELD_CONFIDENCE_THRESHOLDS.get(
            field,
            0.5
        )

        if confidence < threshold:
            continue

        field_state = existing_requirements.setdefault(
            field,
            {
                "value": None,
                "status": "MISSING",
                "confidence": 0.0,
            }
        )

        # -------------------------------------------------
        # DOCUMENT VALUES ARE NOT USER CONFIRMATIONS
        # -------------------------------------------------

        field_state["value"] = value
        field_state["status"] = "PROVIDED"
        field_state["confidence"] = confidence
        field_state["attempts"] = 0
        field_state["question_count"] = 0
        field_state["source"] = "document"

        filled_fields.append(field)

    return {
        "requirements": existing_requirements,
        "filled_fields": filled_fields,
        "document_summary": result.get(
            "document_summary",
            ""
        ),
    }


# =========================================================
# DOCUMENT AGENT NODE
# =========================================================

def document_agent_node(
    state: Dict[str, Any]
) -> Dict[str, Any]:

    filename = state.get(
        "uploaded_filename",
        ""
    )

    file_bytes = state.get(
        "uploaded_file_bytes",
        b""
    )

    requirements = state.get(
        "requirements",
        {}
    )

    try:

        document_text = extract_text_from_file(
            filename,
            file_bytes
        )

    except Exception as e:

        return {
            "requirements": requirements,
            "document_summary": state.get(
                "document_summary",
                ""
            ),
            "document_filled_fields": [],
            "agent_response": (
                f"Unable to read the uploaded document: {e}"
            ),
            "next_action": "wait_for_user",
        }

    result = extract_requirements_from_document(
        document_text,
        requirements
    )

    filled_fields = result[
        "filled_fields"
    ]

    document_summary = result.get(
        "document_summary",
        ""
    ).strip()

    existing_summary = state.get(
        "document_summary",
        ""
    ).strip()

    if document_summary:

        new_summary = (
            f'From "{filename}": '
            f"{document_summary}"
        )

        if existing_summary:

            combined_summary = (
                f"{existing_summary}\n\n"
                f"{new_summary}"
            )

        else:

            combined_summary = new_summary

    else:

        combined_summary = existing_summary

    if filled_fields:

        readable = ", ".join(
            field.replace("_", " ")
            for field in filled_fields
        )

        response_text = (
            f"I reviewed your document and found "
            f"information for: {readable}. "
            f"I'll use that information while gathering "
            f"anything that is still unclear."
        )

    else:

        response_text = (
            "I reviewed the document, but I couldn't "
            "confidently extract any project requirements "
            "from it. I'll continue by asking you directly."
        )

    return {
        "requirements": result["requirements"],

        # Important: retained for future turns
        "document_summary": combined_summary,

        # Important: tells the requirement manager
        # what came from the document
        "document_filled_fields": filled_fields,

        "agent_response": response_text,

        # IMPORTANT:
        # document processing is finished.
        # Requirement Manager should continue.
        "next_action": "continue_requirement_interview",
    }
