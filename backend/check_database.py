from app.database import SessionLocal
from app.models import Project


db = SessionLocal()

print("====================================")
print("PROJECTS IN DATABASE")
print("====================================")

projects = db.query(Project).all()

for project in projects:

    print(
        "ID:",
        project.id,
        "| User ID:",
        project.user_id,
        "| Name:",
        project.project_name
    )

db.close()
