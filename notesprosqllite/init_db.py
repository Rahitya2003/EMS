import mysql.connector

def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rahithya@123",
        database="company"
    )

    cursor = conn.cursor()

    # Create employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            eid INT PRIMARY KEY,
            ename VARCHAR(100),
            edept VARCHAR(100),
            esalary DECIMAL(10,2),
            ephone VARCHAR(15)
        )
    """)

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100),
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50),
            email VARCHAR(100) UNIQUE,
            profile_pic VARCHAR(255)
        )
    """)

    conn.commit()
    conn.close()

    print("✅ MySQL Database initialized successfully!")

if __name__ == "__main__":
    init_db()