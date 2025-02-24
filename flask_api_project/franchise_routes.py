from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.sql.expression import func, case
from datetime import datetime, timedelta
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
    
@franchise_bp.route("/franchise/shops", methods=["GET"])
@jwt_required()
def get_franchise_shops():
    """Return all shops owned by the logged-in franchise manager."""
    
    # Get the logged-in user
    franchise_manager = Admin.query.get(get_jwt_identity())

    # Ensure the user is a franchise manager
    if not franchise_manager or franchise_manager.role != "franchise_manager":
        return jsonify({"error": "Unauthorized"}), 403

    # Fetch all shops belonging to the franchise
    shops = Shop.query.filter_by(franchise_id=franchise_manager.franchise_id).all()

    return jsonify({
        "shops": [{"id": shop.shop_id, "name": shop.shop_name, "location": shop.location} for shop in shops]
    })  
    
@franchise_bp.route("/franchise/fraud-detection", methods=["GET"])
@jwt_required()
def detect_fraud():
    """Detect unusual spikes in transactions for franchise shops."""
    
    # Get the logged-in franchise manager
    franchise_manager = Admin.query.get(get_jwt_identity())

    if not franchise_manager or franchise_manager.role != "franchise_manager":
        return jsonify({"error": "Unauthorized"}), 403

    # Get all shops under this franchise
    shop_ids = [shop.shop_id for shop in Shop.query.filter_by(franchise_id=franchise_manager.franchise_id).all()]
    
    if not shop_ids:
        return jsonify({"error": "No shops found for this franchise"}), 404

    # Get the last 30 days of transactions
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Calculate average points added and removed per shop
    avg_query = db.session.query(
        PointHistory.shop_id,
        func.avg(PointHistory.points).label("avg_points"),
        func.stddev(PointHistory.points).label("stddev_points")
    ).filter(PointHistory.timestamp >= thirty_days_ago, PointHistory.shop_id.in_(shop_ids))\
    .group_by(PointHistory.shop_id).all()

    anomalies = []

    # Check each shop's transactions against the average
    for shop_id, avg_points, stddev_points in avg_query:
        if stddev_points is None:  # If only one transaction, no deviation
            continue

        # 🔹 FIX: Convert both values to float before math operations
        threshold = float(avg_points) + (2 * float(stddev_points))

        suspicious_transactions = PointHistory.query.filter(
            PointHistory.shop_id == shop_id,
            PointHistory.timestamp >= thirty_days_ago,
            PointHistory.points > threshold
        ).all()

        if suspicious_transactions:
            anomalies.append({
                "shop_id": shop_id,
                "shop_name": Shop.query.get(shop_id).shop_name,
                "average_points": float(avg_points),  # Convert to float for consistency
                "threshold": threshold,
                "suspicious_transactions": [
                    {"id": t.id, "points": float(t.points), "date": t.timestamp} for t in suspicious_transactions
                ]
            })

    return jsonify({"fraud_alerts": anomalies})

@franchise_bp.route("/franchise/top-operators", methods=["GET"])
@jwt_required()
def top_operators():
    """Get top operators/admins based on transactions with date filtering."""
    
    franchise_manager = Admin.query.get(get_jwt_identity())

    if not franchise_manager or franchise_manager.role != "franchise_manager":
        return jsonify({"error": "Unauthorized"}), 403

    # Get all shops under this franchise
    shop_ids = [shop.shop_id for shop in Shop.query.filter_by(franchise_id=franchise_manager.franchise_id).all()]

    if not shop_ids:
        return jsonify({"error": "No shops found for this franchise"}), 404

    # 🛠️ Date filtering (default: show all-time data)
    date_filter = request.args.get("filter", "all")  # Options: "today", "week", "month"

    now = datetime.utcnow()

    if date_filter == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)  # Start of today
    elif date_filter == "week":
        start_date = now - timedelta(days=7)  # Last 7 days
    elif date_filter == "month":
        start_date = now.replace(day=1)  # First day of the current month
    else:
        start_date = None  # No filter applied

    # 🛠️ Base Query (Apply filters FIRST)
    query = db.session.query(
        PointHistory.performed_by_id,
        func.coalesce(Admin.admin_name, PointHistory.operator_name).label("name"),
        func.sum(case((PointHistory.transaction_type == "add", PointHistory.points), else_=0)).label("total_added"),
        func.sum(case((PointHistory.transaction_type == "remove", PointHistory.points), else_=0)).label("total_removed"),
    ).outerjoin(Admin, PointHistory.performed_by_id == Admin.id)\
    .filter(PointHistory.shop_id.in_(shop_ids))  # ✅ Apply this BEFORE limit

    # ✅ Apply date filter before `.limit()`
    if start_date:
        query = query.filter(PointHistory.timestamp >= start_date)

    query = query.group_by(PointHistory.performed_by_id, "name")\
                 .order_by(func.sum(PointHistory.points).desc())\
                 .limit(10)  # ✅ Apply `.limit()` last

    top_operators_query = query.all()

    return jsonify({
        "filter": date_filter,
        "top_operators": [
            {"id": op[0], "name": op[1], "total_added": str(op[2]), "total_removed": str(op[3])}
            for op in top_operators_query
        ]
    })




     
