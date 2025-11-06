"""
Test script to force BUY/SELL actions for testing
This temporarily lowers confidence thresholds to see actual trades
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# Login credentials
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Login and get token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✓ Logged in as {USERNAME}")
        return token
    else:
        print(f"✗ Login failed: {response.text}")
        return None

def get_current_config(token):
    """Get current bot configuration"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/settings/bot-config", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def update_config(token, updates):
    """Update bot configuration"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{BASE_URL}/api/settings/bot-config",
        headers=headers,
        json=updates
    )
    if response.status_code == 200:
        print(f"✓ Config updated: {updates}")
        return response.json()
    else:
        print(f"✗ Config update failed: {response.text}")
        return None

def run_gods_hand(token):
    """Run Gods Hand once"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/bot/gods-hand/start?continuous=false&interval_seconds=60",
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*60}")
        print(f"Gods Hand Result:")
        print(f"{'='*60}")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"✗ Gods Hand failed: {response.text}")
        return None

def main():
    print("Testing Gods Hand with Lower Confidence Threshold")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        return
    
    # Get current config
    print("\n1. Getting current configuration...")
    original_config = get_current_config(token)
    if original_config:
        print(f"   Current Symbol: {original_config.get('symbol')}")
        print(f"   Current Min Confidence: {original_config.get('min_confidence', 0.7)}")
        print(f"   Paper Trading: {original_config.get('paper_trading', True)}")
    
    # Lower the minimum confidence to allow more trades
    print("\n2. Lowering minimum confidence to 0.50 (50%)...")
    update_config(token, {
        "min_confidence": 0.50,  # Lower threshold
        "paper_trading": True,    # Keep paper trading for safety
        "symbol": "XRP/USDT"      # Test with XRP
    })
    
    # Test different symbols to find one that generates action
    test_symbols = ["XRP/USDT", "BTC/USDT", "ETH/USDT", "SOL/USDT"]
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"Testing with {symbol}")
        print(f"{'='*60}")
        
        # Update symbol
        update_config(token, {"symbol": symbol})
        
        # Run Gods Hand
        result = run_gods_hand(token)
        
        if result:
            action = result.get('action') or result.get('recommendation', {}).get('action', 'HOLD')
            confidence = result.get('confidence') or result.get('recommendation', {}).get('confidence', 0)
            
            print(f"\n🎯 Action: {action}")
            print(f"📊 Confidence: {confidence:.0%}")
            
            if action in ['BUY', 'SELL']:
                print(f"\n✅ SUCCESS! Found {action} action for {symbol}")
                break
        
        time.sleep(2)  # Wait between tests
    
    # Restore original settings
    print(f"\n{'='*60}")
    print("Restoring original configuration...")
    if original_config:
        update_config(token, {
            "min_confidence": original_config.get('min_confidence', 0.7),
            "symbol": original_config.get('symbol', 'BTC/USDT')
        })
    
    print("\nTest complete!")

if __name__ == "__main__":
    main()
