import pymysql
from werkzeug.security import generate_password_hash

# Establish connection to your MySQL database
connection = pymysql.connect(
    host='localhost',  # Replace with your host if needed
    user='root',       # Replace with your username
    password='admin123',  # Replace with your password
    database='user_points_system'  # Replace with your database name
)

# Hash the password
password = "test"  # Replace with the actual password you want to store
password_hash = generate_password_hash(password, method="pbkdf2:sha256")

# Insert user data into the database
try:
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO till_operators (till_number, operator_name, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, ("001", "Cashier1", password_hash, "user"))  # Adjust values as needed
        connection.commit()

    print("User created successfully!")

except Exception as e:
    print(f"Error: {e}")
finally:
    connection.close()
