from flask import Flask, jsonify, Blueprint, request, render_template, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from decimal import Decimal
from datetime import datetime
from sqlalchemy import text

# Initialize your Flask app and the database object
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin123@localhost/user_points_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev_secret_key_1234567890'

# Admin authentication key
ADMIN_KEY = "admin123"  # Replace with your desired admin key
SUPERUSER_HASHED_PASSWORD = "scrypt:32768:8:1$gdAZwtLHS3XKh2Vb$4d7042e565690de6e7a033fa8d713acd306d97ca0d0cb19a5dfa3874c7927eaee642b7d5f0b3663fa1c04ea390eb59bd3758e55e08814ab64a59249f914905c8"

db = SQLAlchemy(app)

#CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
#CORS(app)


# Database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'admin123'  # Change this if you have a password
DB_NAME = 'user_points_system'

superuser_password = "superman"  # Change this to your desired password
hashed_password = generate_password_hash(superuser_password, method="pbkdf2:sha256")

print("Superuser Hashed Password:", hashed_password)



#@app.route('/test-db')
#def test_db():
 #   try:
        # Query the users table using text() for raw SQL
  #      result = db.session.execute(text("SELECT * FROM users"))
        
        # Fetch column names
   #     columns = result.keys()
        
        # Fetch rows and convert them into a list of dictionaries
    #    users_list = [dict(zip(columns, row)) for row in result.fetchall()]

     #   return jsonify({"users": users_list}), 200
   # except Exception as e:
        # Log the error to the console for debugging
    #    print(f"Error: {str(e)}")
     #   return jsonify({"error": str(e)}), 500





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

# Function to get admin by username
def get_admin_by_username(username):
    return Admin.query.filter_by(admin_name=username).first()

# Route to handle Admin login
@app.route('/api/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    # 🔹 Validate Inputs
    if not username or not password or not role:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    # 🔹 Get Admin from Database
    admin = get_admin_by_username(username)
    if not admin:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401  # ❌ No admin found

    # 🔹 Check Password Hash
    if not check_password_hash(admin.password_hash, password):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401  # ❌ Wrong password

    # 🔹 Ensure Role Matches
    if admin.role != role:
        return jsonify({"success": False, "error": "Role mismatch"}), 403  # ❌ User chose the wrong role

    # ✅ Successful Login → Set Session
    session['logged_in'] = True
    session['username'] = username
    session['role'] = admin.role

    response = jsonify({
        "success": True,
        "message": "Login successful",
        "role": admin.role
    })
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response, 200  # ✅ Success

# ✅ Check Login Status
@app.route('/api/check-login', methods=['GET'])
def check_login():
    if session.get('logged_in'):
        return jsonify({
            "success": True,
            "role": session.get('role')
        }), 200  # ✅ Logged in
    return jsonify({
        "success": False,
        "error": "Not logged in"
    }), 401  # ❌ Not logged in


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

@app.route('/api/admins', methods=['GET'])
def get_admins():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, admin_name, admin_surname, admin_picture, role FROM admin")
    admins = cursor.fetchall()

    return jsonify({"admins": [{"id": a[0], "admin_name": a[1], "admin_surname": a[2], "admin_picture": a[3], "role": a[4]} for a in admins]}), 200

@app.route('/api/manage-permissions', methods=['POST'])
def manage_permissions():
    """Super User updates roles for Admins, Managers, and Till Operators"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')  # The admin whose role is being updated
        new_role = data.get('new_role')  # The new role to be assigned
        super_user_key = data.get('super_user_key')  # Authorization check

        # Convert role to lowercase to match DB storage
        if new_role:
            new_role = new_role.lower()

        # Validate role
        valid_roles = {'admin', 'manager', 'super'}
        if new_role not in valid_roles:
            return jsonify({"error": "Invalid role provided"}), 400

        # Ensure only the super user can update roles
        if super_user_key != SUPERUSER_HASHED_PASSWORD:
            return jsonify({"error": "Unauthorized. Only Super User can manage permissions."}), 403

        # Database connection
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        # Check if the admin exists
        cursor.execute("SELECT id FROM admin WHERE id = %s", (admin_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Admin not found"}), 404

        # Update the role
        cursor.execute("UPDATE admin SET role = %s WHERE id = %s", (new_role, admin_id))
        connection.commit()

        return jsonify({"message": "Role updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Close resources safely
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route('/api/till-operators', methods=['GET'])
def get_till_operators():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, till_number, operator_name FROM till_operators")
    operators = cursor.fetchall()

    return jsonify({"till_operators": [{"id": o[0], "till_number": o[1], "operator_name": o[2]} for o in operators]}), 200

@app.route('/api/manage_user', methods=['POST', 'PUT', 'DELETE', 'GET'])
def manage_user():
    """ Route to Add, Edit, Delete, or Fetch Admins, Till Operators, and Regular Users """
    
    try:
        # For GET requests, use request.args, otherwise use request.get_json()
        data = request.args if request.method == 'GET' else request.get_json()
        print("Received Data:", data)

        action = data.get('action')  # 'add', 'edit', 'delete', 'fetch'
        user_type = data.get('user_type')  # 'admin', 'till_operator', or 'user'
        user_id = data.get('id')  # Needed for edit/delete/fetch
        
        if not action or not user_type:
            return jsonify({"error": "Missing required parameters"}), 400

        # Ensure valid connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Handle different actions based on the action type
        if action == 'add':
            return add_user(data, user_type, cursor, connection)
        elif action == 'edit' and user_id:
            return edit_user(data, user_type, user_id, cursor, connection)
        elif action == 'delete' and user_id:
            return delete_user(user_id, user_type, cursor, connection)
        elif action == 'fetch':
            return fetch_users(user_type)  # Only pass user_type, not cursor
        else:
            return jsonify({"error": "Invalid action or missing user_id"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



def add_user(data, user_type, cursor, connection):
    """ Add an admin, till operator, or regular user """
    print(f"Received Data for {user_type}: {data}")
    if user_type == 'admin':
        required_fields = ['admin_name', 'admin_surname', 'admin_phone_number', 'admin_id_number', 'password', 'role']
        table_name = 'admin'
        columns = "admin_name, admin_surname, admin_phone_number, admin_id_number, admin_picture, password_hash, role"
    elif user_type == 'till_operator':
        required_fields = ['till_number', 'operator_name', 'password', 'role']
        table_name = 'till_operators'
        columns = "till_number, operator_name, password_hash, role"
    elif user_type == 'user':
        required_fields = ['email', 'name', 'password']
        table_name = 'users'
        columns = "email, name, password_hash"
    else:
        return jsonify({"error": "Invalid user type"}), 400

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)} for {user_type}"}), 400

    password_hash = generate_password_hash(data['password'])

    values = [data[field] if field != 'password' else password_hash for field in required_fields]

    # Ensure admin_picture is NULL if not provided
    if user_type == 'admin':
        values.insert(4, data.get('admin_picture', None))

    query = f"INSERT INTO {table_name} ({columns}) VALUES ({', '.join(['%s'] * len(values))})"
    cursor.execute(query, tuple(values))
    connection.commit()

    return jsonify({"message": f"{user_type.capitalize()} added successfully"}), 201


def edit_user(data, user_type, user_id, cursor, connection):
    """ Edit an existing admin, till operator, or regular user """
    if user_type == 'admin':
        table_name = 'admin'
        valid_fields = ['admin_name', 'admin_surname', 'admin_phone_number', 'admin_id_number', 'admin_picture', 'password_hash', 'role']
    elif user_type == 'till_operator':
        table_name = 'till_operators'
        valid_fields = ['till_number', 'operator_name', 'password_hash', 'role']
    elif user_type == 'user':
        table_name = 'users'
        valid_fields = ['email', 'name', 'password_hash']
    else:
        return jsonify({"error": "Invalid user type"}), 400

    update_fields = []
    values = []

    for field in valid_fields:
        if field in data:
            update_fields.append(f"{field} = %s")
            values.append(generate_password_hash(data[field]) if field == 'password' else data[field])

    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(user_id)
    query = f"UPDATE {table_name} SET {', '.join(update_fields)} WHERE id = %s"
    cursor.execute(query, tuple(values))
    connection.commit()

    return jsonify({"message": f"{user_type.capitalize()} updated successfully"}), 200


def delete_user(user_id, user_type, cursor, connection):
    """ Delete an admin, till operator, or regular user """
    table_name = 'admin' if user_type == 'admin' else 'till_operators' if user_type == 'till_operator' else 'users'
    cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (user_id,))
    connection.commit()

    return jsonify({"message": f"{user_type.capitalize()} deleted successfully"}), 200


def fetch_users(user_type):
    """ Fetch all admins or till operators """
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    
    # Determine the table based on user_type
    table_name = 'admin' if user_type == 'admin' else 'till_operators' if user_type == 'till_operator' else 'users'
    
    try:
        # Execute query to fetch users from the correct table
        cursor.execute(f"SELECT * FROM {table_name}")
        users = cursor.fetchall()

        # Get the column names from cursor.description
        columns = [column[0] for column in cursor.description]
        
        # Format the result into a list of dictionaries
        users_data = [{columns[i]: user[i] for i in range(len(columns))} for user in users]
        
        return jsonify(users_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Close the cursor and connection after use
        cursor.close()
        connection.close()


from sqlalchemy import text

@app.route('/api/metrics', methods=['GET'])
def get_dashboard_metrics():
    try:
        # Query the metrics data
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM users
        """))
        total_users = result.fetchone()[0]

        result = db.session.execute(text("""
            SELECT COUNT(*) FROM till_operators
        """))
        till_operator_count = result.fetchone()[0]

        result = db.session.execute(text("""
            SELECT COUNT(*) FROM admin
        """))
        admin_count = result.fetchone()[0]

        # Assuming only one superuser
        superuser_count = 1

        result = db.session.execute(text("""
            SELECT SUM(points) FROM point_history 
            WHERE transaction_type = 'add' 
            AND timestamp >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """))
        total_added_points = result.fetchone()[0] or 0

        result = db.session.execute(text("""
            SELECT SUM(points) FROM point_history 
            WHERE transaction_type = 'remove' 
            AND timestamp >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """))
        total_removed_points = result.fetchone()[0] or 0

        result = db.session.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE created_at >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """))
        new_users_this_month = result.fetchone()[0]

        return jsonify({
            "total_users": total_users,
            "till_operator_count": till_operator_count,
            "admin_count": admin_count,
            "superuser_count": superuser_count,
            "total_added_points": total_added_points,
            "total_removed_points": total_removed_points,
            "new_users_this_month": new_users_this_month
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")  # Debugging error in the console
        return jsonify({"error": str(e)}), 500


@app.route('/api/allocate-points', methods=['POST'])
def allocate_points():
    data = request.get_json()
    user_id = data.get('user_id')
    points = data.get('points')  # Points should be a float or decimal
    transaction_type = data.get('transaction_type')
    admin_key = data.get('admin_key')

    if admin_key != ADMIN_KEY:
        return jsonify({"error": "Invalid admin key"}), 403

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    if points is None:
        return jsonify({"error": "Points value is required"}), 400

    if not transaction_type:
        return jsonify({"error": "Transaction type is required"}), 400

    try:
        # Convert points to Decimal for consistency
        points = Decimal(str(points))

        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch an unused transaction ID
        cursor.execute("SELECT transaction_id FROM predefined_transactions WHERE used = 0 LIMIT 1")
        transaction_record = cursor.fetchone()
        if not transaction_record:
            return jsonify({"error": "No available transaction IDs"}), 400

        transaction_id = transaction_record[0]  # Assign fetched transaction ID

        # Check if the user exists and retrieve current points
        cursor.execute("SELECT points FROM users WHERE id = %s", (user_id,))
        current_points = cursor.fetchone()
        if not current_points:
            return jsonify({"error": "User not found"}), 404

        # Convert current points to Decimal
        current_points = Decimal(str(current_points[0]))

        # Perform the correct operation based on transaction type
        if transaction_type == 'add':
            new_points = current_points + points
        elif transaction_type == 'remove':
            new_points = current_points - points
        else:
            return jsonify({"error": "Invalid transaction type"}), 400

        # Update the user's points
        cursor.execute("UPDATE users SET points = %s WHERE id = %s", (new_points, user_id))
        cursor.execute("INSERT INTO point_history (user_id, points, transaction_type, transaction_id) VALUES (%s, %s, %s, %s)",
                       (user_id, points, transaction_type, transaction_id))

        # Mark the transaction ID as used in predefined_transactions
        cursor.execute("UPDATE predefined_transactions SET used = 1 WHERE transaction_id = %s", (transaction_id,))

        connection.commit()

        return jsonify({"message": "Points successfully updated", "transaction_id": transaction_id}), 200

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

                   
# Models

# Define the User model

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

# Assuming your 'admin' table has these columns
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(100), nullable=False)
    admin_surname = db.Column(db.String(100), nullable=False)
    admin_phone_number = db.Column(db.String(15), nullable=False)
    admin_id_number = db.Column(db.String(100), nullable=False)
    admin_picture = db.Column(db.String(200), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Admin {self.admin_name} {self.admin_surname}>'
    
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
    # Check if 'till_number' is in the session
    if 'till_number' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    try:
        operator = Operator.query.filter_by(till_number=session['till_number']).first()
        if operator:
            return jsonify({
                'operator_name': operator.operator_name,
                'role': operator.role,
                'till_number': operator.till_number,
                'created_at': operator.created_at
            })
        else:
            return jsonify({'message': 'Operator not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

@app.route('/api/logout', methods=['POST'])
def admin_logout():
    session.clear()  # ✅ Clears all session data
    return jsonify({"success": True, "message": "Logout successful"}), 200  # ✅ Success


@app.route('/logout', methods=['POST'])
def logout():
    # Remove user-related session data (like login credentials)
    session.clear()
    # Redirect to login page after logout
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
