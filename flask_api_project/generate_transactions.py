# generate_transactions.py
from app import create_app, db
from app.models import PredefinedTransaction  # Replace with the actual model(s) you need
import uuid

def generate_transaction():
    """
    Generate a new transaction and insert it into the database
    if it doesn't already exist.
    """
    # Initialize the Flask application
    app = create_app()

    # Use the application context for database operations
    with app.app_context():
        # Logic to generate a new transaction (using UUID for uniqueness)
        transaction_id = str(uuid.uuid4())  # Unique transaction ID based on UUID
        
        # Check if the transaction already exists
        predefined_transaction = PredefinedTransaction.query.filter_by(transaction_id=transaction_id).first()

        if predefined_transaction:
            print(f"Transaction {transaction_id} already exists.")
        else:
            # Insert the transaction into the database if it doesn't exist
            try:
                new_transaction = PredefinedTransaction(transaction_id=transaction_id)
                db.session.add(new_transaction)
                db.session.commit()
                print(f"Transaction {transaction_id} generated and added to the database.")
            except Exception as e:
                db.session.rollback()  # Roll back in case of an error
                print(f"Failed to generate transaction {transaction_id}: {e}")

if __name__ == "__main__":
    generate_transaction()  # Call the function when the script is executed directly
