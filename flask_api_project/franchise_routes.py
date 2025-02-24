from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Admin, PointHistory, Shop  # ✅ Import from models.py

franchise_bp = Blueprint("franchise", __name__)

@franchise_bp.route("/franchise/analytics", methods=["GET"])
@jwt_required()
def get_franchise_analytics():
    # 🔹 Get the current logged-in franchise manager from Admin table
    current_admin = Admin.query.get(get_jwt_identity())
    
    if not current_admin or current_admin.role != "franchise_manager":
        return jsonify({"error": "Unauthorized"}), 403

    # 🔹 Ensure franchise_id is valid
    if not current_admin.franchise_id:
        return jsonify({"error": "Franchise not found"}), 404

    # 🔹 Get query parameters for filtering
    shop_id = request.args.get("shop_id", type=int)
    start_date = request.args.get("start_date")  # Format: YYYY-MM-DD
    end_date = request.args.get("end_date")  # Format: YYYY-MM-DD
    filter_type = request.args.get("filter", "total")  # Options: total, shop, date

    # 🔹 Get all shops under this franchise
    shop_ids_query = db.session.query(Shop.shop_id).filter_by(franchise_id=current_admin.franchise_id)

    # 🔹 Apply shop filter if provided
    if shop_id:
        shop_ids_query = shop_ids_query.filter(Shop.shop_id == shop_id)

    # 🔹 Convert to list of IDs
    shop_ids = [s[0] for s in shop_ids_query.all()]

    # 🔹 Base query for transactions
    transactions_query = db.session.query(PointHistory).filter(PointHistory.shop_id.in_(shop_ids))

    # 🔹 Apply date range filter
    if start_date:
        transactions_query = transactions_query.filter(PointHistory.timestamp >= start_date)
    if end_date:
        transactions_query = transactions_query.filter(PointHistory.timestamp <= end_date)

    # 🔹 Calculate total added & removed points
    total_added = db.session.query(db.func.coalesce(db.func.sum(PointHistory.points), 0))\
        .filter(PointHistory.transaction_type == "add", PointHistory.shop_id.in_(shop_ids)).scalar()

    total_removed = db.session.query(db.func.coalesce(db.func.sum(PointHistory.points), 0))\
        .filter(PointHistory.transaction_type == "remove", PointHistory.shop_id.in_(shop_ids)).scalar()

    # 🔹 Get shop details
    shops = Shop.query.filter(Shop.shop_id.in_(shop_ids)).all()

    return jsonify({
        "total_added": total_added,
        "total_removed": total_removed,
        "shops": [{"id": shop.shop_id, "name": shop.shop_name} for shop in shops]

    })
