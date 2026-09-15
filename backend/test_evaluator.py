from app.agent.evaluator import evaluate_project


project_data = {
    "project_name": "AI Student Learning Assistant",

    "business_objective": (
        "Help students learn more effectively"
    ),

    "target_users": "College students",

    "problem_statement": (
        "Students struggle to find personalized learning resources"
    ),

    "expected_features": (
        "AI chatbot, recommendations, progress tracking"
    ),

    "technology_preferences": "Python, FastAPI",

    "timeline": "3 months",

    "additional_instructions": ""
}


result = evaluate_project(project_data)

print(result)