import database
from models import User

def authenticate(username, password):
    conn = database.get_users_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if row:
        return User(id=row['id'], username=row['username'], password=row['password'], role=row['role'], name=row['name'])
    return None

def get_user_by_id(user_id):
    conn = database.get_users_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if row:
        return User(id=row['id'], username=row['username'], password=row['password'], role=row['role'], name=row['name'])
    return None
