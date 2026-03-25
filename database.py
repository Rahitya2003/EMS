# Database connection
def get_db():
    try:
        conn = mysql.connector.connect(
            host="rahithya.mysql.pythonanywhere-services.com",  # PythonAnywhere host
            user="rahithya",
            password="Rahithya@123",
            database="rahithya$company"
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None