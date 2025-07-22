# test_connection.py
import requests
import json
import uuid # Used to generate a unique session ID

# --- Configuration ---
PERSONA_PHONE_NUMBER = "7777777777" # The "Debt-Heavy Low Performer"
BASE_URL = "http://localhost:8080"
STREAM_URL = f"{BASE_URL}/mcp/stream"
LOGIN_URL = f"{BASE_URL}/login"

# The JSON payload to ask the server for the net worth details.
JSON_RPC_PAYLOAD = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {"name": "fetch_net_worth", "arguments": {}}
}

def run_test():
    """Connects to the server with the correct auth flow and fetches data."""
    print("--- Starting Connection Test ---")
    session = requests.Session() # Use a session to handle cookies automatically

    try:
        # --- Step 1: Generate our own unique session ID ---
        session_id = f"mcp-session-{uuid.uuid4()}"
        print(f"\n[Step 1] Generated a unique Session ID: {session_id}")
        
        headers = {
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }

        # --- Step 2: Initial "knock-on-the-door" to get a login_url ---
        print("\n[Step 2] Making initial API call with our new Session ID...")
        initial_response = session.post(STREAM_URL, headers=headers, json=JSON_RPC_PAYLOAD)
        
        if initial_response.status_code != 200:
             print(f"❌ ERROR: Initial API call failed! Status: {initial_response.status_code}")
             print(f"Response Body: {initial_response.text}")
             return

        # --- THIS IS THE CORRECTED LOGIC ---
        # The login_url is nested inside a stringified JSON. We need to parse it twice.
        try:
            response_data = initial_response.json()
            content_text = response_data['result']['content'][0]['text']
            # Now, parse the inner JSON string
            inner_data = json.loads(content_text)
            login_url = inner_data.get("login_url")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"❌ ERROR: Could not parse the server's response to find the login_url. Error: {e}")
            print(f"Full Response: {initial_response.text}")
            return

        if not login_url:
            print("❌ ERROR: Did not receive a login_url from the server.")
            print(f"Response: {initial_response.text}")
            return
        
        print(f"✅ Received login URL from server.")

        # --- Step 3: Perform the actual login with the session ID ---
        print("\n[Step 3] Performing login with Session ID and Phone Number...")
        
        login_data = {
            'sessionId': session_id,
            'phoneNumber': PERSONA_PHONE_NUMBER,
            'passcode': '1234'
        }
        login_response = session.post(LOGIN_URL, data=login_data)

        if login_response.status_code != 200:
            print(f"❌ Login failed! Status: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        print("✅ Login successful!")

        # --- Step 4: Fetch the financial data again, now authenticated ---
        print("\n[Step 4] Fetching financial data with authenticated session...")
        data_response = session.post(STREAM_URL, headers=headers, json=JSON_RPC_PAYLOAD)

        if data_response.status_code == 200:
            print("✅ Data fetched successfully!")
            financial_data = data_response.json().get("result", {})
            print("\n--- Financial Data Received ---")
            print(json.dumps(financial_data, indent=2))
        else:
            print(f"❌ Failed to fetch data! Status: {data_response.status_code}")
            print(f"Response: {data_response.text}")

    except requests.exceptions.ConnectionError:
        print("\n❌ CRITICAL ERROR: Could not connect to the server.")
        print("Please make sure your Go server is running in the other terminal.")
        return
    except requests.exceptions.JSONDecodeError as e:
        print(f"\n❌ CRITICAL ERROR: Failed to decode JSON from the server response. Error: {e}")
        print("This can happen if the server returns an HTML error page instead of JSON.")
        return


    print("\n--- Test Complete ---")


if __name__ == "__main__":
    run_test()
