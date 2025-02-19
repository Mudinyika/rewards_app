# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os




# Initialize the database
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configure app from environment variable or fallback to default config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'mysql+pymysql://root:admin123@127.0.0.1/user_points_system'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database with the app
    db.init_app(app)

    # Ensure tables are created on app startup
    with app.app_context():
        db.create_all()

    # Import and register blueprints inside the factory function
    from app.routes import users, cards, points, roles # Import blueprints here
    app.register_blueprint(users, url_prefix='/api')
    app.register_blueprint(cards, url_prefix='/api')
    app.register_blueprint(points, url_prefix='/api')
    app.register_blueprint(roles, url_prefix='/api')
   

    return app
