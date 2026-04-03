import database
from models import User, Book, Request, IssuedBook
from datetime import datetime, timedelta
FINE_PER_DAY = 10 
# --- USER MANAGEMENT ---
def add_user(username, password, role, name):
    conn = database.get_users_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)",
                       (username, password, role, name))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        return False
    finally:
        conn.close()

def delete_user(username):
    conn = database.get_users_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = %s AND role != 'admin'", (username,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        conn.close()

def get_all_users():
    conn = database.get_users_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        return [User(**row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_username_by_id(user_id):
    conn = database.get_users_db_connection()
    if not conn: return "Unknown"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else "Unknown"
    finally:
        conn.close()

# --- BOOK MANAGEMENT ---
def add_book(title, author, keywords, copies):
    conn = database.get_books_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (title, author, keywords, total_copies, available_copies) VALUES (%s, %s, %s, %s, %s)",
                       (title, author, keywords, copies, copies))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding book: {e}")
        return False
    finally:
        conn.close()

def remove_book(book_id):
    conn = database.get_books_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error removing book: {e}")
        return False
    finally:
        conn.close()

def search_books(query):
    conn = database.get_books_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        q = f"%{query}%"
        cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s OR keywords LIKE %s", (q, q, q))
        return [Book(**row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_book_by_id(book_id):
    conn = database.get_books_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        row = cursor.fetchone()
        return Book(**row) if row else None
    finally:
        conn.close()

# --- REQUEST MANAGEMENT ---
def create_request(user_id, book_id, req_type):
    conn = database.get_books_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        # Verify book exists
        book = get_book_by_id(book_id)
        if not book:
            return False
            
        if req_type == 'issue' and book.available_copies <= 0:
            print("No copies available to issue.")
            return False
            
        cursor.execute("INSERT INTO requests (user_id, book_id, type, status) VALUES (%s, %s, %s, 'pending')",
                       (user_id, book_id, req_type))
        conn.commit()
        return True
    finally:
        conn.close()

def get_pending_requests():
    conn = database.get_books_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        #cursor.execute("SELECT * FROM requests WHERE status = 'pending'")
        cursor.execute("""SELECT r.id, u.username, b.title AS book_title, r.type, r.timestamp,
           COALESCE((
               SELECT fine FROM issued_books ib
               WHERE ib.user_id = r.user_id 
               AND ib.book_id = r.book_id 
               AND ib.returned = 0
               LIMIT 1
           ), 0) AS fine
        FROM requests r
        JOIN lms_users_db.users u ON r.user_id = u.id
        JOIN books b ON r.book_id = b.id
        WHERE r.status = 'pending'
    """)
        return cursor.fetchall()
    finally:
        conn.close()

def handle_request(req_id, action): # action = 'approved' or 'rejected'
    conn = database.get_books_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM requests WHERE id = %s AND status = 'pending'", (req_id,))
        req_row = cursor.fetchone()
        if not req_row:
            return False
            
        req = Request(**req_row)
        
        if action == 'approved':
            if req.type == 'issue':
                # Check copies again
                cursor.execute("SELECT available_copies FROM books WHERE id = %s FOR UPDATE", (req.book_id,))
                avail = cursor.fetchone()['available_copies']
                if avail > 0:
                    cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = %s", (req.book_id,))
                    due = datetime.now() + timedelta(days=14)
                    cursor.execute("INSERT INTO issued_books (user_id, book_id, issue_date, due_date) VALUES (%s, %s, NOW(), %s)",
                                   (req.user_id, req.book_id, due))
                else:
                    action = 'rejected' # Auto reject if no copies
                    
            elif req.type == 'return':
                # cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = %s", (req.book_id,))
                # cursor.execute("DELETE FROM issued_books WHERE user_id = %s AND book_id = %s", (req.user_id, req.book_id))
                 cursor.execute("""SELECT * FROM issued_books WHERE user_id=%s AND book_id=%s AND returned=0 """, (req.user_id, req.book_id))
                 issued = cursor.fetchone()
                 if issued:
                    due_date = issued['due_date']
                    today = datetime.now().date()
                    fine = 0
                    if today > due_date:
                        days_late = (today - due_date).days
                        fine = days_late * FINE_PER_DAY

                    cursor.execute("UPDATE issued_books SET returned=1, fine=%s WHERE id=%s ", (fine, issued['id']))
                    cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id=%s ", (req.book_id,))
            elif req.type == 'renew':
                new_due = datetime.now() + timedelta(days=14)
                cursor.execute("UPDATE issued_books SET due_date = %s WHERE user_id = %s AND book_id = %s",
                               (new_due, req.user_id, req.book_id))
                               
        cursor.execute("UPDATE requests SET status = %s WHERE id = %s", (action, req_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error handling request: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_issued_books(user_id):
    conn = database.get_books_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT ib.book_id, b.title, ib.due_date, ib.fine FROM issued_books ib JOIN books b ON ib.book_id = b.id WHERE ib.user_id = %s AND ib.returned = 0", (user_id,))
        # return [IssuedBook(**row) for row in cursor.fetchall()]
        return cursor.fetchall()
    finally:
        conn.close()
