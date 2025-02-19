from flask import Blueprint, request, jsonify
from app import db
from app.models import Point

bp = Blueprint('points', __name__, url_prefix='/api/points')

@bp.route('', methods=['POST'])
def add_points():
    data = request.json
    point = Point(user_id=data['user_id'], points=data['points'])
    db.session.add(point)
    db.session.commit()
    return jsonify({"message": "Points added"}), 201

@bp.route('/<int:user_id>', methods=['GET'])
def get_user_points(user_id):
    points = Point.query.filter_by(user_id=user_id).all()
    total_points = sum([p.points for p in points])
    return jsonify({"user_id": user_id, "total_points": total_points})
