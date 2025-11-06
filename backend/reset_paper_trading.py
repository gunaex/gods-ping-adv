"""
Reset Paper Trading Data
Clears all paper trading trades and snapshots to start fresh
"""
import sqlite3
from datetime import datetime

DB_PATH = "gods_ping.db"


def reset_paper_trading(user_id: int = None):
    """
    Reset paper trading data.
    
    Args:
        user_id: If provided, only reset for specific user. Otherwise reset all.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔄 Resetting Paper Trading Data...")
        print("=" * 50)
        
        # Count current data
        if user_id:
            cursor.execute("SELECT COUNT(*) FROM trades WHERE user_id = ? AND status IN ('completed_paper', 'simulated')", (user_id,))
            trade_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM paper_trading_snapshots WHERE user_id = ?", (user_id,))
            snapshot_count = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM trades WHERE status IN ('completed_paper', 'simulated')")
            trade_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM paper_trading_snapshots")
            snapshot_count = cursor.fetchone()[0]
        
        print(f"📊 Current data:")
        print(f"   - Paper trades: {trade_count}")
        print(f"   - Performance snapshots: {snapshot_count}")
        
        if trade_count == 0 and snapshot_count == 0:
            print("\n✅ No paper trading data found. Already clean!")
            return
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will delete:")
        print(f"   - {trade_count} paper trades")
        print(f"   - {snapshot_count} performance snapshots")
        if user_id:
            print(f"   For user ID: {user_id}")
        else:
            print(f"   For ALL users")
        
        confirm = input("\nType 'YES' to confirm deletion: ")
        if confirm != 'YES':
            print("❌ Reset cancelled.")
            return
        
        # Delete paper trading data
        if user_id:
            # Delete paper trades for specific user
            cursor.execute("""
                DELETE FROM trades 
                WHERE user_id = ? 
                AND status IN ('completed_paper', 'simulated')
            """, (user_id,))
            deleted_trades = cursor.rowcount
            
            # Delete snapshots for specific user
            cursor.execute("DELETE FROM paper_trading_snapshots WHERE user_id = ?", (user_id,))
            deleted_snapshots = cursor.rowcount
        else:
            # Delete all paper trades
            cursor.execute("DELETE FROM trades WHERE status IN ('completed_paper', 'simulated')")
            deleted_trades = cursor.rowcount
            
            # Delete all snapshots
            cursor.execute("DELETE FROM paper_trading_snapshots")
            deleted_snapshots = cursor.rowcount
        
        conn.commit()
        
        print("\n✅ Reset Complete!")
        print(f"   - Deleted {deleted_trades} paper trades")
        print(f"   - Deleted {deleted_snapshots} snapshots")
        print(f"\n💰 Your budget remains unchanged in bot_configs")
        print(f"🎮 Paper trading will start fresh from your current budget")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
    finally:
        conn.close()


def show_paper_trading_stats():
    """Show current paper trading statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("\n📊 Current Paper Trading Statistics")
        print("=" * 50)
        
        # Get users with paper trades
        cursor.execute("""
            SELECT u.id, u.username, COUNT(t.id) as trade_count
            FROM users u
            LEFT JOIN trades t ON u.id = t.user_id 
                AND t.status IN ('completed_paper', 'simulated')
            GROUP BY u.id, u.username
            ORDER BY u.id
        """)
        
        users = cursor.fetchall()
        
        for user_id, username, trade_count in users:
            print(f"\n👤 {username} (ID: {user_id})")
            print(f"   Paper trades: {trade_count}")
            
            if trade_count > 0:
                # Show recent trades
                cursor.execute("""
                    SELECT symbol, side, amount, price, timestamp
                    FROM trades
                    WHERE user_id = ? 
                    AND status IN ('completed_paper', 'simulated')
                    ORDER BY timestamp DESC
                    LIMIT 5
                """, (user_id,))
                
                recent_trades = cursor.fetchall()
                print(f"   Recent trades:")
                for symbol, side, amount, price, timestamp in recent_trades:
                    print(f"      {timestamp}: {side} {amount:.4f} {symbol} @ ${price:.2f}")
        
        # Overall statistics
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status IN ('completed_paper', 'simulated')")
        total_trades = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paper_trading_snapshots")
        total_snapshots = cursor.fetchone()[0]
        
        print(f"\n📈 Total Statistics:")
        print(f"   Total paper trades: {total_trades}")
        print(f"   Total snapshots: {total_snapshots}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    print("🎮 Paper Trading Reset Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            show_paper_trading_stats()
        elif sys.argv[1] == "reset":
            if len(sys.argv) > 2:
                user_id = int(sys.argv[2])
                reset_paper_trading(user_id)
            else:
                reset_paper_trading()
        else:
            print("Usage:")
            print("  python reset_paper_trading.py stats          - Show statistics")
            print("  python reset_paper_trading.py reset          - Reset all users")
            print("  python reset_paper_trading.py reset <user_id> - Reset specific user")
    else:
        print("\n1. Show current statistics")
        print("2. Reset paper trading data")
        choice = input("\nEnter choice (1 or 2): ")
        
        if choice == "1":
            show_paper_trading_stats()
        elif choice == "2":
            user_input = input("\nEnter user ID (or press Enter for all users): ")
            if user_input.strip():
                user_id = int(user_input)
                reset_paper_trading(user_id)
            else:
                reset_paper_trading()
        else:
            print("Invalid choice")
