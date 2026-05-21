"""Test Flask app API endpoints"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_chat_api():
    print("\n" + "="*60)
    print("Testing /api/chat endpoint")
    print("="*60)
    
    payload = {
        "question": "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
        "emergency_mode": "normal"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"\nResponse Text:\n{data.get('response', 'N/A')}")
            print(f"\nMode: {data.get('mode', 'N/A')}")
            print(f"Audio URL: {data.get('audio_url', 'N/A')}")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Flask app is not running")
        print("Please start the app with: python app.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chat_api()
