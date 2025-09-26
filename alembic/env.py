import sys
import os
from dotenv import load_dotenv
# Load .env file before anything else
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add your app to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.db.base import Base  # <-- import your Base
from app.core.config import settings  # <-- import your settings

# Import all models so Alembic can detect them
from app.models import users, workflow, webhook, credentials

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Set your database URL from settings
config.set_main_option('sqlalchemy.url', settings.MIGRATION_DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=settings.MIGRATION_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()