import mysql.connector
from mysql.connector import Error
import config

def get_base_connection():
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL base: {e}")
        return None

def get_users_db_connection():
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.USERS_DB
        )
        return connection
    except Error as e:
        print(f"Error connecting to users_db: {e}")
        return None

def get_books_db_connection():
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.BOOKS_DB
        )
        return connection
    except Error as e:
        print(f"Error connecting to books_db: {e}")
        return None

def init_databases():
    base_conn = get_base_connection()
    if not base_conn:
        print("Could not connect to MySQL server. Check configuration in config.py.")
        return False
        
    cursor = base_conn.cursor()
    # Create databases if they don't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.USERS_DB}")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.BOOKS_DB}")
    base_conn.commit()
    cursor.close()
    base_conn.close()

    # Initialize users_db tables
    u_conn = get_users_db_connection()
    if u_conn:
        u_cursor = u_conn.cursor()
        u_cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'librarian', 'student', 'faculty') NOT NULL,
                name VARCHAR(255) NOT NULL
            )
        """)
        
        # Seed admin user if the table is empty
        u_cursor.execute("SELECT COUNT(*) FROM users")
        if u_cursor.fetchone()[0] == 0:
            u_cursor.execute(
                "INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)",
                ("admin", "admin", "admin", "System Admin")
            )
            # Seed an initial librarian user automatically
            u_cursor.execute(
                "INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)",
                ("librarian", "librarian", "librarian", "Head Librarian")
            )
        
        u_conn.commit()
        u_cursor.close()
        u_conn.close()

    # Initialize books_db tables
    b_conn = get_books_db_connection()
    if b_conn:
        b_cursor = b_conn.cursor()
        b_cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                keywords VARCHAR(255),
                total_copies INT NOT NULL,
                available_copies INT NOT NULL
            )
        """)
        
        b_cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                book_id INT NOT NULL,
                type ENUM('issue', 'return', 'renew') NOT NULL,
                status ENUM('pending', 'approved', 'rejected') NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(id)
            )
        """)
        
        b_cursor.execute("""
            CREATE TABLE IF NOT EXISTS issued_books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                book_id INT NOT NULL,
                issue_date DATETIME NOT NULL,
                due_date DATETIME NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id)
            )
        """)
        
        b_conn.commit()
        b_cursor.close()
        b_conn.close()
        
    return True
