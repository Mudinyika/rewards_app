from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()  # ✅ Initialize db


class Shop(db.Model):
    __tablename__ = "shops"

    shop_id = db.Column(db.Integer, primary_key=True)  # ✅ Match database column
    shop_name = db.Column(db.String(255), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    franchise_id = db.Column(db.Integer, db.ForeignKey("franchises.id"), nullable=True)

    franchise = db.relationship("Franchise", backref="shops")


    def __repr__(self):
        return f"<Shop {self.name} (Franchise {self.franchise_id})>"

class Franchise(db.Model):
    __tablename__ = "franchises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_email = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Franchise {self.name} (Owner: {self.owner_name})>"

class PointHistory(db.Model):
    __tablename__ = "point_history"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.shop_id"), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # "add" or "remove"
    points = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    shop = db.relationship("Shop", backref=db.backref("point_history", lazy=True))


class Operator(db.Model):
    __tablename__ = "till_operators"

    id = db.Column(db.Integer, primary_key=True)
    till_number = db.Column(db.String(50), unique=True, nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="admin")  # 'admin', 'user', 'superuser'    
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.shop_id"), nullable=True)  # New column
    
    shop = db.relationship("Shop", backref="operators")

    def __init__(self, till_number, operator_name, password, role="admin", shop_id=None):
        self.till_number = till_number
        self.operator_name = operator_name
        self.password_hash = generate_password_hash(password)
        self.role = role
        self.shop_id = shop_id

    # Password validation method
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Operator {self.operator_name}>"


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    points = db.Column(db.Integer, default=0)

    def __init__(self, name, email, password_hash, points=0):
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.points = points

    def __repr__(self):
        return f"<User {self.name} ({self.email})>"

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class TransactionID(db.Model):
    __tablename__ = "transaction_ids"
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(255), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)


class Points(db.Model):
    __tablename__ = "points"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(255))


# Assuming your 'admin' table has these columns
class Admin(db.Model):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(100), nullable=False)
    admin_surname = db.Column(db.String(100), nullable=False)
    admin_phone_number = db.Column(db.String(15), nullable=False)
    admin_id_number = db.Column(db.String(100), nullable=False)
    admin_picture = db.Column(db.String(200), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.shop_id"), nullable=True)  # New column
    franchise_id = db.Column(db.Integer, db.ForeignKey("franchises.id"), nullable=True)
    
    shop = db.relationship("Shop", backref="admins")
    franchise = db.relationship("Franchise", backref="admins")

    def __repr__(self):
        return f"<Admin {self.admin_name} {self.admin_surname}>"