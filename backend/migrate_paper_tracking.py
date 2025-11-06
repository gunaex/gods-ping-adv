"""
Database migration: Add paper_trading_snapshots table
Run this to add the performance tracking table
"""
import sqlite3
from datetime import datetime

DB_PATH = "gods_ping.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='paper_trading_snapshots'
    """)
    
    if cursor.fetchone():
        print("✓ Table 'paper_trading_snapshots' already exists")
    else:
        print("Creating table 'paper_trading_snapshots'...")
        cursor.execute("""
            CREATE TABLE paper_trading_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol VARCHAR,
                bot_type VARCHAR,
                timestamp DATETIME NOT NULL,
                starting_balance FLOAT DEFAULT 0.0,
                current_balance FLOAT DEFAULT 0.0,
                quantity_held FLOAT DEFAULT 0.0,
                avg_buy_price FLOAT DEFAULT 0.0,
                current_price FLOAT DEFAULT 0.0,
                realized_pl FLOAT DEFAULT 0.0,
                unrealized_pl FLOAT DEFAULT 0.0,
                total_pl FLOAT DEFAULT 0.0,
                pl_percent FLOAT DEFAULT 0.0,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate FLOAT DEFAULT 0.0,
                max_drawdown FLOAT DEFAULT 0.0,
                sharpe_ratio FLOAT DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_pts_user_id ON paper_trading_snapshots(user_id)")
        cursor.execute("CREATE INDEX idx_pts_symbol ON paper_trading_snapshots(symbol)")
        cursor.execute("CREATE INDEX idx_pts_timestamp ON paper_trading_snapshots(timestamp)")
        
        conn.commit()
        print("✓ Table created successfully")
    
    conn.close()
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
