"""
Manual Trade Test - Force a BUY or SELL action
This script helps you see actual trade execution
"""
import requests
import json

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    return response.json()["access_token"] if response.status_code == 200 else None

def get_recommendation(token, symbol):
    """Get AI recommendation"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/ai/recommend",
        headers=headers,
        json={"symbol": symbol}
    )
    return response.json() if response.status_code == 200 else None

def execute_trade(token, symbol, side, quantity):
    """Execute a manual trade"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/trading/order",
        headers=headers,
        json={
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": "market"
        }
    )
    return response.json() if response.status_code == 200 else None

def main():
    print("Manual Trade Test")
    print("="*60)
    
    token = login()
    if not token:
        print("Login failed!")
        return
    
    print("✓ Logged in\n")
    
    # Test different symbols
    symbols = ["BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT"]
    
    for symbol in symbols:
        print(f"\n{symbol}")
        print("-"*40)
        
        rec = get_recommendation(token, symbol)
        if rec:
            action = rec.get('action', 'HOLD')
            confidence = rec.get('confidence', 0)
            reasoning = rec.get('reasoning', '')
            
            print(f"Action: {action}")
            print(f"Confidence: {confidence:.0%}")
            print(f"Reasoning: {reasoning}")
            
            if action in ['BUY', 'SELL']:
                print(f"\n🎯 Found {action} signal!")
                
                # Ask user if they want to execute
                choice = input(f"\nExecute this {action}? (y/n): ")
                if choice.lower() == 'y':
                    quantity = float(input("Enter quantity: "))
                    result = execute_trade(token, symbol, action, quantity)
                    if result:
                        print(f"\n✅ Trade executed!")
                        print(json.dumps(result, indent=2))
                    else:
                        print(f"\n✗ Trade failed")
                break

if __name__ == "__main__":
    main()
