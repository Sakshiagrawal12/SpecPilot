import sqlite3

DB_PATH = r"D:\project\SpecPilot\backend\specpilot.db"

print("====================================")
print("DATABASE CONFIGURATION")
print("====================================")
print("Database path:")
print(DB_PATH)
print("====================================")

connection = sqlite3.connect(DB_PATH)

cursor = connection.cursor()

# Get table structure
cursor.execute("PRAGMA table_info(users)")

columns = cursor.fetchall()

print("\nUSERS TABLE COLUMNS")
print("====================================")

for column in columns:
    print(
        "ID:", column[0],
        "| Name:", column[1],
        "| Type:", column[2]
    )


# Get users using only columns that actually exist
cursor.execute("SELECT * FROM users")

users = cursor.fetchall()

print("\nUSERS IN DATABASE")
print("====================================")

if not users:

    print("NO USERS FOUND")

else:

    for user in users:
        print(user)


connection.close()