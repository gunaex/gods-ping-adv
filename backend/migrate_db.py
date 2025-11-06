"""
Database migration script to add incremental position building columns
Run this once to update your existing database
"""
import sqlite3
import os
import sys

# Try multiple possible database locations
DB_PATHS = [
    "gods_ping.db",                    # Current directory
    "backend/gods_ping.db",            # From project root
    "./gods_ping.db",                  # Explicit current dir
    "../gods_ping.db",                 # Parent directory
]

DB_PATH = None
for path in DB_PATHS:
    if os.path.exists(path):
        DB_PATH = path
        break

if DB_PATH is None:
    print("❌ Database file not found in any of these locations:")
    for path in DB_PATHS:
        print(f"   - {os.path.abspath(path)}")
    print("\nℹ️  The database is created when you first run the backend server.")
    print("   Please start the backend at least once, then run this migration.")
    sys.exit(1)

print(f"📊 Connecting to database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(bot_configs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    migrations_needed = []
    
    # Check all required columns
    required_columns = {
        'entry_step_percent': 10.0,
        'exit_step_percent': 10.0,
        'trailing_take_profit_percent': 2.5,
        'hard_stop_loss_percent': 3.0
    }
    
    for col_name, default_val in required_columns.items():
        if col_name not in columns:
            migrations_needed.append((col_name, default_val))
    
    if not migrations_needed:
        print("✅ All columns already exist! No migration needed.")
    else:
        print(f"🔧 Adding {len(migrations_needed)} new columns to bot_configs table...")
        
        for col_name, default_val in migrations_needed:
            cursor.execute(f"""
                ALTER TABLE bot_configs 
                ADD COLUMN {col_name} REAL DEFAULT {default_val}
            """)
            print(f"✅ Added {col_name} column (default: {default_val})")
        
        # Commit changes
        conn.commit()
        print("✅ Database migration completed successfully!")
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(bot_configs)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"\n📋 Current bot_configs columns: {', '.join(columns_after)}")

except sqlite3.Error as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    exit(1)

finally:
    conn.close()
    print("\n🎉 Done! You can now restart your backend server.")
