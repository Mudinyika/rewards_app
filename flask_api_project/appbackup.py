from flask import Flask, jsonify, request, render_template, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from decimal import Decimal

# Initialize your Flask app and the database object
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:my_password@localhost/user_points_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev_secret_key_1234567890'

# Admin authentication key
ADMIN_KEY = "admin123"  # Replace with your desired admin key
db = SQLAlchemy(app)

CORS(app)


# Database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'admin123'  # Change this if you have a password
DB_NAME = 'user_points_system'


@app.route('/')
def index():
    return render_template('login_form.html')
# Function to create a new till operator (this would be used during setup)
def create_till_operator(till_number, operator_name, password):
    # Hash the password before saving it to the database
    hashed_password = generate_password_hash(password)
    
    # Connect to the MySQL database using pymysql
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO till_operators (till_number, operator_name, password_hash)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (till_number, operator_name, hashed_password))
            connection.commit()
    finally:
        connection.close()
    
# Function to retrieve the hashed password for a given till_number and operator_name
def get_password_hash_for_operator(till_number, operator_name):
    # Connect to the MySQL database using pymysql
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    try:
        with connection.cursor() as cursor:
            query = """
            SELECT password_hash
            FROM till_operators
            WHERE till_number = %s AND operator_name = %s
            """
            cursor.execute(query, (till_number, operator_name))
            result = cursor.fetchone()
            if result:
                return result[0]  # Return the hashed password
            else:
                return None  # No matching operator found
    finally:
        connection.close()

# Function to validate operator credentials (login logic)
def validate_till_operator(till_number, operator_name, password):
    # Get the stored password hash from the database
    stored_password_hash = get_password_hash_for_operator(till_number, operator_name)

    if stored_password_hash and check_password_hash(stored_password_hash, password):
        return True  # Valid credentials
    else:
        return False  # Invalid credentials


# Function to get the role of an operator
def get_operator_role(till_number, operator_name):
    # Connect to the MySQL database using pymysql
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    try:
        with connection.cursor() as cursor:
            query = """
            SELECT role
            FROM till_operators
            WHERE till_number = %s AND operator_name = %s
            """
            cursor.execute(query, (till_number, operator_name))
            result = cursor.fetchone()
            if result:
                return result[0]  # Return role ('user', 'admin', etc.)
            else:
                return None  # No operator found
    finally:
        connection.close()
        
# Route for the login page (serving the login form)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    till_number = data.get('till_number')
    operator_name = data.get('operator_name')
    password = data.get('password')

    # Validate login credentials
    if validate_till_operator(till_number, operator_name, password):
        role = get_operator_role(till_number, operator_name)
        if role in ['user', 'admin']:
            # Set session variables
            session['logged_in'] = True
            session['till_number'] = till_number
            session['operator_name'] = operator_name
            session['role'] = role

            return jsonify({
                "success": True,
                "redirect": "/allocate_points_page",
                "role": role
            })
        return jsonify({"success": False, "error": "Insufficient privileges"}), 403
    return jsonify({"success": False, "error": "Invalid credentials"}), 401


def get_db_connection():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

def create_app():
    print("App creation started...") 
    # Create a Flask application instance
    app = Flask(__name__)

    # Set up the configuration (this will look for the Config class in config.py)
    app.config.from_object('app.config.Config')

    # Initialize the database with the app
    db.init_app(app)

    # You can also set up routes, blueprints, etc., here
    with app.app_context():
        print("Creating database tables...")  # Print to see if table creation is working
        db.create_all()

    return app

from decimal import Decimal


  
@app.route('/api/allocate-points', methods=['POST'])
def allocate_points_api():
    data = request.get_json()
    user_id = data.get('user_id')
    points = data.get('points')  # Points from request, should be a float or decimal
    transaction_type = data.get('transaction_type')
    transaction_id = data.get('transaction_id')  # New field for transaction ID
    admin_key = data.get('admin_key')

    if admin_key != ADMIN_KEY:
        return jsonify({"error": "Invalid admin key"}), 403
    
    if not transaction_id:
        return jsonify({'error': 'Transaction ID is required'}), 400

    if not user_id:
        return jsonify({"error": "Missing required fields"}), 409
    
    if not points:
        return jsonify({'error': 'Please enter correct format'}), 408
    
    if not transaction_type:
        return jsonify({'error': 'Transaction ID is required'}), 407

    try:
        # Convert points to a Decimal to ensure consistency
        points = Decimal(str(points))  # Convert the points to a Decimal to avoid float issues

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the transaction ID exists in the predefined_transactions table
        cursor.execute("SELECT used FROM predefined_transactions WHERE transaction_id = %s", (transaction_id,))
        transaction_record = cursor.fetchone()
        if not transaction_record:
            return jsonify({"error": "Invalid transaction ID"}), 400
        if transaction_record[0]:  # Check if 'used' is True
            return jsonify({"error": "Transaction ID already used"}), 400

        # Check if the user exists and retrieve current points
        cursor.execute("SELECT points FROM users WHERE id = %s", (user_id,))
        current_points = cursor.fetchone()
        if not current_points:
            return jsonify({"error": "User not found"}), 404

        # Get current points as Decimal
        current_points = Decimal(str(current_points[0]))  # Convert current points to Decimal

        # Perform the correct operation based on the transaction type
        if transaction_type == 'add':
            new_points = current_points + points
        elif transaction_type == 'remove':
            new_points = current_points - points
        else:
            return jsonify({"error": "Invalid transaction type"}), 400

        # Update the points in the database
        cursor.execute("UPDATE users SET points = %s WHERE id = %s", (new_points, user_id))
        cursor.execute("INSERT INTO point_history (user_id, points, transaction_type, transaction_id) VALUES (%s, %s, %s, %s)",
                       (user_id, points, transaction_type, transaction_id))

        # Mark the transaction ID as used in predefined_transactions
        cursor.execute("UPDATE predefined_transactions SET used = TRUE WHERE transaction_id = %s", (transaction_id,))

        connection.commit()

        return jsonify({"message": "Points successfully updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/user-stats', methods=['GET'])
def user_stats():
    period = request.args.get('period', 'monthly')  # Default to monthly
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query for new, deleted, and current users based on the period
        if period == 'monthly':
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE created_at BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND CURDATE()) AS new_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NOT NULL AND deleted_at BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND CURDATE()) AS deleted_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) AS current_users
            """)
        elif period == 'daily':
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE created_at = CURDATE()) AS new_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NOT NULL AND DATE(deleted_at) = CURDATE()) AS deleted_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) AS current_users
            """)
        elif period == 'weekly':
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE YEARWEEK(created_at, 1) = YEARWEEK(CURDATE(), 1)) AS new_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NOT NULL AND YEARWEEK(deleted_at, 1) = YEARWEEK(CURDATE(), 1)) AS deleted_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) AS current_users
            """)
        elif period == 'yearly':
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE YEAR(created_at) = YEAR(CURDATE())) AS new_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NOT NULL AND YEAR(deleted_at) = YEAR(CURDATE())) AS deleted_users,
                    (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) AS current_users
            """)

        data = cursor.fetchone()

        new_users = data[0]
        deleted_users = data[1]
        current_users = data[2]

        return jsonify({
            'new_users': new_users,
            'deleted_users': deleted_users,
            'current_users': current_users
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()
@app.route('/api/users-created-per-month', methods=['GET'])
def users_created_per_month():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query to count the number of users created per month
        cursor.execute("""
            SELECT YEAR(created_at) AS year, MONTH(created_at) AS month, COUNT(*) AS user_count
            FROM users
            GROUP BY YEAR(created_at), MONTH(created_at)
            ORDER BY year, month
        """)
        data = cursor.fetchall()

        # Prepare the data for the frontend
        months = []
        user_counts = []
        for row in data:
            year_month = f"{row[0]}-{row[1]:02d}"
            months.append(year_month)
            user_counts.append(row[2])

        return jsonify({
            'months': months,
            'user_counts': user_counts
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()




@app.route('/api/search-users', methods=['GET'])
def search_users():
    search_query = request.args.get('query', '')

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Search users by ID or name
        cursor.execute(""" 
            SELECT id, name FROM users 
            WHERE id LIKE %s OR name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))

        users = cursor.fetchall()

        # Format the response to return an array of objects
        formatted_users = [{"id": user[0], "name": user[1]} for user in users]

        return jsonify({"users": formatted_users}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close() 
        connection.close()


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    period = request.args.get('period', 'daily')  # Default to daily metrics
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Determine date range based on selected period (daily, weekly, or monthly)
        if period == 'daily':
            cursor.execute("SELECT COUNT(id) FROM users WHERE DATE(created_at) = CURDATE()")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(points) FROM point_history WHERE DATE(timestamp) = CURDATE() AND transaction_type = 'add'")
            total_points_added = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(points) FROM point_history WHERE DATE(timestamp) = CURDATE() AND transaction_type = 'remove'")
            total_points_removed = cursor.fetchone()[0] or 0
        elif period == 'weekly':
            cursor.execute("SELECT COUNT(id) FROM users WHERE YEARWEEK(created_at, 1) = YEARWEEK(CURDATE(), 1)")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(points) FROM point_history WHERE YEARWEEK(timestamp, 1) = YEARWEEK(CURDATE(), 1) AND transaction_type = 'add'")
            total_points_added = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(points) FROM point_history WHERE YEARWEEK(timestamp, 1) = YEARWEEK(CURDATE(), 1) AND transaction_type = 'remove'")
            total_points_removed = cursor.fetchone()[0] or 0
        elif period == 'monthly':
            cursor.execute("SELECT COUNT(id) FROM users WHERE MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE())")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(points) FROM point_history WHERE MONTH(timestamp) = MONTH(CURDATE()) AND YEAR(timestamp) = YEAR(CURDATE()) AND transaction_type = 'add'")
            total_points_added = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(points) FROM point_history WHERE MONTH(timestamp) = MONTH(CURDATE()) AND YEAR(timestamp) = YEAR(CURDATE()) AND transaction_type = 'remove'")
            total_points_removed = cursor.fetchone()[0] or 0

        return jsonify({
            "user_count": user_count,
            "total_points_added": total_points_added,
            "total_points_removed": total_points_removed
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/api/add-user', methods=['POST'])
def add_user():
    cursor = None
    connection = None

    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        admin_key = data.get('admin_key')

        if admin_key != ADMIN_KEY:
            return jsonify({"error": "Invalid admin key"}), 403

        if not email or not name or not password:
            return jsonify({"error": "Missing required fields"}), 400

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
            (email, name, hashed_password)
        )
        connection.commit()

        return jsonify({"message": "User created successfully"}), 201

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query to get user details
        cursor.execute("SELECT name, points FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Query to get the last transaction
        cursor.execute(
            "SELECT points, transaction_type, timestamp FROM point_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1",
            (user_id,)
        )
        last_transaction = cursor.fetchone()

        # Format the last transaction details
        last_transaction_info = None
        if last_transaction:
            points, transaction_type, timestamp = last_transaction
            last_transaction_info = f"{transaction_type.capitalize()} {points} points on {timestamp}"

        # Return the user details
        return jsonify({
            "name": user[0],
            "points": user[1],
            "last_transaction": last_transaction_info
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()           
            
@app.route('/admin')
def admin():
    return render_template('admin.html')
# Models
class TransactionID(db.Model):
    __tablename__ = 'transaction_ids'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(255), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)

class Points(db.Model):
    __tablename__ = 'points'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(255))
    

# Route to add points
@app.route('/api/card-swipe', methods=['POST'])
def handle_card_swipe():
    """
    Handle magnetic stripe card swipe, fetch user information by ID.
    """
    data = request.get_json()
    card_data = data.get('card_data')  # Raw data from the magnetic stripe card reader

    if not card_data:
        return jsonify({"error": "No card data provided"}), 400

    try:
        # Decrypt or parse card data to extract user ID
        # For this example, assume the card_data is a plain user_id
        user_id = card_data.strip()

        # Validate the user ID (e.g., check length, format, etc.)
        if not user_id.isdigit():
            return jsonify({"error": "Invalid card data"}), 400

        # Fetch user details
        connection = get_db_connection()
        cursor = connection.cursor()

        # Query the user information from the database
        cursor.execute("SELECT name, points FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Fetch last transaction for user
        cursor.execute(
            "SELECT points, transaction_type, timestamp FROM point_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT 1",
            (user_id,)
        )
        last_transaction = cursor.fetchone()

        last_transaction_info = None
        if last_transaction:
            points, transaction_type, timestamp = last_transaction
            last_transaction_info = f"{transaction_type.capitalize()} {points} points on {timestamp}"

        # Return user information
        return jsonify({
            "user_id": user_id,
            "name": user[0],
            "points": user[1],
            "last_transaction": last_transaction_info
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/allocate_points', methods=['POST'])
def allocate_points():
    data = request.get_json()
    till_number = data.get('till_number')
    operator_name = data.get('operator_name')
    password = data.get('password')

    # Validate operator credentials (login)
    if validate_till_operator(till_number, operator_name, password):
        # Check the operator's role
        role = get_operator_role(till_number, operator_name)

        if role == 'user' or role == 'admin':
            # Set session for logged-in user
            session['username'] = operator_name
            session['role'] = role

            # Redirect to allocate points page
            return jsonify({"success": True, "role": role, "redirect": "/allocate_points_page"})
        else:
            return jsonify({"success": False, "error": "Insufficient privileges"}), 403
    else:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

# Route for the allocate points page
@app.route('/allocate_points_page', methods=['GET'])
def allocate_points_page():
    if not session.get('logged_in'):
        return redirect(url_for('index'))  # Redirect to login if not authenticated
    
    # Extract data for rendering or API responses
    operator_name = session.get('operator_name', 'Unknown')
    till_number = session.get('till_number', 'Unknown')
    role = session.get('role', 'Unknown')
    
    return render_template('AllocatePoints.html', till_number=till_number, operator_name=operator_name, role=role)






@app.route('/api/operator_info', methods=['GET'])
def get_operator_info():
    operator = Operator.query.filter_by(till_number=session['till_number']).first()
    if operator:
        return jsonify({
            'operator_name': operator.operator_name,
            'till_number': operator.till_number,
            'role': operator.role
        })
    return jsonify({'error': 'Operator not found'}), 404

@app.route('/add_operator', methods=['POST'])
def add_operator():
    # Get data from the request body
    data = request.get_json()

    # Validate input data
    till_number = data.get('till_number')
    operator_name = data.get('operator_name')
    password = data.get('password')
    role = data.get('role')

    if not till_number or not operator_name or not password or not role:
        return jsonify({"error": "All fields are required"}), 400

    # Check if the operator already exists
    existing_operator = Operator.query.filter_by(till_number=till_number).first()
    if existing_operator:
        return jsonify({"error": "Operator already exists"}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create the new operator
    new_operator = Operator(
        till_number=till_number,
        operator_name=operator_name,
        password=hashed_password,
        role=role
    )

    # Add operator to the database
    db.session.add(new_operator)
    db.session.commit()

    return jsonify({"message": "Operator added successfully"}), 201        

@app.route('/logout', methods=['POST'])
def logout():
    # Remove user-related session data (like login credentials)
    session.clear()
    # Redirect to login page after logout
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
