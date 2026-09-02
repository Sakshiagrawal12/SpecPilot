
from sqlalchemy import inspect, text

from app.database import engine


# =========================================================
# DATABASE MIGRATION
# =========================================================

def add_missing_columns():

    inspector = inspect(engine)

    print("====================================")
    print("SPEC PILOT DATABASE MIGRATION")
    print("====================================")

    # -----------------------------------------------------
    # PROJECTS TABLE
    # -----------------------------------------------------

    project_columns = {
        column["name"]
        for column in inspector.get_columns("projects")
    }

    required_project_columns = {
        "ai_problem_statement": "TEXT",
        "target_audience": "TEXT",
    }

    with engine.begin() as connection:

        for column_name, column_type in required_project_columns.items():

            if column_name not in project_columns:

                print(
                    f"Adding missing column: "
                    f"projects.{column_name}"
                )

                connection.execute(
                    text(
                        f"""
                        ALTER TABLE projects
                        ADD COLUMN {column_name} {column_type}
                        """
                    )
                )

            else:

                print(
                    f"Column already exists: "
                    f"projects.{column_name}"
                )

    print()
    print("====================================")
    print("DATABASE MIGRATION COMPLETED")
    print("====================================")


if __name__ == "__main__":
    add_missing_columns()
