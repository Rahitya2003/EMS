import mysql.connector

def get_db():
    """Create and return a MySQL database connection"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="company"
    )