"""
Force BUY/SELL Test - Lower thresholds and test multiple symbols
This will help you see actual BUY/SELL actions
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    response = requests.post(f"{BASE_URL}/api/auth/login", data={"username": USERNAME, "password": PASSWORD})
    return response.json()["access_token"] if response.status_code == 200 else None

def main():
    token = login()
    if not token:
        print("Login failed!")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Update config with very low threshold
    print("Setting minimum confidence to 0.40 (40%) to allow more trades...")
    config_update = {
        "min_confidence": 0.40,
        "paper_trading": True,
        "budget": 1000
    }
    
    response = requests.put(f"{BASE_URL}/api/settings/bot-config", headers=headers, json=config_update)
    print(f"Config updated: {response.status_code}\n")
    
    # Test multiple symbols
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT", "ADA/USDT", "DOGE/USDT"]
    
    buy_found = False
    sell_found = False
    
    for symbol in symbols:
        if buy_found and sell_found:
            break
            
        print(f"\n{'='*60}")
        print(f"Testing {symbol}")
        print(f"{'='*60}")
        
        # Update symbol
        requests.put(f"{BASE_URL}/api/settings/bot-config", headers=headers, json={"symbol": symbol})
        
        # Run Gods Hand
        response = requests.post(f"{BASE_URL}/api/bot/gods-hand/start?continuous=false", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            action = result.get('action', 'HOLD')
            confidence = result.get('confidence', 0)
            message = result.get('message', '')
            
            print(f"\n🎯 Action: {action}")
            print(f"📊 Confidence: {confidence:.0%}")
            print(f"💬 Message: {message}")
            
            if action == 'BUY':
                print(f"\n✅ BUY ACTION FOUND for {symbol}!")
                buy_found = True
            elif action == 'SELL':
                print(f"\n✅ SELL ACTION FOUND for {symbol}!")
                sell_found = True
        else:
            print(f"Error: {response.text}")
        
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  BUY action found: {'✅' if buy_found else '❌'}")
    print(f"  SELL action found: {'✅' if sell_found else '❌'}")
    print(f"{'='*60}")
    
    # Restore confidence
    print("\nRestoring minimum confidence to 0.70 (70%)...")
    requests.put(f"{BASE_URL}/api/settings/bot-config", headers=headers, json={"min_confidence": 0.70})

if __name__ == "__main__":
    main()
