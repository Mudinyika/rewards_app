from argon2 import PasswordHasher

# Your test password
password = 'password123'

# Create a PasswordHasher object
ph = PasswordHasher()

# Generate a hashed password
hashed_password = ph.hash(password)

print("Hashed password:", hashed_password)
