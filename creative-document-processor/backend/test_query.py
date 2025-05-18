#!/usr/bin/env python3
import requests
import json
import sys
import time
import signal
import os

def signal_handler(sig, frame):
    print("\nInterrupted by user, exiting...")
    sys.exit(0)

# Set up signal handler for clean exit with Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

def test_query(kb, prompt, timeout=120):
    """Test query with a longer timeout and better debug info"""
    
    # Set API key directly
    api_key = "AIzaSyD1wnZAgNPnes4CmKyfc6RxQRFlGCWU0ZY"
    os.environ["GOOGLE_API_KEY"] = api_key
    print(f"✓ Setting API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Make the API key available in the headers
    url = "http://localhost:8000/query/"
    headers = {
        "Content-Type": "application/json",
        "X-Google-API-Key": api_key  # Add API key to headers in case server checks there
    }
    data = {"kb": kb, "prompt": prompt}
    
    print(f"\n📤 Sending query to {kb}:")
    print(f"   Prompt: {prompt}")
    print(f"   Timeout: {timeout} seconds\n")
    
    try:
        start_time = time.time()
        print("⏳ Making request, waiting for response...")
        
        with requests.post(url, headers=headers, json=data, stream=True, timeout=timeout) as response:
            if response.status_code != 200:
                print(f"❌ Error: Status code {response.status_code}")
                print(response.text)
                return
            
            print(f"✓ Connection established with status code: {response.status_code}")
            print(f"✓ Response headers: {response.headers}")
            print("\n📥 Processing SSE stream...\n")
            
            # Track if we received anything beyond the initial processing message
            received_content = False
            buffer = ""
            line_count = 0
            
            print("=" * 50)
            for line in response.iter_lines():
                if line:
                    line_count += 1
                    decoded_line = line.decode('utf-8')
                    
                    # Print raw line
                    print(f"📌 Line {line_count}: {decoded_line}")
                    
                    # Parse SSE format
                    if decoded_line.startswith('data: '):
                        data_content = decoded_line[6:]
                        
                        # Skip the initial "Processing query..." message
                        if data_content != "Processing query...":
                            received_content = True
                        
                        try:
                            # Try to parse as JSON
                            json_data = json.loads(data_content)
                            print(f"📋 JSON: {json_data}")
                            
                            # Check if this is a final response
                            if isinstance(json_data, dict) and json_data.get("status") == "complete":
                                print("\n✅ Received complete response!")
                                if "answer" in json_data:
                                    print(f"\n📝 Answer: {json_data['answer']}")
                                if "sources" in json_data:
                                    print(f"\n📚 Sources: {json_data['sources']}")
                            
                        except json.JSONDecodeError:
                            # Handle plain text
                            print(f"📄 Text: {data_content}")
                        
                        buffer += data_content + "\n"
                        
                    # Print a separator for readability
                    print("-" * 50)
            
            print("=" * 50)
            
            elapsed_time = time.time() - start_time
            print(f"\n⏱️ Stream ended after {elapsed_time:.2f} seconds")
            
            # Print summary information
            if not received_content:
                print("⚠️ Only received initial 'Processing query...' message, no actual content!")
            else:
                print("✓ Received response content beyond the initial processing message")
            
            print(f"\n📊 Summary:")
            print(f"  - Total lines received: {line_count}")
            print(f"  - Response buffer size: {len(buffer)} characters")
            
            if buffer:
                print("\n📜 Complete response buffer:")
                print("-" * 50)
                print(buffer)
                print("-" * 50)
                
                # Save response to file for later analysis
                with open("query_response.txt", "w") as f:
                    f.write(buffer)
                print("\n💾 Response saved to query_response.txt")
            else:
                print("\n❌ No content received in the response")
        
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Use command line args if provided, otherwise use defaults
    kb = sys.argv[1] if len(sys.argv) > 1 else "recipes"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "What are the main ingredients in this recipe?"
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    
    test_query(kb, prompt, timeout) 