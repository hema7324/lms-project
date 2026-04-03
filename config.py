import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234") # Change this to your actual MySQL root password

# Database names
USERS_DB = "lms_users_db"
BOOKS_DB = "lms_books_db"
