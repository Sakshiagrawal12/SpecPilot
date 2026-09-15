# =========================================================
# FIELD REQUIREMENTS
# =========================================================
#
# Defines what information is required for each project
# field before AI generation should proceed.
#
# The evaluator uses these requirements to determine
# whether the user's input is sufficiently specified.
# =========================================================


FIELD_REQUIREMENTS = {

    # =====================================================
    # PROJECT NAME
    # =====================================================

    "project_name": {

        "required": True,

        "description": (
            "The name should clearly identify the software project."
        ),

        "criteria": [
            "Must identify the project.",
            "Must not be empty.",
            "Should be specific enough to distinguish the project."
        ]
    },


    # =====================================================
    # BUSINESS OBJECTIVE
    # =====================================================

    "business_objective": {

        "required": True,

        "description": (
            "Explains what the project is expected to achieve."
        ),

        "criteria": [
            "Must describe the desired outcome.",
            "Must explain the main goal of the project.",
            "Should provide enough context to understand what success means."
        ]
    },


    # =====================================================
    # TARGET USERS
    # =====================================================

    "target_users": {

        "required": True,

        "description": (
            "Identifies the people who are expected to use "
            "or benefit from the product."
        ),

        "criteria": [
            "Must identify the intended users.",
            "Users should be specific enough to understand the target audience.",
            "Avoid unnecessarily broad descriptions."
        ]
    },


    # =====================================================
    # PROBLEM STATEMENT
    # =====================================================

    "problem_statement": {

        "required": True,

        "description": (
            "Explains the real problem that the project "
            "is intended to solve."
        ),

        "criteria": [
            "Must describe the problem.",
            "Must identify who experiences the problem.",
            "Should explain the impact or difficulty caused by the problem."
        ]
    },


    # =====================================================
    # EXPECTED FEATURES
    # =====================================================

    "expected_features": {

        "required": True,

        "description": (
            "Describes the main functionality expected from "
            "the software."
        ),

        "criteria": [
            "Must identify the main functionality.",
            "Features should be relevant to the stated problem.",
            "Should provide enough information to understand the expected system capabilities."
        ]
    },


    # =====================================================
    # TECHNOLOGY PREFERENCES
    # =====================================================

    "technology_preferences": {

        "required": False,

        "description": (
            "Specifies technologies the user prefers to use."
        ),

        "criteria": [
            "If provided, technologies should be clearly identified.",
            "The system should respect explicitly stated technology preferences."
        ]
    },


    # =====================================================
    # TIMELINE
    # =====================================================

    "timeline": {

        "required": False,

        "description": (
            "Specifies the expected project duration or deadline."
        ),

        "criteria": [
            "If provided, the timeline should be understandable.",
            "The timeline should be usable when planning tasks and sprints."
        ]
    },


    # =====================================================
    # ADDITIONAL INSTRUCTIONS
    # =====================================================

    "additional_instructions": {

        "required": False,

        "description": (
            "Contains additional constraints or instructions "
            "provided by the user."
        ),

        "criteria": [
            "If provided, instructions should be considered during generation.",
            "Instructions must not override the original project scope."
        ]
    }
}