#!/usr/bin/env python3
import requests
import json
import sys
import time

def query_with_sse(kb, prompt, timeout=30):
    """Query the knowledge base with SSE for streaming response."""
    url = "http://localhost:8000/query/"
    headers = {"Content-Type": "application/json"}
    data = {"kb": kb, "prompt": prompt}
    
    print(f"Sending query to {kb}: {prompt}")
    print(f"Using timeout of {timeout} seconds")
    
    try:
        # Make request with stream=True to get SSE
        with requests.post(url, headers=headers, json=data, stream=True, timeout=timeout) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                return
            
            print(f"Connection established with status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print("Processing SSE stream...")
            
            # Process the SSE stream
            buffer = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    # Print each line coming in
                    print(f"Raw line: {decoded_line}")
                    
                    # Parse SSE format and accumulate the data
                    if decoded_line.startswith('data: '):
                        data_content = decoded_line[6:]
                        buffer += data_content + "\n"
                        
                        # Try to parse as JSON
                        try:
                            json_data = json.loads(data_content)
                            print(f"Parsed JSON: {json_data}")
                        except json.JSONDecodeError:
                            print(f"Text content: {data_content}")
            
            # Print the final accumulated response
            if buffer:
                print("\nComplete response:")
                print(buffer)
            else:
                print("\nNo content received in the response.")
    
    except requests.exceptions.Timeout:
        print(f"Request timed out after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Use command line args if provided, otherwise use defaults
    kb = sys.argv[1] if len(sys.argv) > 1 else "recipes"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "What are the main ingredients in this recipe?"
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    query_with_sse(kb, prompt, timeout) 