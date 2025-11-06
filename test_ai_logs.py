import requests, sys, json, time

BASE_URL = "http://localhost:8000"
USER = "Admin"
PASS = "K@nph0ng69"

def login():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"username": USER, "password": PASS})
    r.raise_for_status()
    return r.json()["access_token"]


def get_logs(token, category=None, limit=50):
    params = {"limit": str(limit)}
    if category:
        params["category"] = category
    r = requests.get(f"{BASE_URL}/api/logs", headers={"Authorization": f"Bearer {token}"}, params=params)
    r.raise_for_status()
    return r.json()


def get_ai_comparisons(token, limit=50):
    r = requests.get(f"{BASE_URL}/api/logs/ai-actions", headers={"Authorization": f"Bearer {token}"}, params={"limit": str(limit)})
    r.raise_for_status()
    return r.json()


def main():
    try:
        token = login()
    except Exception as e:
        print(f"LOGIN_FAIL: {e}")
        sys.exit(1)

    try:
        thinking = get_logs(token, category="ai_thinking", limit=50)
        actions = get_logs(token, category="ai_action", limit=50)
        errors = get_logs(token, category="error", limit=20)
        bots = get_logs(token, category="bot", limit=20)
        comps = get_ai_comparisons(token, limit=50)
    except Exception as e:
        print(f"FETCH_FAIL: {e}")
        sys.exit(2)

    print("SUMMARY")
    print(json.dumps({
        "thinking_total": thinking.get("total"),
        "actions_total": actions.get("total"),
        "errors_total": errors.get("total"),
        "bot_total": bots.get("total"),
        "comparisons_total": comps.get("total"),
    }, indent=2))

    # Quick quality checks
    latest_think = (thinking.get("logs") or [])[:5]
    latest_act = (actions.get("logs") or [])[:5]

    def brief(log):
        return {
            "ts": log.get("timestamp"),
            "symbol": log.get("symbol"),
            "rec": log.get("ai_recommendation"),
            "conf": log.get("ai_confidence"),
            "msg": log.get("message"),
            "exec": log.get("ai_executed"),
            "reason": log.get("execution_reason"),
        }

    print("LATEST_THINKING")
    print(json.dumps([brief(x) for x in latest_think], indent=2))

    print("LATEST_ACTIONS")
    print(json.dumps([brief(x) for x in latest_act], indent=2))

    print("ERRORS_SAMPLE")
    print(json.dumps((errors.get("logs") or [])[:3], indent=2))

    print("BOT_LOGS_SAMPLE")
    print(json.dumps((bots.get("logs") or [])[:3], indent=2))

    print("COMPARISONS_SAMPLE")
    comps_sample = (comps.get("comparisons") or [])[:5]
    print(json.dumps(comps_sample, indent=2))

if __name__ == "__main__":
    main()
