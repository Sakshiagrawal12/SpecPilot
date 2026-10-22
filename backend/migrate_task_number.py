from sqlalchemy import text

from app.database import engine

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT project_id, COUNT(*), MIN(task_number), MAX(task_number) "
        "FROM tasks GROUP BY project_id ORDER BY project_id"
    ))
    print("project_id | tasks | first | last")
    for r in rows:
        print(f"{r[0]:>10} | {r[1]:>5} | {r[2]} | {r[3]}")