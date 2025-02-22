from flask import (Flask,
    jsonify,
    Blueprint,
    send_from_directory,
    request,
    render_template,
    url_for,
    session,
    redirect,
    send_file,
)
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from datetime import datetime, timedelta
from sqlalchemy import text
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import json
import re
from decimal import Decimal, InvalidOperation
import os
from config import config  # Import the config dictionary
from waitress import serve


load_dotenv()  # Load environment variables from .env
print(f"DEBUG: SQLALCHEMY_DATABASE_URI = {os.getenv('SQLALCHEMY_DATABASE_URI')}")  # Check if it loads

#  Set Flask environment dynamically from .env
env = os.getenv("FLASK_ENV", "production")  # Default to production

#  Debugging: Check if the database URI is actually loaded
db_uri = os.getenv("SQLALCHEMY_DATABASE_URI")
print(f" DEBUG: Loaded SQLALCHEMY_DATABASE_URI = {db_uri}")

if not db_uri:
    raise RuntimeError("ERROR: SQLALCHEMY_DATABASE_URI is not set! Check your .env file.")


# Initialize your Flask app and the database object
app = Flask(__name__, static_folder="react_build")


app.config.from_object(config[env])  # Load production or development config

# Initialize Flask Extensions
mail = Mail(app)
db = SQLAlchemy(app)

# Setup CORS for security
CORS(app, resources={r"/api/*": {"origins": ["https://192.168.1.197:8443"], "supports_credentials": True}})



# Load admin credentials
ADMIN_KEY = os.getenv("ADMIN_KEY")
SUPERUSER_HASHED_PASSWORD = os.getenv("SUPERUSER_HASHED_PASSWORD")

# Database connection details
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Create a serializer for generating secure tokens
s = URLSafeTimedSerializer(app.config["MAIL_PASSWORD"])


superuser_password = "superman"  # Change this to your desired password
hashed_password = generate_password_hash(superuser_password, method="pbkdf2:sha256")

print("Superuser Hashed Password:", hashed_password)


def clear_session(preserve_admin=False):
    print("clear_session called with preserve_admin =", preserve_admin)
    """
    Clears the session data.

    If preserve_admin is True, this function will preserve the admin-related keys
    ('admin_id', 'username', 'role') and clear all other keys. Otherwise, it clears everything.
    """
    if preserve_admin:
        admin_keys = {"admin_id", "username", "role"}
        keys_to_remove = [key for key in session.keys() if key not in admin_keys]
    else:
        keys_to_remove = list(session.keys())
    for key in keys_to_remove:
        session.pop(key, None)
    if preserve_admin:
        print("Cleared till operator session data; admin session preserved.")
    else:
        print("Cleared previous session data.")


@app.route("/reset-password-request", methods=["POST"])
def reset_password_request():
    email = request.form["email"]

    # Query the database for the user instead of checking 'users'
    user = db.session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()

    if not user:
        return jsonify({"error": "Email not found."}), 400

    # Generate a password reset token
    token = s.dumps(email, salt="password-reset-salt")

    # Send reset email with the token
    reset_url = url_for("reset_password", token=token, _external=True)
    msg = Message("Password Reset Request", recipients=[email])
    msg.body = f"To reset your password, click the following link: {reset_url}"
    try:
        mail.send(msg)
        return jsonify({"message": "A password reset link has been sent to your email."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=3600)  # 1 hour expiration
    except SignatureExpired:
        return jsonify({"error": "The reset link has expired."}), 400

    if request.method == "POST":
        new_password = request.form["password"]

        # ✅ Query user from database
        user = db.session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()

        if not user:
            return jsonify({"error": "User not found."}), 400

        # ✅ Update the password in the database
        hashed_password = generate_password_hash(new_password)
        db.session.execute(text("UPDATE users SET password_hash = :password WHERE email = :email"), {"password": hashed_password, "email": email})
        db.session.commit()

        return jsonify({"message": "Your password has been successfully reset."}), 200

    return render_template("reset_password.html", token=token)



@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # ✅ Query the database to check if the email exists
    user = db.session.execute(
        text("SELECT * FROM users WHERE email = :email"), {"email": email}
    ).fetchone()

    if not user:
        return jsonify({"error": "Email not found."}), 404

    # ✅ Generate a password reset token
    token = s.dumps(email, salt="password-reset-salt")

    # ✅ Send reset email with the token
    reset_url = url_for("reset_password", token=token, _external=True)
    msg = Message("Password Reset Request", recipients=[email])
    msg.body = f"To reset your password, click the following link: {reset_url}"

    try:
        mail.send(msg)
        return jsonify({"success": True, "message": "Reset link sent to email!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send reset link: {str(e)}"}), 500


# ✅ Serve React App at /admin


@app.route("/admin")
@app.route("/admin/<path:path>")
def serve_react(path="index.html"):
    print(f"🛠️ Serving React: {path}")  # Debugging
    return send_from_directory(app.static_folder, path)


@app.route("/")
def index():
    return render_template("login_form.html")


# Function to create a new till operator (this would be used during setup)


def create_till_operator(till_number, operator_name, password):
    # Hash the password before saving it to the database
    hashed_password = generate_password_hash(password)

    # Connect to the MySQL database using pymysql
    connection = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
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


# Function to retrieve the hashed password for a given till_number and
# operator_name


def get_password_hash_for_operator(till_number, operator_name):
    # Connect to the MySQL database using pymysql
    connection = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
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
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
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


# ✅ Fix: Clear session before login to prevent conflicts


def clear_session():
    session_keys = list(session.keys())  # Store existing session keys
    for key in session_keys:
        session.pop(key)
    print("🧹 Cleared previous session data.")


# Route for the login page (serving the login form)
# ✅ Till Operator Login


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login_form.html")  # Serve the login page

    print("🛠️ Initiating Login Process...")  # ✅ Log Start

    # ✅ Handle JSON requests properly
    if request.is_json:
        data = request.get_json()
        operator_name = data.get("operator_name")
        password = data.get("password")
        till_number = data.get("till_number")
    else:
        # ✅ Handle form submissions (for HTML login page)
        operator_name = request.form.get("operator_name")
        password = request.form.get("password")
        till_number = request.form.get("till_number")

    use_touch_mode = request.args.get("use_touch_mode")  # Read from URL query params

    # ✅ Check for missing fields
    if not operator_name or not password or not till_number:
        print("❌ Error: Missing fields!")
        return jsonify({"error": "All fields are required."}), 400

    # ✅ Validate till number
    if till_number not in ["001", "002", "003", "004", "005"]:
        print("❌ Error: Invalid till number!")
        return jsonify({"error": "Invalid till number selected."}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch operator credentials
            cursor.execute(
                "SELECT password_hash, role FROM till_operators WHERE operator_name = %s",
                (operator_name,),
            )
            operator = cursor.fetchone()

            if not operator or not check_password_hash(operator[0], password):
                print("❌ Error: Invalid login credentials!")
                return jsonify({"error": "Invalid operator name or password."}), 401

            # ✅ Fix: Clear previous session before setting a new one
            clear_session()
            print("🧹 Cleared previous session data.")

            # Store till session in database
            cursor.execute(
                "INSERT INTO till_sessions (operator_name, till_number, session_start) VALUES (%s, %s, NOW())",
                (operator_name, till_number),
            )
            connection.commit()

            # ✅ Store new Till Operator session
            session["logged_in"] = True
            session["operator_name"] = operator_name
            session["till_number"] = till_number
            session["role"] = operator[1]
            session.modified = True  # ✅ Ensure session persists!

            print(f"✅ SESSION DATA SET: {dict(session)}")  # ✅ Log Full Session

            # ✅ JSON Response for API requests
            if request.is_json:
                return jsonify({"success": True, "message": "Login successful"}), 200

            # ✅ Redirect for HTML form-based logins
            if use_touch_mode:
                return redirect("/allocate?mode=touch")
            else:
                return redirect("/allocate_points_page")

    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    finally:
        connection.close()


def get_admin_by_username(username):
    """Fetch an admin by username using SQLAlchemy."""
    return db.session.execute(
        text(
            "SELECT id, admin_name, password_hash, role FROM admin WHERE admin_name = :username"
        ),
        {"username": username},
    ).fetchone()


@app.route("/api/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    admin = get_admin_by_username(username)
    if not admin:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    if not check_password_hash(admin.password_hash, password):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    # 🛠️ ✅ Fix: Clear any previous session before setting new session
    clear_session()

    # ✅ Store new Admin session
    session["logged_in"] = True
    session["admin_id"] = admin.id  # 🔹 Fix: Save admin ID for tracking
    session["username"] = username
    session["role"] = admin.role

    print("🔍 SESSION DATA (Admin):", session)  # ✅ Log session data

    response = jsonify(
        {"success": True, "message": "Login successful", "role": admin.role}
    )
    response.headers["Access-Control-Allow-Credentials"] = "true"

    return response, 200


# ✅ Check Login Route
@app.route("/api/check-login", methods=["GET"])
def check_login():
    if session.get("logged_in"):
        if "admin_id" in session:  # ✅ Only admins should pass for React
            return (
                jsonify(
                    {"success": True, "role": session.get("role"), "user_type": "admin"}
                ),
                200,
            )
        elif "operator_name" in session:
            return (
                jsonify(
                    {
                        "success": False,  # ❌ Block till operators from logging in React
                        "error": "Till operators must use the till system.",
                    }
                ),
                401,
            )
    return jsonify({"success": False, "error": "Not logged in"}), 401


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

@app.route("/api/check-superuser", methods=["GET"])
def check_superuser():
    """Check if the logged-in user is a superuser."""
    print("🔍 SESSION DATA (Superuser Check):", dict(session))  # Debugging log

    if "logged_in" in session:
        print("✅ User is logged in")
    else:
        print("❌ User is NOT logged in")

    if "role" in session:
        print(f"🛠️ User role found: {session['role']}")
    else:
        print("❌ No role found in session")

    if session.get("logged_in") and session.get("role") == "super":
        print("✅ Superuser confirmed")
        return jsonify({"is_superuser": True})

    print("❌ Not a superuser")
    return jsonify({"is_superuser": False}), 401

@app.route("/api/update-admin-role", methods=["POST"])
def update_admin_role():
    """Update the role of an admin (Superuser required)"""
    data = request.get_json()
    admin_id = data.get("admin_id")
    new_role = data.get("new_role")
    superuser_password = data.get("superuser_password")

    # ✅ Ensure the user is logged in and is a superuser
    if not session.get("logged_in") or session.get("role") != "super":
        return jsonify({"error": "Unauthorized. Only superusers can change roles."}), 403

    # ✅ Validate inputs
    if not admin_id or not new_role or not superuser_password:
        return jsonify({"error": "Missing required fields."}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # ✅ Fetch the password of the logged-in superuser
        cursor.execute("SELECT password_hash FROM admin WHERE id = %s", (session["admin_id"],))
        superuser_record = cursor.fetchone()

        # ✅ Check if the password is correct
        if not superuser_record or not check_password_hash(superuser_record[0], superuser_password):
            return jsonify({"error": "Incorrect superuser password."}), 401

        # ✅ Ensure the admin exists before updating
        cursor.execute("SELECT id FROM admin WHERE id = %s", (admin_id,))
        admin_record = cursor.fetchone()
        if not admin_record:
            return jsonify({"error": "Admin not found."}), 404

        # ✅ Update the admin role
        cursor.execute("UPDATE admin SET role = %s WHERE id = %s", (new_role, admin_id))
        connection.commit()

        return jsonify({"success": True, "message": "Role updated successfully."}), 200
    except Exception as e:
        print("❌ Error updating role:", e)
        return jsonify({"error": "Database error occurred."}), 500
    finally:
        cursor.close()
        connection.close()




def create_app():
    print("App creation started...")
    # Create a Flask application instance
    app = Flask(__name__)

    # Set up the configuration (this will look for the Config class in
    # config.py)
    app.config.from_object("app.config.Config")

    # Initialize the database with the app
    db.init_app(app)

    # You can also set up routes, blueprints, etc., here
    with app.app_context():
        # Print to see if table creation is working
        print("Creating database tables...")
        db.create_all()

    return app


@app.route("/api/admins", methods=["GET"])
def get_admins():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, admin_name, admin_surname, admin_picture, role FROM admin"
    )
    admins = cursor.fetchall()

    return (
        jsonify(
            {
                "admins": [
                    {
                        "id": a[0],
                        "admin_name": a[1],
                        "admin_surname": a[2],
                        "admin_picture": a[3],
                        "role": a[4],
                    }
                    for a in admins
                ]
            }
        ),
        200,
    )


@app.route("/api/manage-permissions", methods=["POST"])
def manage_permissions():
    """Super User updates roles for Admins, Managers, and Till Operators"""
    connection = None
    cursor = None
    try:
        data = request.get_json()
        # The admin whose role is being updated
        admin_id = data.get("admin_id")
        new_role = data.get("new_role")  # The new role to be assigned
        super_user_key = data.get("super_user_key")  # Authorization check

        # Convert role to lowercase to match DB storage
        if new_role:
            new_role = new_role.lower()

        # Validate role
        valid_roles = {"admin", "manager", "super"}
        if new_role not in valid_roles:
            return jsonify({"error": "Invalid role provided"}), 400

        # Ensure only the super user can update roles
        if super_user_key != SUPERUSER_HASHED_PASSWORD:
            return (
                jsonify(
                    {"error": "Unauthorized. Only Super User can manage permissions."}
                ),
                403,
            )

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


@app.route("/api/get-transaction-id", methods=["GET"])
def get_transaction_id():
    """Fetch an unused transaction ID."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT transaction_id FROM predefined_transactions WHERE used = 0 LIMIT 1"
        )
        transaction_record = cursor.fetchone()

        cursor.close()
        connection.close()

        if transaction_record:
            return jsonify({"transaction_id": transaction_record[0]}), 200
        else:
            return jsonify({"error": "No available transaction IDs"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/till-operators", methods=["GET"])
def get_till_operators():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, till_number, operator_name FROM till_operators")
    operators = cursor.fetchall()

    return (
        jsonify(
            {
                "till_operators": [
                    {"id": o[0], "till_number": o[1], "operator_name": o[2]}
                    for o in operators
                ]
            }
        ),
        200,
    )


@app.route("/api/manage_user", methods=["POST", "PUT", "DELETE", "GET"])
def manage_user():
    """Route to Add, Edit, Delete, or Fetch Admins, Till Operators, and Regular Users"""

    admin_id = session.get("admin_id")  # ✅ Get Admin ID from session
    role = session.get("role")  # ✅ Get logged-in admin role

    if not admin_id:
        return jsonify({"error": "Unauthorized: Admin ID missing"}), 403

    try:
        data = request.args if request.method == "GET" else request.get_json()
        print("Received Data:", data)

        action = data.get("action")  # 'add', 'edit', 'delete', 'fetch'
        user_type = data.get("user_type")
        user_id = data.get("id")  # Needed for edit/delete/fetch

        if not action or not user_type:
            return jsonify({"error": "Missing required parameters"}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        # ✅ Fetch the target user's role if modifying an existing user
        target_role = None
        if user_id:
            cursor.execute("SELECT role FROM admin WHERE id = %s", (user_id,))
            target_role = cursor.fetchone()
            if target_role:
                target_role = target_role[0]  # Extract role value

        # 🚨 Restrict Manager Modifications (Managers CANNOT perform CRUD)
        if role == "manager":
            if action in ["add", "edit", "delete"]:
                return jsonify({"error": "Managers cannot perform this action"}), 403

        # 🚨 Restrict Admin Modifications 🚨
        if role == "admin":
            if target_role == "super":
                return jsonify({"error": "Admins cannot modify Super Users"}), 403
            if action == "add" and data.get("role") == "superuser":
                return jsonify({"error": "Admins cannot create a Superuser"}), 403
            if user_type == "admin" and action in ["edit", "delete"]:
                return jsonify({"error": "Admins cannot modify other Admins"}), 403

        # ✅ Allow Super Users Full Control
        if role == "super":
            print("✅ Super User action allowed.")

        # Handle different actions
        if action == "add":
            return add_user(data, user_type, cursor, connection)
        elif action == "edit" and user_id:
            return edit_user(data, user_type, user_id, cursor, connection)
        elif action == "delete" and user_id:
            return delete_user(user_id, user_type, cursor, connection)
        elif action == "fetch":
            return fetch_users(user_type)
        else:
            return jsonify({"error": "Invalid action or missing user_id"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def add_user(data, user_type, cursor, connection):
    """Add an admin, till operator, or regular user"""

    admin_id = session.get("admin_id")
    admin_key = data.get("admin_key")

    # ✅ Ensure admin is logged in OR a valid admin key is provided
    if not admin_id and (not admin_key or admin_key != os.getenv("ADMIN_KEY")):
        return jsonify({"error": "Unauthorized: Admin ID or valid key required"}), 403

    print(f"Received Data for {user_type}: {data}")

    # Define required fields & table
    user_config = {
        "admin": {
            "fields": [
                "admin_name", "admin_surname", "admin_phone_number",
                "admin_id_number", "password", "role"
            ],
            "table": "admin",
            "columns": "admin_name, admin_surname, admin_phone_number, admin_id_number, admin_picture, password_hash, role"
        },
        "till_operator": {
            "fields": ["operator_name", "password", "role"],
            "table": "till_operators",
            "columns": "till_number, operator_name, password_hash, role"
        },
        "user": {
            "fields": ["email", "name", "password"],
            "table": "users",
            "columns": "email, name, password_hash"
        }
    }

    if user_type not in user_config:
        return jsonify({"error": "Invalid user type"}), 400

    required_fields = user_config[user_type]["fields"]
    table_name = user_config[user_type]["table"]
    columns = user_config[user_type]["columns"]

    missing_fields = [field for field in required_fields if field not in data and field != "till_number"]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)} for {user_type}"}), 400

    password_hash = generate_password_hash(data["password"])
    values = []  # till_number should be None by default
    
    # Only insert None for till_number if the user is a till_operator
    if user_type == "till_operator":
        values.append(None)  # till_number should be None
    
    values.extend([data[field] if field != "password" else password_hash for field in required_fields])


    if user_type == "admin":
        values.insert(4, data.get("admin_picture", None))

    query = f"INSERT INTO {table_name} ({columns}) VALUES ({', '.join(['%s'] * len(values))})"
    cursor.execute(query, tuple(values))
    connection.commit()

    return jsonify({"message": f"{user_type.capitalize()} added successfully"}), 201


def edit_user(data, user_type, user_id, cursor, connection):
    """Edit an existing admin, till operator, or regular user"""

    table_mappings = {
        "admin": ("admin", ["admin_name", "admin_surname", "admin_phone_number", "admin_id_number", "admin_picture", "password", "role"]),
        "till_operator": ("till_operators", ["till_number", "operator_name", "password", "role"]),
        "user": ("users", ["email", "name", "password"])
    }

    if user_type not in table_mappings:
        return jsonify({"error": "Invalid user type"}), 400

    table_name, valid_fields = table_mappings[user_type]

    update_fields = []
    values = []

    for field in valid_fields:
        if field in data:
            if field == "password":
                update_fields.append("password_hash = %s")
                values.append(generate_password_hash(data[field]))
            else:
                update_fields.append(f"{field} = %s")
                values.append(data[field])

    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(user_id)
    query = f"UPDATE {table_name} SET {', '.join(update_fields)} WHERE id = %s"
    cursor.execute(query, tuple(values))
    connection.commit()

    return jsonify({"message": f"{user_type.capitalize()} updated successfully"}), 200

def delete_user(user_id, user_type, cursor, connection):
    """Delete an admin, till operator, or regular user"""
    table_name = (
        "admin"
        if user_type == "admin"
        else "till_operators" if user_type == "till_operator" else "users"
    )
    cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (user_id,))
    connection.commit()

    return jsonify({"message": f"{user_type.capitalize()} deleted successfully"}), 200

def fetch_users(user_type):
    """Fetch all admins, till operators, or users"""

    connection = get_db_connection()
    cursor = connection.cursor()

    table_mappings = {"admin": "admin", "till_operator": "till_operators", "user": "users"}
    table_name = table_mappings.get(user_type)

    if not table_name:
        return jsonify({"error": "Invalid user type"}), 400

    cursor.execute(f"SELECT * FROM {table_name}")
    users = cursor.fetchall() or []  # ✅ Return empty list if no users exist

    columns = [column[0] for column in cursor.description]
    users_data = [{columns[i]: user[i] for i in range(len(columns))} for user in users]

    return jsonify(users_data), 200



@app.route("/api/metrics", methods=["GET"])
def get_dashboard_metrics():
    try:
        # Query the metrics data
        result = db.session.execute(
            text(
                """
            SELECT COUNT(*) FROM users
        """
            )
        )
        total_users = result.fetchone()[0]

        result = db.session.execute(
            text(
                """
            SELECT COUNT(*) FROM till_operators
        """
            )
        )
        till_operator_count = result.fetchone()[0]

        result = db.session.execute(
            text(
                """
            SELECT COUNT(*) FROM admin
        """
            )
        )
        admin_count = result.fetchone()[0]

        # Assuming only one superuser
        superuser_count = 1

        result = db.session.execute(
            text(
                """
            SELECT SUM(points) FROM point_history
            WHERE transaction_type = 'add'
            AND timestamp >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """
            )
        )
        total_added_points = result.fetchone()[0] or 0

        result = db.session.execute(
            text(
                """
            SELECT SUM(points) FROM point_history
            WHERE transaction_type = 'remove'
            AND timestamp >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """
            )
        )
        total_removed_points = result.fetchone()[0] or 0

        result = db.session.execute(
            text(
                """
            SELECT COUNT(*) FROM users
            WHERE created_at >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """
            )
        )
        new_users_this_month = result.fetchone()[0]

        return (
            jsonify(
                {
                    "total_users": total_users,
                    "till_operator_count": till_operator_count,
                    "admin_count": admin_count,
                    "superuser_count": superuser_count,
                    "total_added_points": total_added_points,
                    "total_removed_points": total_removed_points,
                    "new_users_this_month": new_users_this_month,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error: {str(e)}")  # Debugging error in the console
        return jsonify({"error": str(e)}), 500




@app.route("/api/allocate-points", methods=["POST"])
def allocate_points():
    """Allocate or remove points for users."""

    data = request.get_json()
    print("🔍 Received Data:", data)  # ✅ Log incoming data
    
    try:
        # ✅ Convert points to Decimal safely
        points = Decimal(str(data.get("points")))
        if points <= 0:
            return jsonify({"error": "Points must be greater than zero"}), 400
    except (TypeError, ValueError, InvalidOperation) as e:
        print(f"❌ Decimal Conversion Error: {e}")
        return jsonify({"error": "Invalid points value. Must be a valid number."}), 400

    # ✅ Extract data from request
    user_id = data.get("user_id")
    transaction_type = data.get("transaction_type")
    admin_key = data.get("admin_key")
    bypass_admin_key = data.get("bypass_admin_key", False)  # ✅ Flag for keypad mode
    till_number = data.get("till_number")  # ✅ Only required for Admins

    # ✅ Only check admin key if not using keypad mode
    if not bypass_admin_key and admin_key != ADMIN_KEY:
        return jsonify({"error": "Invalid admin key"}), 403

    # ✅ Validate required fields
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    if points is None:
        return jsonify({"error": "Points value is required"}), 400
    if not transaction_type:
        return jsonify({"error": "Transaction type is required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # ✅ Fetch an unused transaction ID
        cursor.execute(
            "SELECT transaction_id FROM predefined_transactions WHERE used = 0 LIMIT 1"
        )
        transaction_record = cursor.fetchone()
        if not transaction_record:
            return jsonify({"error": "No available transaction IDs"}), 400

        transaction_id = transaction_record[0]

        # ✅ Fetch session role
        role = session.get('role')
        admin_id = session.get('admin_id', None)  # Admin ID if present
        
        operator_name = None
        allocated_by = "-"

        # ✅ Handling for Till Operators
        if role == "till_operator":
            till_number = session.get('till_number')
            operator_name = session.get('operator_name')

            print(f"🔍 Debug: Till Operator - Till={till_number}, Operator={operator_name}")
            if not till_number or not operator_name:
                print("❌ Error: Till operator session missing till number.")
                return jsonify({"error": "Till operator details missing. Please log in again."}), 400

        # ✅ Handling for Admins (including when both admin and operator are logged in on the same till)
        elif role in ["admin", "super"]:
            if not till_number:
                return jsonify({"error": "Till number is required for admin allocation"}), 400

            # ✅ Check if a Till Operator is logged into the specified till.
            cursor.execute(
                "SELECT operator_name FROM till_sessions WHERE till_number = %s ORDER BY session_start DESC LIMIT 1",
                (till_number,),
            )
            operator = cursor.fetchone()
            if operator:
                operator_name = operator[0]  # ✅ Active till operator's name
            else:
                operator_name = "-"  # ✅ No operator logged in on this till

            allocated_by = session.get("username")  # ✅ Admin's username

            print(f"✅ Admin Allocation: Till={till_number}, Allocated By={allocated_by}, Operator={operator_name}")

        # ✅ Check if the user exists and retrieve current points
        cursor.execute("SELECT points FROM users WHERE id = %s", (user_id,))
        current_points = cursor.fetchone()
        if not current_points:
            return jsonify({"error": "User not found"}), 404

        current_points = Decimal(str(current_points[0])) if current_points[0] is not None else Decimal("0")

        # ✅ Perform correct operation based on transaction type
        if transaction_type == "add":
            new_points = current_points + points
        elif transaction_type == "remove":
            if points > current_points:
                return jsonify({"error": "Insufficient points for removal"}), 400
            new_points = current_points - points
        else:
            return jsonify({"error": "Invalid transaction type"}), 400

        # ✅ Update the user's points
        cursor.execute(
            "UPDATE users SET points = %s WHERE id = %s", (new_points, user_id)
        )

        # ✅ Insert transaction into `point_history`
        cursor.execute(
            """
            INSERT INTO point_history 
            (user_id, points, transaction_type, transaction_id, till_number, operator_name, allocated_by) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            (
                user_id,
                points,
                transaction_type,
                transaction_id,
                till_number,
                operator_name,
                allocated_by,
            ),
        )

        # ✅ Mark the transaction ID as used
        cursor.execute(
            "UPDATE predefined_transactions SET used = 1 WHERE transaction_id = %s",
            (transaction_id,),
        )

        connection.commit()

        return jsonify({"message": "Points successfully updated"}), 200

    except Exception as e:
        print(f"❌ Database Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


        # ✅ Log admin action in `audit_log`
        if role in ["admin", "super"]:
            ip_address = get_client_ip()
            
            # ✅ Ensure proper decimal formatting for logging
            formatted_points = f"{points:.2f}"  # ✅ Standardize decimal format

            log_admin_action(
                admin_id,
                "ALLOCATE_POINTS",
                f"Allocated {formatted_points} points ({transaction_type}) to user ID {user_id} via till {till_number}. "
                f"Operator: {operator_name if operator_name != '-' else 'N/A'}.",
                ip_address,
            )

        print("✅ Points successfully allocated!")

        return (
            jsonify(
                {
                    "message": "Points successfully updated",
                    "transaction_id": transaction_id,
                }
            ),
            200,
        )




# Route to serve Allocate Points pages based on mode
@app.route("/allocate")
def allocate_page():
    if "operator_name" not in session:
        return redirect(url_for("login"))  # Redirect to login if not authenticated

    mode = request.args.get("mode", "standard")  # Default to standard mode
    if mode == "touch":
        return render_template(
            "AllocatePointsTouch.html",
            operator_name=session["operator_name"],
            till_number=session["till_number"],
            role=session["role"],
        )  # Pass session data
    return render_template(
        "AllocatePoints.html",
        operator_name=session["operator_name"],
        till_number=session["till_number"],
        role=session["role"],
    )


@app.route("/api/search-users", methods=["GET"])
def search_users():
    search_query = request.args.get("query", "")

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Search users by ID or name
        cursor.execute(
            """ 
            SELECT id, name FROM users 
            WHERE id LIKE %s OR name LIKE %s
            """,
            ("%" + search_query + "%", "%" + search_query + "%"),
        )

        users = cursor.fetchall()

        # Format the response to return an array of objects
        formatted_users = [{"id": user[0], "name": user[1]} for user in users]

        return jsonify({"users": formatted_users}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


@app.route("/api/users/<int:user_id>", methods=["GET"])
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
            (user_id,),
        )
        last_transaction = cursor.fetchone()

        # Format the last transaction details
        last_transaction_info = None
        if last_transaction:
            points, transaction_type, timestamp = last_transaction
            last_transaction_info = (
                f"{transaction_type.capitalize()} {points} points on {timestamp}"
            )

        # Return the user details
        return (
            jsonify(
                {
                    "name": user[0],
                    "points": user[1],
                    "last_transaction": last_transaction_info,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


# Models

# Define the User model


class Operator(db.Model):
    __tablename__ = "till_operators"

    id = db.Column(db.Integer, primary_key=True)
    till_number = db.Column(db.String(50), unique=True, nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(50), nullable=False, default="admin"
    )  # 'admin', 'user', 'superuser'

    def __init__(self, till_number, operator_name, password, role="admin"):
        self.till_number = till_number
        self.operator_name = operator_name
        self.password_hash = generate_password_hash(password)
        self.role = role

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

    def __repr__(self):
        return f"<Admin {self.admin_name} {self.admin_surname}>"


# Route to add points
@app.route("/api/card-swipe", methods=["POST"])
def handle_card_swipe():
    """
    Handle magnetic stripe card swipe, fetch user information by ID.
    """
    data = request.get_json()
    card_data = data.get("card_data")  # Raw data from the magnetic stripe card reader

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
            (user_id,),
        )
        last_transaction = cursor.fetchone()

        last_transaction_info = None
        if last_transaction:
            points, transaction_type, timestamp = last_transaction
            last_transaction_info = (
                f"{transaction_type.capitalize()} {points} points on {timestamp}"
            )

        # Return user information
        return (
            jsonify(
                {
                    "user_id": user_id,
                    "name": user[0],
                    "points": user[1],
                    "last_transaction": last_transaction_info,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


# Route for the allocate points page
@app.route("/allocate_points_page", methods=["GET"])
def allocate_points_page():
    if not session.get("logged_in"):
        return redirect(url_for("index"))  # Redirect to login if not authenticated

    # Extract data for rendering or API responses
    operator_name = session.get("operator_name", "Unknown")
    till_number = session.get("till_number", "Unknown")
    role = session.get("role", "Unknown")

    return render_template(
        "AllocatePoints.html",
        till_number=till_number,
        operator_name=operator_name,
        role=role,
    )


@app.route("/api/operator_info", methods=["GET"])
def get_operator_info():
    # Check if 'till_number' is in the session
    if "till_number" not in session:
        return redirect(url_for("login"))  # Redirect to login if not logged in

    try:
        operator = Operator.query.filter_by(till_number=session["till_number"]).first()
        if operator:
            return jsonify(
                {
                    "operator_name": operator.operator_name,
                    "role": operator.role,
                    "till_number": operator.till_number,
                    "created_at": operator.created_at,
                }
            )
        else:
            return jsonify({"message": "Operator not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add_operator", methods=["POST"])
def add_operator():
    # Get data from the request body
    data = request.get_json()

    # Validate input data
    till_number = data.get("till_number")
    operator_name = data.get("operator_name")
    password = data.get("password")
    role = data.get("role")

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
        role=role,
    )

    # Add operator to the database
    db.session.add(new_operator)
    db.session.commit()

    return jsonify({"message": "Operator added successfully"}), 201


@app.route("/logout", methods=["POST"])
def logout():
    """Logout Till Operators, Archive Session, and Redirect to Login Page"""

    print("🛠️ Initiating Logout...")

    # ✅ Check full session before doing anything
    session_data = dict(session)  # Store full session snapshot
    print(f"🔍 Full Session Data BEFORE Logout: {session_data}")

    # ✅ Capture session values BEFORE clearing
    operator_name = session_data.get("operator_name")
    till_number = session_data.get("till_number")
    admin_id = session_data.get("admin_id")
    role = session_data.get("role")

    if operator_name and till_number:
        print(f"✅ Logging Out: Operator={operator_name}, Till={till_number}")
        archive_and_remove_till_session(operator_name, till_number)
    else:
        print(
            f"⚠️ Warning: Operator Name or Till Number Missing During Logout! (operator_name={operator_name}, till_number={till_number})"
        )

    # ✅ Explicitly remove only Till Operator Session Data
    session_keys_to_remove = ["logged_in", "till_number", "operator_name", "role"]
    for key in session_keys_to_remove:
        session.pop(key, None)

    print(f"🔍 Full Session Data AFTER Logout: {dict(session)}")  # ✅ Log what remains

    # ✅ Restore admin session if applicable
    if admin_id and role in ["admin", "super"]:
        session["admin_id"] = admin_id
        session["role"] = role
        print("✅ Admin session preserved!")
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Till operator logged out, admin session preserved",
                }
            ),
            200,
        )

    print("✅ Logout complete. Redirecting to login page...")
    
    # ✅ Redirect to login page if accessed from a browser
    if request.headers.get("Accept", "").startswith("text/html"):
        return redirect("/login")
    
    # ✅ Return JSON response for API clients (Postman)
    return jsonify({"success": True, "message": "Logout successful"}), 200


@app.route("/api/logout", methods=["POST"])
def admin_logout():
    """Logout Admins only (without affecting Till Operators)"""

    print("🔍 Before Admin Logout: SESSION DATA:", session)  # Debugging

    if "admin_id" in session:  # ✅ Only clear Admin session
        session.pop("logged_in", None)
        session.pop("admin_id", None)
        session.pop("username", None)
        session.pop("role", None)

    print("✅ After Admin Logout: SESSION DATA:", session)  # Debugging
    return jsonify({"success": True, "message": "Admin logout successful"}), 200


def archive_and_remove_till_session(operator_name, till_number):
    """Archive a specific till session immediately upon logout"""

    if not operator_name or not till_number:
        print("⚠️ Skipping archive: Missing operator or till number.")
        return

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # ✅ Archive the till session before deleting it
        cursor.execute(
            """
            INSERT INTO till_sessions_archive (operator_name, till_number, session_start, session_end)
            SELECT operator_name, till_number, session_start, NOW()
            FROM till_sessions
            WHERE operator_name = %s AND till_number = %s
        """,
            (operator_name, till_number),
        )

        # ✅ Delete the session from active `till_sessions`
        cursor.execute(
            "DELETE FROM till_sessions WHERE operator_name = %s AND till_number = %s",
            (operator_name, till_number),
        )

        connection.commit()
        print(
            f"✅ Archived and removed session for {operator_name} (Till {till_number})"
        )

    except Exception as e:
        print(f"❌ Error archiving till session: {str(e)}")

    finally:
        cursor.close()
        connection.close()


@app.route("/api/generate-report", methods=["GET"])
def generate_report():
    """Generate a transaction report with totals and optional till filtering."""
    try:
        # Get filters from query params
        report_type = request.args.get("report_type")  # daily, weekly, monthly, yearly
        till_number = request.args.get("till_number")    # Optional till filter
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Determine date range based on report type
        today = datetime.today().strftime("%Y-%m-%d")
        if report_type == "daily":
            start_date = end_date = today
        elif report_type == "weekly":
            start_date = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today
        elif report_type == "monthly":
            start_date = (datetime.today().replace(day=1)).strftime("%Y-%m-%d")
            end_date = today
        elif report_type == "yearly":
            start_date = (datetime.today().replace(month=1, day=1)).strftime("%Y-%m-%d")
            end_date = today
        elif not start_date or not end_date:
            start_date = end_date = today  # Default to daily if no dates provided

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Updated SQL Query: Directly select from point_history
        query = """
            SELECT 
                p.till_number, 
                p.operator_name, 
                p.points, 
                p.transaction_type, 
                p.timestamp, 
                p.allocated_by,  
                u.id AS customer_id
            FROM point_history p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE DATE(p.timestamp) BETWEEN %s AND %s
        """
        params = [start_date, end_date]
        if till_number:
            query += " AND p.till_number = %s"
            params.append(till_number)
        query += " ORDER BY p.timestamp DESC"

        cursor.execute(query, tuple(params))
        transactions = cursor.fetchall()

        # Calculate Total Points Added and Removed
        cursor.execute(
            """ 
            SELECT 
                SUM(CASE WHEN p.transaction_type = 'add' THEN p.points ELSE 0 END) AS total_added,
                SUM(CASE WHEN p.transaction_type = 'remove' THEN p.points ELSE 0 END) AS total_removed
            FROM point_history p
            WHERE DATE(p.timestamp) BETWEEN %s AND %s
            """ + (" AND p.till_number = %s" if till_number else ""),
            tuple(params),
        )
        totals = cursor.fetchone()
        total_points_added = totals[0] if totals[0] is not None else 0
        total_points_removed = totals[1] if totals[1] is not None else 0

        cursor.close()
        connection.close()

        if not transactions:
            return jsonify({"error": "No transactions found for the selected date range."}), 404

        # Generate PDF Report
        filename = f"transaction_report_{start_date}_to_{end_date}.pdf"
        pdf_path = os.path.join(os.getcwd(), filename)
        pdf = canvas.Canvas(pdf_path, pagesize=letter)
        pdf.setTitle(f"Transaction Report ({start_date} - {end_date})")

        # Report Header
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(180, 750, f"Transaction Report ({start_date} - {end_date})")
        if till_number:
            pdf.setFont("Helvetica", 12)
            pdf.drawString(200, 730, f"Till Number: {till_number}")

        # Table Headers
        pdf.setFont("Helvetica-Bold", 10)
        headers = ["Till Number", "Operator Name", "Points", "Type", "Timestamp", "Allocated By", "Customer ID"]
        x_positions = [50, 130, 220, 280, 350, 450, 550]
        for i, header in enumerate(headers):
            pdf.drawString(x_positions[i], 710, header)

        # Transactions Data
        pdf.setFont("Helvetica", 10)
        y_position = 690
        for row in transactions:
            (till_no, op_name, points, transaction_type, timestamp, allocated_by, customer_id) = row
            data = [
                str(till_no) if till_no else "-",
                op_name if op_name else "-",
                str(points),
                transaction_type if transaction_type else "-",
                str(timestamp),
                allocated_by if allocated_by else "-",
                str(customer_id) if customer_id else "-"
            ]
            for i, text in enumerate(data):
                pdf.drawString(x_positions[i], y_position, text)
            y_position -= 20
            if y_position < 50:
                pdf.showPage()
                y_position = 750

        # Total Points Summary
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_position - 30, f"Total Points Added: {total_points_added}")
        pdf.drawString(50, y_position - 50, f"Total Points Removed: {total_points_removed}")
        pdf.save()

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/generate-admin-log-report", methods=["GET"])
def generate_admin_log_report():
    """Generate an Admin Log Report in PDF format with better layout"""

    try:
        # Get filters from query params
        report_type = request.args.get("report_type")  # daily, weekly, monthly, yearly
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Determine date range based on report type
        today = datetime.today().strftime("%Y-%m-%d")
        if report_type == "daily":
            start_date = end_date = today
        elif report_type == "weekly":
            start_date = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today
        elif report_type == "monthly":
            start_date = (datetime.today().replace(day=1)).strftime("%Y-%m-%d")
            end_date = today
        elif report_type == "yearly":
            start_date = (datetime.today().replace(month=1, day=1)).strftime("%Y-%m-%d")
            end_date = today
        elif not start_date or not end_date:
            start_date = end_date = today  # Default to daily if no dates provided

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch admin logs within the selected date range
        query = """
            SELECT a.admin_name, l.action, l.details, l.ip_address, l.timestamp
            FROM audit_log l
            JOIN admin a ON l.admin_id = a.id
            WHERE DATE(l.timestamp) BETWEEN %s AND %s
            ORDER BY l.timestamp DESC
        """
        cursor.execute(query, (start_date, end_date))
        logs = cursor.fetchall()

        cursor.close()
        connection.close()

        # **Handle No Data Case**
        if not logs:
            return jsonify({"error": "No logs found for the selected date range."}), 404

        # **Generate PDF Report**
        filename = f"admin_log_report_{start_date}_to_{end_date}.pdf"
        pdf_path = os.path.join(os.getcwd(), filename)

        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # **Table Headers**
        data = [
            ["Admin Name", "Action", "Details", "IP Address", "Timestamp"]
        ]  # Header row

        # **Add log data with text wrapping**
        for row in logs:
            admin_name, action, details, ip_address, timestamp = row

            # ✅ Sanitize details before adding to PDF
            details = sanitize_log_details(details)

            details_wrapped = Paragraph(details, styles["Normal"])  # Wrap details text
            data.append(
                [admin_name, action, details_wrapped, ip_address, str(timestamp)]
            )

        # **Define Table Layout & Styling**
        table = Table(data, colWidths=[80, 110, 220, 100, 100])  # Adjust column widths
        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.grey,
                    ),  # Header background color
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.whitesmoke,
                    ),  # Header text color
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Align text to the left
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),  # Header font
                    ("FONTSIZE", (0, 0), (-1, -1), 9),  # Font size
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),  # Header padding
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, -1),
                        colors.beige,
                    ),  # Row background color
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black,
                    ),  # Add table grid lines
                ]
            )
        )

        # **Add Table to PDF**
        elements.append(table)
        doc.build(elements)

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_client_ip():
    """Get the real IP address of the client, even if behind a proxy."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0]
    return request.remote_addr  # Direct IP if no proxy


def sanitize_log_details(details):
    """Remove sensitive fields like passwords from log details"""
    try:
        # Extract JSON-like part from the string (if present)
        match = re.search(r"\{.*\}", details)
        if match:
            json_part = match.group(0)  # Extract the JSON-like part

            # Convert string to dictionary
            data = json.loads(
                json_part.replace("'", '"')
            )  # Convert single quotes to double quotes (valid JSON)

            # Remove password field if it exists
            if "password" in data:
                del data["password"]

            # Convert back to string and rebuild the log entry
            sanitized_json = json.dumps(data, ensure_ascii=False)
            return details.replace(
                json_part, sanitized_json
            )  # Replace old JSON part with sanitized JSON

    except json.JSONDecodeError:
        pass  # If JSON parsing fails, fallback to regex

    # Regex fallback: Mask password if found in non-JSON logs
    sanitized_details = re.sub(r"'password'\s*:\s*'.*?'", "'password': '****'", details)
    return sanitized_details


def log_admin_action(admin_id, action, details, ip_address):
    """Logs an action performed by an admin into the audit_log table"""
    try:
        if not admin_id:
            print("❌ Error: Admin ID is missing!")
            return

        details = sanitize_log_details(details)  # ✅ Sanitize before storing
        ip_address = ip_address or "Unknown IP"

        print(
            f"✅ Logging Action: Admin ID: {admin_id}, Action: {action}, Details: {details}, IP: {ip_address}"
        )

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO audit_log (admin_id, action, details, ip_address, timestamp)
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (admin_id, action, details, ip_address))
        connection.commit()
        print("✅ Log entry added successfully!")

    except Exception as e:
        print(f"❌ Error logging admin action: {e}")
    finally:
        cursor.close()
        connection.close()


@app.route("/api/debug-session", methods=["GET"])
def debug_session():
    return jsonify(
        {
            "logged_in": session.get("logged_in", False),
            "admin_id": session.get("admin_id"),
            "role": session.get("role"),
            "username": session.get("username"),
        }
    )


if __name__ == "__main__":
    print("🚀 Running production server with Waitress...")
    serve(app, host="0.0.0.0", port=5000)  # Let Nginx handle external requests



