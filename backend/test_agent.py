from app.agent.runner import (
    create_empty_requirements,
    process_message
)


# =========================================================
# CONVERSATION
# =========================================================

conversation = [
    "I want to build an AI learning assistant.",
    "The goal is to help students find personalized learning resources.",
    "The target users are college students.",
    "Students struggle to find the right study material.",
    "The application should have an AI chatbot, course recommendations, and progress tracking.",
    "I want to use Python and FastAPI.",
    "The project should be completed in 3 months."
]


# =========================================================
# INITIAL REQUIREMENTS
# =========================================================

requirements = create_empty_requirements()


# =========================================================
# PROCESS CONVERSATION
# =========================================================

for turn, user_message in enumerate(conversation, start=1):

    print("\n")
    print("=" * 60)
    print(f"TURN {turn}")
    print("=" * 60)

    print("\nUSER:")
    print(user_message)

    result = process_message(
        user_message,
        requirements
    )

    requirements = result["requirements"]

    print("\nAGENT:")
    print(result.get("agent_response"))

    print("\nMISSING FIELDS:")
    print(result.get("missing_fields"))

    print("\nCOMPLETENESS:")
    print(result.get("completeness_status"))

    print("\nSCORE:")
    print(result.get("completeness_score"))

    print("\nNEXT ACTION:")
    print(result.get("next_action"))

    print("\nREQUIREMENTS:")

    for field, data in requirements.items():
        print(f"{field}: {data['value']}")

    # =====================================================
    # STOP WHEN REQUIREMENTS ARE COMPLETE
    # =====================================================

    if result.get("next_action") == "generate_prd":

        print("\n")
        print("=" * 60)
        print("REQUIREMENT COLLECTION COMPLETE")
        print("=" * 60)

        print("\nThe agent is ready to generate the PRD.")

        break