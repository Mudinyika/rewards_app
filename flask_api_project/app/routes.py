# app/routes.py
from flask import Blueprint, jsonify, request
from app.models import allocate_points, User, Card, Point  # Import your models here
from werkzeug.security import generate_password_hash

# Define the blueprints for the routes
users = Blueprint('users', __name__)
cards = Blueprint('cards', __name__)
points = Blueprint('points', __name__)
roles = Blueprint('roles', __name__)

# Example of defining the user routes
@users.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not all(key in data for key in ['name', 'email', 'password']):
        return jsonify({"message": "name, email, and password are required"}), 400

    # Hash the password before saving
    password_hash = generate_password_hash(data['password'])
    user = User(name=data['name'], email=data['email'], password_hash=password_hash)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"message": "User created", "user_id": user.id}), 201

@users.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "points": user.points
    })

# Example of defining the cards routes
@cards.route('/cards', methods=['GET'])
def get_cards():
    try:
        all_cards = Card.query.all()
        if not all_cards:
            return jsonify({"message": "No cards found"}), 404
        
        cards_data = [{'id': card.id, 'card_number': card.card_number} for card in all_cards]
        return jsonify(cards_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Example of defining points routes
@points.route("/api/points", methods=["GET", "OPTIONS"])
def get_points():
    return jsonify({"points": []}), 200

# Endpoint for allocating points
@roles.route('/allocate_points', methods=['POST'])
def allocate_points_route():
    transaction_id = request.json.get('transaction_id')
    points = request.json.get('points')

    if not transaction_id or not points:
        return {'message': 'Transaction ID and points are required'}, 400

    allocate_points(transaction_id, points)
    return {'message': 'Points allocation processed successfully'}, 200
