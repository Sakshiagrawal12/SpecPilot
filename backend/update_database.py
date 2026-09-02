import sqlite3

DATABASE_PATH = "specpilot.db"


connection = sqlite3.connect(DATABASE_PATH)

cursor = connection.cursor()


print("====================================")
print("UPDATING DATABASE")
print("====================================")


# Get existing columns
cursor.execute("PRAGMA table_info(projects)")

existing_columns = {
    row[1]
    for row in cursor.fetchall()
}


print("Existing project columns:")
print(existing_columns)


# ---------------------------------------------------------
# DESCRIPTION
# ---------------------------------------------------------

if "description" not in existing_columns:

    cursor.execute(
        """
        ALTER TABLE projects
        ADD COLUMN description TEXT
        """
    )

    print("Added: description")

else:

    print("Already exists: description")


# ---------------------------------------------------------
# AI DESCRIPTION
# ---------------------------------------------------------

if "ai_description" not in existing_columns:

    cursor.execute(
        """
        ALTER TABLE projects
        ADD COLUMN ai_description TEXT
        """
    )

    print("Added: ai_description")

else:

    print("Already exists: ai_description")


# ---------------------------------------------------------
# PRD
# ---------------------------------------------------------

if "prd" not in existing_columns:

    cursor.execute(
        """
        ALTER TABLE projects
        ADD COLUMN prd TEXT
        """
    )

    print("Added: prd")

else:

    print("Already exists: prd")


# ---------------------------------------------------------
# TASK BREAKDOWN
# ---------------------------------------------------------

if "task_breakdown" not in existing_columns:

    cursor.execute(
        """
        ALTER TABLE projects
        ADD COLUMN task_breakdown TEXT
        """
    )

    print("Added: task_breakdown")

else:

    print("Already exists: task_breakdown")


# ---------------------------------------------------------
# SPRINT PLAN
# ---------------------------------------------------------

if "sprint_plan" not in existing_columns:

    cursor.execute(
        """
        ALTER TABLE projects
        ADD COLUMN sprint_plan TEXT
        """
    )

    print("Added: sprint_plan")

else:

    print("Already exists: sprint_plan")


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

connection.commit()


print()
print("Database update completed successfully.")


# ---------------------------------------------------------
# VERIFY
# ---------------------------------------------------------

cursor.execute("PRAGMA table_info(projects)")

columns = cursor.fetchall()


print()
print("====================================")
print("PROJECT TABLE COLUMNS")
print("====================================")


for column in columns:

    print(
        f"ID: {column[0]} | "
        f"Name: {column[1]} | "
        f"Type: {column[2]}"
    )


connection.close()