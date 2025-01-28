# backend/app/config.py

class Config:
    # Disable modification tracking for performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection URI with charset specified in the URI itself
    SQLALCHEMY_DATABASE_URI = (
        'mysql+pymysql://root:admin123@127.0.0.1:3306/user_points_system'
    )
    
    # Optional: No need to include SQLALCHEMY_ENGINE_OPTIONS for charset
    # SECRET_KEY: Use a random secret key for Flask sessions, cookies, etc.
    SECRET_KEY = 'your-secret-key'
    

