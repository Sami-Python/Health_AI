import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"

def verify_api_security():
    print("Verifying API Security Layers")
    print(f"Target: {BASE_URL}")

    # 1. Check Public Endpoint (Should be Accessible)
    print("\n[1] Testing Public Endpoint (GET /)")
    try:
        res = requests.get(f"{BASE_URL}/")
        if res.status_code == 200:
             print("   Success: Public endpoint accessible.")
        else:
             print(f"   Error: Public endpoint returned {res.status_code}")
    except Exception as e:
        print(f"   Connection Error: {e}")
        print("   Is the backend running? (docker-compose up or python main.py)")
        return

    # 2. Check Protected Endpoint WITHOUT Token
    print("\n[2] Testing Protected Endpoint (GET /goals) WITHOUT Token")
    res = requests.get(f"{BASE_URL}/goals")
    if res.status_code == 401: # or 403 depending on implementation
        print("   Success: Request rejected as Unauthorized (401).")
    else:
        print(f"   FAILURE: Request accepted or wrong status! Code: {res.status_code}")

    # 3. Check Protected Endpoint WITH INVALID Token
    print("\n[3] Testing Protected Endpoint (GET /goals) WITH INVALID Token")
    headers = {"Authorization": "Bearer invalid_token_123"}
    res = requests.get(f"{BASE_URL}/goals", headers=headers)
    if res.status_code == 401:
        print("   Success: Invalid token rejected (401).")
    else:
        print(f"   FAILURE: Invalid token accepted! Code: {res.status_code}")

if __name__ == "__main__":
    verify_api_security()
