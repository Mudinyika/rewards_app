# migrations/env.py
import os
import sys
from logging.config import fileConfig

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the app directory to the sys.path to import app and models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../flask_api_project')))

# Import your models (and db object) from app's models.py
from app import db
from app.models import User, Card, Point, Role, UsersRoles  # Import all models here

# This is the Alembic Config object, which provides access to the configuration
config = context.config

# Set the target_metadata to reference your models' metadata
target_metadata = db.metadata

# Configure the logging for Alembic (if needed)
fileConfig(config.config_file_name)

# Other migration configuration and setup goes here...

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# Call the function to determine if Alembic should run offline or online migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
