from app.database import SessionLocal
from app.models import Project

USER_ID = 2  # change this to your user ID

db = SessionLocal()

try:

    projects = (
        db.query(Project)
        .filter(Project.user_id == USER_ID)
        .all()
    )

    print(f"Found {len(projects)} projects.")

    for project in projects:
        print(
            f"Deleting project: "
            f"id={project.id}, "
            f"name={project.project_name}"
        )

        db.delete(project)

    db.commit()

    print(
        f"Successfully deleted {len(projects)} projects."
    )

except Exception as e:

    db.rollback()

    print("ERROR:", e)

finally:

    db.close()

Category: Finance & Personal Management
Business Objective: Help users track income, expenses, savings, and monthly budgets.
Target Users: Students, working professionals, and individuals managing personal finances.
Problem Statement: People often lose track of their spending because their expenses are recorded across different applications or not recorded at all.
Expected Features: Expense tracking, income management, monthly budgets, spending categories, reports, charts, and financial alerts.
Technology Preferences: React, FastAPI, Python, PostgreSQL.
Timeline: 2 months.
Additional Instructions: The dashboard should clearly display spending patterns and remaining budget



