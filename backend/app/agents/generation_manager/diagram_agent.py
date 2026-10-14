import re 

from app.ai.llm import llm


# =========================================================
# DIAGRAM PROMPT
# =========================================================

DIAGRAM_PROMPT = """
You are an expert Systems Architect.

Convert the following user workflow into a valid Mermaid.js
flowchart using `graph TD`.

USER WORKFLOW:
{workflow_text}


=========================================================
RULES
=========================================================

1. Return ONLY valid Mermaid.js syntax.

2. The output MUST start with:
   graph TD

3. Do NOT return Markdown code fences.

4. Do NOT add explanations.

5. Do NOT add text before or after the Mermaid code.

6. Preserve the exact order of the workflow.

7. Represent user actions and system actions clearly.

8. Keep node labels short and readable.

9. Do NOT invent workflow steps.

10. Do NOT add functionality that is not present
    in the supplied workflow.

11. Use simple Mermaid syntax compatible with Mermaid.js v10.


=========================================================
EXAMPLE
=========================================================

Input:

1. User logs in.
2. User searches for a destination.
3. System displays destinations.
4. User selects a destination.
5. System generates an itinerary.


Output:

graph TD
    A[1. User Logs In] --> B[2. Search Destination]
    B --> C[3. Display Destinations]
    C --> D[4. Select Destination]
    D --> E[5. Generate Itinerary]
"""


# =========================================================
# DIAGRAM AGENT
# =========================================================

class DiagramAgent:

    def generate_diagram(
        self,
        workflow_text: str
    ) -> str:

        if not workflow_text or not workflow_text.strip():

            raise ValueError(
                "Workflow text cannot be empty."
            )


        prompt = DIAGRAM_PROMPT.format(
            workflow_text=workflow_text
        )


        print(
            "========================================"
        )

        print(
            "GENERATING WORKFLOW DIAGRAM"
        )

        print(
            "WORKFLOW LENGTH:",
            len(workflow_text)
        )

        print(
            "PROMPT LENGTH:",
            len(prompt)
        )

        print(
            "========================================"
        )


        response = llm.generate(
            prompt
        )


        response = response.strip()


        # =================================================
        # CLEAN MARKDOWN FENCES
        # =================================================

        match = re.search(
            r"```mermaid\s*(.*?)\s*```",
            response,
            re.DOTALL | re.IGNORECASE
        )


        if match:

            response = match.group(1).strip()


        else:

            response = (
                response
                .replace("```mermaid", "")
                .replace("```", "")
                .strip()
            )


        # =================================================
        # VALIDATION
        # =================================================

        if not response.startswith("graph TD"):

            raise RuntimeError(
                "Diagram Agent returned invalid Mermaid syntax."
            )


        print(
            "MERMAID GENERATED:"
        )

        print(
            response
        )


        return response


# =========================================================
# INSTANCE
# =========================================================

diagram_agent = DiagramAgent()