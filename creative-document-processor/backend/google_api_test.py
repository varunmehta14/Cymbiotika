import os
import requests
import json
import time

def check_google_api_key():
    # Get API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    
    if not api_key:
        print("❌ No Google API key found in environment variables")
        return False
    
    # Print partial key for verification
    print(f"Found API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Test the key with a simple request to Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": "Hello, what's the weather like today?"}]}]
    }
    
    try:
        print("Testing API key with simple request to Gemini API...")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print(response.text)
            print("✅ API key is valid!")
            return True
        else:
            print(f"❌ API key is invalid. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing API key: {str(e)}")
        return False

def test_query_endpoint():
    print("\nTesting query endpoint with streaming response...")
    url = "http://localhost:8000/query/"
    headers = {"Content-Type": "application/json"}
    data = {"kb": "recipes", "prompt": "What are the main ingredients in this recipe?"}
    
    try:
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code != 200:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            return
        
        print("Connection established, receiving stream:")
        print("-" * 50)
        
        # Process the streaming response
        buffer = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"RAW: {decoded_line}")
                
                # Parse SSE format
                if decoded_line.startswith('data: '):
                    data_content = decoded_line[6:]
                    try:
                        # Try to parse as JSON
                        json_data = json.loads(data_content)
                        print(f"JSON: {json_data}")
                    except json.JSONDecodeError:
                        # Handle plain text
                        print(f"TEXT: {data_content}")
                    
                    buffer += data_content + "\n"
        
        print("-" * 50)
        print("Stream ended")
        
    except Exception as e:
        print(f"❌ Error connecting to endpoint: {str(e)}")

if __name__ == "__main__":
    # Check if API key is valid
    api_key_valid = check_google_api_key()
    
    # Test the query endpoint
    test_query_endpoint() 