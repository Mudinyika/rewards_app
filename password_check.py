from werkzeug.security import generate_password_hash, check_password_hash

# Hash the password
password = "test"
hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
print("Generated Hash:", hashed_password)

# Validate the password
if check_password_hash(hashed_password, password):
    print("Password is correct")
else:
    print("Password is incorrect")
