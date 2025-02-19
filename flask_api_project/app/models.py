# app/models.py
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class TransactionID(db.Model):
    __tablename__ = 'transaction_ids'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)

    def __init__(self, transaction_id):
        self.transaction_id = transaction_id

    def __repr__(self):
        return f"<TransactionID {self.transaction_id}>"

class PredefinedTransaction(db.Model):
    __tablename__ = 'predefined_transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)

    def __init__(self, transaction_id):
        self.transaction_id = transaction_id

    def __repr__(self):
        return f"<PredefinedTransaction {self.transaction_id}>"

# Define the User model
class User(db.Model):
    __tablename__ = 'users'
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

# Define the Card model
class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), unique=True, nullable=False)

    def __init__(self, card_number):
        self.card_number = card_number

    def __repr__(self):
        return f"<Card {self.card_number}>"

# Define the Point model
class Point(db.Model):
    __tablename__ = 'points'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points_allocated = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, points_allocated):
        self.user_id = user_id
        self.points_allocated = points_allocated

    def __repr__(self):
        return f"<Point {self.user_id} - {self.points_allocated} points>"

# Define the allocate_points function
def allocate_points(transaction_id, points):
    """
    Allocates points to a user based on a transaction ID.
    """
    print(f"Allocating {points} points for transaction {transaction_id}")
    
    # Example: Logic to update points for a user
    user = User.query.filter_by(transaction_id=transaction_id).first()
    if user:
        user.points += points  # Update points
        db.session.commit()  # Commit changes to the database
        print(f"Points allocated to user {user.name}")
    else:
        print(f"User with transaction_id {transaction_id} not found.")


class Operator(db.Model):
    __tablename__ = 'till_operators'
    
    id = db.Column(db.Integer, primary_key=True)
    till_number = db.Column(db.String(50), unique=True, nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='admin')  # 'admin', 'user', 'superuser'

    def __init__(self, till_number, operator_name, password, role='admin'):
        self.till_number = till_number
        self.operator_name = operator_name
        self.password_hash = generate_password_hash(password)
        self.role = role

    # Password validation method
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Operator {self.operator_name}>'    