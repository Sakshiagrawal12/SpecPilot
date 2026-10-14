ALL_FIELDS = [
    "project_name",
    "category",
    "business_objective",
    "problem_statement",
    "target_users",
    "expected_features",
    "technology_preferences",
    "timeline",
    "additional_instructions",
]

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

# -------------------------------------------------------------------
# Core question prompts (Static 'example' keys removed in favor of 
# dynamic LLM generation via RequirementQuestionPlanner)
# -------------------------------------------------------------------
QUESTIONS = {
    "category": {
        "text": "What category does this project belong to?",
        "context_prompt": "Suggest 3-4 broad project domains relevant to the project name."
    },
    "business_objective": {
        "text": "What is the main goal or objective of this project?",
        "context_prompt": "Provide a goal example tailored strictly to the project's category."
    },
    "problem_statement": {
        "text": "What specific problem or pain point should this project solve?",
        "context_prompt": "Provide a realistic problem example tailored to the existing target users and project goal."
    },
    "target_users": {
        "text": "Who are the main target users or primary audience of this project?",
        "context_prompt": "Suggest target user profiles specifically relevant to this project type."
    },
    "expected_features": {
        "text": "What key features or capabilities would you like this project to provide?",
        "context_prompt": "Provide key feature examples relevant to the project's goal and target users."
    },
    "technology_preferences": {
        "text": "Do you have any preferred technologies, frameworks, databases, or tools for this project?",
        "context_prompt": "Suggest common tech stacks for this type of application or accept 'no preference'."
    },
    "timeline": {
        "text": "Do you have a target timeline or deadline for completing this project?",
        "context_prompt": "Provide typical timeframe examples like '3 months' or a target date."
    },
    "additional_instructions": {
        "text": "Is there anything else you would like considered (e.g., security, compliance, integrations)?",
        "context_prompt": "Suggest relevant non-functional constraints or accept 'none'."
    }
}

FIELD_EXPLANATIONS = {
    "category": (
        "The category is the broad domain your project fits into — "
        "such as event planning, healthcare, education, or e-commerce."
    ),
    "business_objective": (
        "This is the core outcome your project aims to achieve for its owners or users."
    ),
    "problem_statement": (
        "This describes the exact frustration, inefficiency, or difficulty current users face."
    ),
    "target_users": (
        "These are the specific groups or roles who will interact with the solution."
    ),
    "expected_features": (
        "These are the key functional requirements and tools the software must include."
    ),
    "technology_preferences": (
        "The preferred tech stack, databases, cloud platforms, or AI models."
    ),
    "timeline": (
        "The estimated duration or strict completion milestone for this release."
    ),
    "additional_instructions": (
        "Additional guidelines, design constraints, compliance, or integration requirements."
    ),
}

# -------------------------------------------------------------------
# Expanded Signal Patterns to capture user requests for suggestions/advice
# -------------------------------------------------------------------
QUESTION_SIGNAL_PATTERNS = [
    r"\bwhat (does|is|are|do)\b",
    r"\bwhat.{0,15}\bmean",
    r"\bcan you explain\b",
    r"\bexplain\b",
    r"\bgive.{0,10}example\b",
    r"\bfor example\b",
    r"\bi don'?t (get|understand|know)\b",
    r"\bi didn'?t (get|understand|know)\b",
    r"\bunable to understand\b",
    r"\bconfus(ed|ing)\b",
    r"\bsuggest\b",
    r"\bshould i\b",
    r"\bwhich (one|user|feature|technology)\b",
    r"\bhelp me (choose|define|decide)\b",
    r"\?$",
]

FIELD_SYNONYMS = {
    "category": ["category", "type of project", "domain", "industry"],
    "business_objective": ["objective", "goal", "business objective", "purpose", "aim"],
    "target_users": ["target users", "users", "audience", "who uses", "persona", "customers"],
    "problem_statement": ["problem", "problem statement", "issue", "pain point", "challenge"],
    "expected_features": ["features", "functionality", "capabilities", "modules"],
    "technology_preferences": ["technology", "tech stack", "tools", "framework", "database", "languages"],
    "timeline": ["timeline", "deadline", "duration", "timeframe", "schedule"],
    "additional_instructions": ["additional instructions", "extra requirements", "constraints", "notes"],
}

FIELD_CONFIDENCE_THRESHOLDS = {
    "category": 0.3,
    "business_objective": 0.55,
    "target_users": 0.45,
    "problem_statement": 0.55,
    "expected_features": 0.5,
    "technology_preferences": 0.35,
    "timeline": 0.3,
    "additional_instructions": 0.0,
}

MAX_CLARIFICATION_ATTEMPTS = 2