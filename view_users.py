import sqlite3

def view_users():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.id, users.first_name, users.last_name, users.email, roles.name
        FROM users
        JOIN roles ON users.role_id = roles.id
    ''')
    users = cursor.fetchall()
    conn.close()

    print("\n📋 Registered Users:\n")
    print("{:<5} {:<15} {:<15} {:<25} {:<15}".format("ID", "First Name", "Last Name", "Email", "Role"))
    print("-" * 80)
    for user in users:
        print("{:<5} {:<15} {:<15} {:<25} {:<15}".format(user[0], user[1], user[2], user[3], user[4]))

if __name__ == "__main__":
    view_users()