#!/usr/bin/env python
import os
import requests
import sys
import time

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
DEMO_EMAIL = "demo@opspilot.ai"
DEMO_PASSWORD = "demo"

def health_check():
    """
    Waits for the backend to become available.
    """
    start_time = time.time()
    while time.time() - start_time < 30: # 30 second timeout
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("Backend is healthy.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("Health check failed: Backend did not become available in time.")
    return False

def test_login():
    """
    Attempts to log in with demo credentials and validates the token.
    """
    if not health_check():
        return False

    print(f"Attempting login for {DEMO_EMAIL} at {BASE_URL}...")
    
    # Step 1: Log in and get tokens
    login_payload = {
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD
    }
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        response.raise_for_status()
        tokens = response.json()
        access_token = tokens.get("access_token")
        if not access_token:
            print("Login failed: No access token in response.")
            return False
        print("Login successful, token received.")
    except requests.exceptions.RequestException as e:
        print(f"Login request failed: {e}")
        return False

    # Step 2: Use the token to access a protected endpoint
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        response.raise_for_status()
        user_info = response.json()
        if user_info.get("email") == DEMO_EMAIL:
            print("Token validation successful.")
            return True
        else:
            print("Token validation failed: User email mismatch.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Protected endpoint request failed: {e}")
        return False

if __name__ == "__main__":
    if test_login():
        print("Login OK")
        sys.exit(0)
    else:
        print("Login failed")
        sys.exit(1)
