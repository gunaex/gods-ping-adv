"""
Migrate the backend/gods_ping.db file specifically
"""
import sqlite3
import os

DB_PATH = "backend/gods_ping.db"

if not os.path.exists(DB_PATH):
    print(f"❌ Database not found: {DB_PATH}")
    exit(1)

print(f"📊 Migrating: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(bot_configs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    changes_made = False
    
    # Add entry/exit step columns if missing
    if 'entry_step_percent' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN entry_step_percent REAL DEFAULT 10.0")
        print("✅ Added entry_step_percent")
        changes_made = True
    
    if 'exit_step_percent' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN exit_step_percent REAL DEFAULT 10.0")
        print("✅ Added exit_step_percent")
        changes_made = True
    
    # Add notification columns if missing
    if 'notification_email' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN notification_email TEXT")
        print("✅ Added notification_email")
        changes_made = True
    
    if 'notify_on_action' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN notify_on_action INTEGER DEFAULT 0")
        print("✅ Added notify_on_action")
        changes_made = True
    
    if 'notify_on_position_size' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN notify_on_position_size INTEGER DEFAULT 0")
        print("✅ Added notify_on_position_size")
        changes_made = True
    
    if 'notify_on_failure' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN notify_on_failure INTEGER DEFAULT 0")
        print("✅ Added notify_on_failure")
        changes_made = True
    
    if 'gmail_user' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN gmail_user TEXT")
        print("✅ Added gmail_user")
        changes_made = True
    
    if 'gmail_app_password' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN gmail_app_password TEXT")
        print("✅ Added gmail_app_password")
        changes_made = True
    
    # Add profit protection columns if missing
    if 'trailing_take_profit_percent' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN trailing_take_profit_percent REAL DEFAULT 2.5")
        print("✅ Added trailing_take_profit_percent")
        changes_made = True
    
    if 'hard_stop_loss_percent' not in columns:
        cursor.execute("ALTER TABLE bot_configs ADD COLUMN hard_stop_loss_percent REAL DEFAULT 3.0")
        print("✅ Added hard_stop_loss_percent")
        changes_made = True
    
    if changes_made:
        conn.commit()
        print("✅ Migration complete!")
    else:
        print("✅ All columns already exist!")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()

finally:
    conn.close()
