import requests, json, sys
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
    # continuous=false to run once
    r = requests.post(
        f"{BASE_URL}/api/bot/gods-hand/start",
        headers={"Authorization": f"Bearer {token}"},
        params={"continuous": "false", "interval_seconds": "30"},
    )
    r.raise_for_status()
    return r.json()


def get_logs(token, category=None, limit=20):
    params = {"limit": str(limit)}
    if category:
        params["category"] = category
    r = requests.get(f"{BASE_URL}/api/logs", headers={"Authorization": f"Bearer {token}"}, params=params)
    r.raise_for_status()
    return r.json()


def main():
    token = login()
    cfg = get_config(token)
    print("CURRENT_CONFIG:")
    print(json.dumps(cfg, indent=2))

    patch = {
        "gods_hand_enabled": True,
        "paper_trading": True,
        "symbol": "SOL/USDT",
        "min_confidence": 0.55,
        "entry_step_percent": 30.0,
        "exit_step_percent": 30.0,
    }
    new_cfg = update_config(token, patch)
    print("UPDATED_CONFIG:")
    print(json.dumps(new_cfg, indent=2))

    results = []
    for i in range(3):
        result = start_gods_hand_once(token)
        results.append(result)
    print("GODS_HAND_RESULTS:")
    print(json.dumps(results, indent=2))

    think = get_logs(token, category="ai_thinking", limit=5)
    act = get_logs(token, category="ai_action", limit=5)

    print("LATEST_THINKING:")
    print(json.dumps(think.get("logs"), indent=2))
    print("LATEST_ACTIONS:")
    print(json.dumps(act.get("logs"), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("TEST_FAIL:", e)
        sys.exit(1)
