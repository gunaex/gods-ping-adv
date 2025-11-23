import logging
from sqlalchemy import inspect, text
from app.db import engine

logger = logging.getLogger(__name__)

def run_db_migrations():
    """
    Check for missing columns in the database and add them if necessary.
    This handles schema evolution without needing a full migration tool like Alembic for now.
    """
    try:
        inspector = inspect(engine)
        
        # Check if table exists first
        if not inspector.has_table("bot_configs"):
            logger.info("Table 'bot_configs' does not exist yet. Skipping migration (will be created by create_all).")
            return

        columns = [c['name'] for c in inspector.get_columns('bot_configs')]
        logger.info(f"Existing columns in bot_configs: {columns}")

        with engine.connect() as conn:
            # List of columns to check and add
            # Format: (column_name, type_sql, default_value_sql)
            # Note: SQLite and Postgres have slightly different syntax, but ADD COLUMN is mostly standard.
            # We use generic types that work on both (FLOAT, INTEGER, TEXT, BOOLEAN).
            
            migrations = [
                ('kill_switch_baseline', 'FLOAT', 'NULL'),
                ('kill_switch_last_trigger', 'TIMESTAMP', 'NULL'), # TIMESTAMP works in PG, DATETIME in SQLite usually mapped
                ('kill_switch_cooldown_minutes', 'INTEGER', '60'),
                ('kill_switch_consecutive_breaches', 'INTEGER', '3'),
                ('cryptopanic_api_key', 'VARCHAR', 'NULL'),
                ('gods_mode_enabled', 'BOOLEAN', 'FALSE'),
                ('tennis_mode_enabled', 'BOOLEAN', 'FALSE'),
                ('notification_email', 'VARCHAR', 'NULL'),
                ('notify_on_action', 'BOOLEAN', 'FALSE'),
                ('notify_on_position_size', 'BOOLEAN', 'FALSE'),
                ('notify_on_failure', 'BOOLEAN', 'FALSE'),
                ('gmail_user', 'VARCHAR', 'NULL'),
                ('gmail_app_password', 'VARCHAR', 'NULL'),
            ]

            for col_name, col_type, default_val in migrations:
                if col_name not in columns:
                    logger.info(f"Migrating: Adding column '{col_name}' to bot_configs...")
                    try:
                        # Construct SQL based on dialect if needed, but simple ADD COLUMN is standard
                        # For boolean defaults in SQL: FALSE/TRUE or 0/1
                        default_clause = ""
                        if default_val != 'NULL':
                            default_clause = f"DEFAULT {default_val}"
                        
                        # Adjust type for SQLite vs Postgres if needed
                        # SQLAlchemy engine.name can be 'sqlite' or 'postgresql'
                        
                        sql = f"ALTER TABLE bot_configs ADD COLUMN {col_name} {col_type} {default_clause}"
                        conn.execute(text(sql))
                        conn.commit()
                        logger.info(f"✅ Added column {col_name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to add column {col_name}: {e}")
                        # Don't raise, try next column
            
            logger.info("Database migration check completed.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
