import requests


BASE_URL = "http://127.0.0.1:8000"

PROJECT_ID = 3

conversation = [
    "I want to build a Smart Expense & Budget Tracker.",
    "The goal is to help users track their expenses, manage budgets, and understand their spending habits so they can make better financial decisions.",
    "The target users are college students and young professionals.",
    "Users find it difficult to keep track of their daily expenses and understand where their money is being spent, which can lead to overspending and poor budget management.",
    "The application should have expense tracking, expense categorization, monthly budget creation, spending summaries, budget alerts, and expense history."
]


for turn, message in enumerate(conversation, start=1):

    print("\n" + "=" * 60)
    print(f"TURN {turn}")
    print("=" * 60)

    print("USER:")
    print(message)

    response = requests.post(
        f"{BASE_URL}/ai/agent/chat/{PROJECT_ID}",
        params={
            "message": message
        }
    )

    print("\nHTTP STATUS:")
    print(response.status_code)

    if response.status_code != 200:
        print("\nERROR:")
        print(response.text)
        break

    data = response.json()

    print("\nAGENT:")
    print(data["message"])

    print("\nMISSING FIELDS:")
    print(data["missing_fields"])

    print("\nCOMPLETENESS:")
    print(data["completeness_status"])

    print("\nSCORE:")
    print(data["completeness_score"])

    print("\nNEXT ACTION:")
    print(data["next_action"])

    print("\nCONVERSATION ID:")
    print(data["conversation_id"])

    if data["next_action"] == "generate_prd":
        print("\n" + "=" * 60)
        print("REQUIREMENT COLLECTION COMPLETE")
        print("=" * 60)
        break