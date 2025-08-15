#!/usr/bin/env python3
"""
Quick OpsPilot MVP Demo
Shows key features in action
"""

import requests
import json

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        print("✅ Backend Health:", response.json())
        return True
    except:
        print("❌ Backend not running")
        return False

def test_auth():
    """Test authentication system"""
    print("\n🔐 Testing Authentication...")
    
    # Login as analyst
    login_data = {"email": "analyst@demo.com", "password": "demo"}
    response = requests.post("http://localhost:8000/auth/login", json=login_data)
    
    if response.status_code == 200:
        tokens = response.json()
        print("✅ Analyst login successful")
        print(f"   Token: {tokens['access_token'][:30]}...")
        return tokens
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_protected_access(tokens):
    """Test protected endpoint access"""
    print("\n🛡️ Testing Protected Access...")
    
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Test accessing docs (should work with auth)
    response = requests.get("http://localhost:8000/docs", headers=headers)
    print(f"✅ Protected endpoint access: {response.status_code}")

def test_upload(tokens):
    """Test file upload functionality"""
    print("\n📁 Testing File Upload...")
    
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Create sample CSV
    csv_content = """trade_id,product_code,quantity,price
T001,ES,100,4500.25
T002,NQ,50,15000.75"""
    
    files = {"file": ("demo_trades.csv", csv_content, "text/csv")}
    response = requests.post("http://localhost:8000/upload", files=files, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ File upload successful")
        print(f"   Processed: {result.get('trades_count', 'N/A')} trades")
    else:
        print(f"❌ Upload failed: {response.status_code}")

def main():
    print("🚀 OpsPilot MVP Quick Demo")
    print("=" * 40)
    
    # Check if backend is running
    if not test_health():
        print("\n💡 To start backend:")
        print("   cd backend")
        print("   python -m uvicorn app.main:app --reload --port 8000")
        return
    
    # Test authentication
    tokens = test_auth()
    if not tokens:
        return
    
    # Test protected access
    test_protected_access(tokens)
    
    # Test file upload
    test_upload(tokens)
    
    print("\n🎉 Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ JWT Authentication")
    print("✅ Protected Endpoints") 
    print("✅ File Upload & Processing")
    print("✅ API Documentation at http://localhost:8000/docs")

if __name__ == "__main__":
    main()
