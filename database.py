import mysql.connector

def get_db():
    """Create and return a MySQL database connection"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rahithya@123",
        database="company"
    )