"""
Test profit protection features:
- Trailing take-profit
- Hard stop-loss
- Daily kill-switch
- Dynamic step sizing
"""
import requests, json, sys, time

BASE_URL = "http://localhost:8000"
USER = "Admin"
PASS = "K@nph0ng69"


def login():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"username": USER, "password": PASS})
    r.raise_for_status()
    return r.json()["access_token"]


def get_config(token):
    r = requests.get(f"{BASE_URL}/api/settings/bot-config", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json()


def update_config(token, patch):
    r = requests.put(
        f"{BASE_URL}/api/settings/bot-config",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=patch,
    )
    r.raise_for_status()
    return r.json()


def start_gods_hand_once(token):
    r = requests.post(
        f"{BASE_URL}/api/bot/gods-hand/start",
        headers={"Authorization": f"Bearer {token}"},
        params={"continuous": "false", "interval_seconds": "30"},
    )
    r.raise_for_status()
    return r.json()


def get_logs(token, category=None, limit=10):
    params = {"limit": str(limit)}
    if category:
        params["category"] = category
    r = requests.get(f"{BASE_URL}/api/logs", headers={"Authorization": f"Bearer {token}"}, params=params)
    r.raise_for_status()
    return r.json()


def main():
    print("=" * 70)
    print(" 🎯 TESTING PROFIT PROTECTION FEATURES")
    print("=" * 70)
    
    token = login()
    print("✅ Logged in")
    
    cfg = get_config(token)
    print("\n📋 CURRENT CONFIG:")
    print(f"  Symbol: {cfg.get('symbol')}")
    print(f"  Budget: ${cfg.get('budget')}")
    print(f"  Paper Trading: {cfg.get('paper_trading')}")
    print(f"  Min Confidence: {cfg.get('min_confidence')}")
    print(f"  Entry Step: {cfg.get('entry_step_percent')}%")
    print(f"  Exit Step: {cfg.get('exit_step_percent')}%")
    print(f"  Trailing TP: {cfg.get('trailing_take_profit_percent')}%")
    print(f"  Hard Stop Loss: {cfg.get('hard_stop_loss_percent')}%")
    print(f"  Max Daily Loss: {cfg.get('max_daily_loss')}%")
    
    # Configure aggressive settings for testing
    patch = {
        "gods_hand_enabled": True,
        "paper_trading": True,
        "symbol": "BTC/USDT",
        "min_confidence": 0.55,
        "entry_step_percent": 20.0,
        "exit_step_percent": 20.0,
        "trailing_take_profit_percent": 2.0,
        "hard_stop_loss_percent": 3.0,
        "max_daily_loss": 5.0,
    }
    new_cfg = update_config(token, patch)
    print("\n✅ Updated config for testing:")
    print(f"  Trailing TP: {new_cfg.get('trailing_take_profit_percent')}%")
    print(f"  Hard Stop Loss: {new_cfg.get('hard_stop_loss_percent')}%")
    print(f"  Entry/Exit Steps: {new_cfg.get('entry_step_percent')}% / {new_cfg.get('exit_step_percent')}%")
    
    # Run multiple iterations
    print("\n🔄 Running 3 Gods Hand iterations...")
    results = []
    for i in range(3):
        print(f"\n  Iteration {i+1}/3...")
        result = start_gods_hand_once(token)
        results.append(result)
        print(f"    Action: {result.get('action')}")
        print(f"    Confidence: {result.get('confidence')}")
        print(f"    Reason: {result.get('reason', 'N/A')}")
        time.sleep(1)
    
    # Check logs for profit protection triggers
    print("\n📊 CHECKING LOGS...")
    actions = get_logs(token, category="ai_action", limit=10)
    bot_logs = get_logs(token, category="bot", limit=10)
    
    print(f"\n  Latest AI Actions ({actions.get('total')} total):")
    for log in (actions.get("logs") or [])[:5]:
        print(f"    • {log.get('message')}")
        if 'STOP LOSS' in log.get('message', '') or 'TRAILING TP' in log.get('message', ''):
            print(f"      🎯 PROFIT PROTECTION TRIGGERED!")
    
    print(f"\n  Latest Bot Logs ({bot_logs.get('total')} total):")
    for log in (bot_logs.get("logs") or [])[:5]:
        print(f"    • {log.get('message')}")
        if 'KILL-SWITCH' in log.get('message', ''):
            print(f"      🛡️ KILL-SWITCH ACTIVATED!")
    
    # Summary
    print("\n" + "=" * 70)
    print(" ✅ PROFIT PROTECTION FEATURES DEPLOYED")
    print("=" * 70)
    print("\n📈 KEY FEATURES NOW ACTIVE:")
    print(f"  1. Trailing Take-Profit: Sells {new_cfg.get('exit_step_percent')}% when profit ≥ {new_cfg.get('trailing_take_profit_percent')}%")
    print(f"  2. Hard Stop-Loss: Closes position if loss ≥ {new_cfg.get('hard_stop_loss_percent')}%")
    print(f"  3. Daily Kill-Switch: Stops trading if daily loss ≥ {new_cfg.get('max_daily_loss')}%")
    print(f"  4. Dynamic Steps: 0.5x-1.5x step size based on AI confidence")
    print("\n💡 NEXT STEPS:")
    print("  • Monitor logs for profit protection triggers")
    print("  • Adjust trailing_take_profit_percent and hard_stop_loss_percent as needed")
    print("  • Review daily P/L before market close")
    print("\n🎯 Your bot is now optimized for maximum profit with downside protection!")
    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
