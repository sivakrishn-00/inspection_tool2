import requests
import json

# ==========================================
# Inspection System API Data Export Example
# ==========================================

# 1. Define the base URL where the inspection system is running
# If running locally, it's usually http://127.0.0.1:8000
BASE_URL = "http://127.0.0.1:8000"

# 2. Add your generated API Key here
# You can generate this by going to Settings -> API Management as a Superuser
API_KEY = "zmsMm22BZcsKvLvf0O7XhZ5-Q9RI8H82e7xw66tTIOE"

# 3. Define the endpoint URL
ENDPOINT = f"{BASE_URL}/api/v1/export/"

def fetch_inspection_data():
    """
    Fetches the latest inspection and complaint data from the server.
    Uses the 'Authorization' header to securely pass the API Key.
    """
    print(f"Attempting to fetch data from {ENDPOINT}...")
    
    # 📝 METHOD: Passing the API Key via Headers
    # This is the recommended secure way to authenticate
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Accept": "application/json"
    }

    try:
        # Make the GET request
        response = requests.get(ENDPOINT, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            print("âœ… Data fetched successfully!")
            
            # Parse the JSON data
            data = response.json()
            
            # Print the data beautifully
            print(json.dumps(data, indent=4))
            return data
            
        elif response.status_code == 401:
            print("âŒ Authentication Error (401 Unauthorized)")
            print("Please check that your API_KEY is correct and active.")
            print(f"Response: {response.text}")
            
        else:
            print(f"âŒ Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"âŒ Connection Error: Could not connect to {BASE_URL}")
        print("Is the Django development server currently running?")
    except Exception as e:
        print(f"âŒ An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    fetch_inspection_data()
