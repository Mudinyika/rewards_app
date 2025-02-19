from flask import Blueprint, request, jsonify
from app import db
from app.models import User

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('', methods=['POST'])
def create_user():
    data = request.json
    user = User(name=data['name'], email=data['email'], password_hash=data['password_hash'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created", "user_id": user.id}), 201

@bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "name": user.name, "email": user.email})
