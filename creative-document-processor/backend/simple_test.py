#!/usr/bin/env python3
"""
A simple test script for the query endpoint using curl.
"""
import subprocess
import json
import time

def main():
    """
    Test the query endpoint.
    """
    print("Testing query endpoint using curl...")
    
    # Define request data
    data = {
        "kb": "resumes",
        "prompt": "what skills does the candidate have?"
    }
    
    # Convert to JSON string
    data_json = json.dumps(data)
    
    # Prepare curl command
    cmd = [
        "curl",
        "-X", "POST",
        "http://localhost:8000/query/",
        "-H", "Content-Type: application/json",
        "-H", "Accept: text/event-stream",
        "-d", data_json,
        "-v"  # Verbose output
    ]
    
    # Run curl command
    print("Running command:", " ".join(cmd))
    
    # Use subprocess to run the command and capture output
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Read and print stdout in real-time
        print("\nResponse:")
        print("-" * 50)
        
        # Process stdout
        for line in process.stdout:
            print(line.strip())
            
        # Get return code
        return_code = process.wait()
        print(f"Command exited with code: {return_code}")
        
    except Exception as e:
        print(f"Error executing curl: {str(e)}")
    
if __name__ == "__main__":
    main() 