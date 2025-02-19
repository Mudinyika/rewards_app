from sqlalchemy import create_engine

# Connection string
DATABASE_URL = 'mysql+pymysql://root:admin123@127.0.0.1/user_points_system'

try:
    # Test the connection
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("Database connection successful!")
    connection.close()
except Exception as e:
    print(f"Database connection failed: {e}")
