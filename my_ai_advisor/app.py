# app.py
import streamlit as st
import requests
import json
import uuid # Used to generate a unique session ID
import google.generativeai as genai

# --- Page Configuration ---
st.set_page_config(
    page_title="Your Personal AI Financial Advisor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; }
    .st-emotion-cache-1g6goon { /* Metric styling */
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 15px;
        background-color: #FFFFFF;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


# --- Core Functions ---

@st.cache_data(ttl=300) # Cache the data for 5 minutes
def get_financial_data(persona_phone_number):
    """
    Connects to the mock server using the proven auth flow, fetches all financial
    data for a persona, and returns it as a single dictionary.
    """
    session = requests.Session()
    session_id = f"mcp-session-{uuid.uuid4()}"
    base_url = "http://localhost:8080"
    stream_url = f"{base_url}/mcp/stream"
    login_url = f"{base_url}/login"
    
    headers = {
        "Content-Type": "application/json",
        "Mcp-Session-Id": session_id
    }

    # A list of all the tools (data types) we want to fetch from the server.
    tools_to_fetch = [
        "fetch_net_worth",
        "fetch_credit_report",
        "fetch_epf_details",
        "fetch_mf_transactions"
    ]

    try:
        # --- Step 1: Initial API call to start the login process ---
        initial_payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tools_to_fetch[0], "arguments": {}}}
        initial_response = session.post(stream_url, headers=headers, json=initial_payload)
        
        if initial_response.status_code != 200:
            st.error(f"Initial API call failed! Status: {initial_response.status_code}")
            return None

        # --- Step 2: Perform login ---
        login_data = {'sessionId': session_id, 'phoneNumber': persona_phone_number, 'passcode': '1234'}
        login_response = session.post(login_url, data=login_data)
        
        if login_response.status_code != 200:
            st.error(f"Login failed! Status: {login_response.status_code}")
            return None

        # --- Step 3: Fetch data from all tools now that we are logged in ---
        full_financial_profile = {}
        for tool_name in tools_to_fetch:
            payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool_name, "arguments": {}}}
            data_response = session.post(stream_url, headers=headers, json=payload)
            
            if data_response.status_code == 200:
                # Correctly parse the doubly-nested JSON response
                response_data = data_response.json()
                content_text = response_data.get('result', {}).get('content', [{}])[0].get('text', '{}')
                full_financial_profile[tool_name] = json.loads(content_text)
            else:
                full_financial_profile[tool_name] = {"error": f"Failed to fetch {tool_name}"}
        
        return full_financial_profile

    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the Fi Mock Server. Is it running?")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None


def get_ai_insights(api_key, user_question, financial_data, persona_name):
    """Sends comprehensive data to Gemini for advanced financial analysis."""
    if not financial_data:
        return "Could not get AI insights due to missing financial data."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        full_prompt = f"""
        You are "Fi-nancial Advisor", a top-tier AI financial analyst. Your analysis must be sharp, data-driven, and highly personalized to the user's persona.

        **USER PERSONA:** You are advising a **{persona_name}**. All your advice must be tailored to this context.

        **AVAILABLE FINANCIAL DATA (This is a comprehensive JSON with multiple data points like net worth, credit score etc.):**
        ```json
        {json.dumps(financial_data, indent=2)}
        ```

        **YOUR TASK:**
        Based on the user's question and their COMPLETE financial data, perform one of the following analytical tasks. Always state your assumptions clearly.

        **1. For General Questions (e.g., "How is my net worth growing?"):**
           - Analyze the trends in assets and liabilities from the `fetch_net_worth` data.
           - Cross-reference with their credit score from the `fetch_credit_report` data if relevant.
           - Provide a summary and suggest 2-3 concrete actions for improvement based on their persona.

        **2. For Loan Affordability Questions (e.g., "Can I afford a ₹50L home loan?"):**
           - Use their `fetch_credit_report.creditScore` to determine their creditworthiness. A score below 650 is poor.
           - Calculate the estimated monthly EMI (assume 8.5% rate, 20 years).
           - Conclude with a clear "Yes," "No," or "It might be a stretch," and explain why, considering their existing debts (from `fetch_net_worth.netWorthResponse.liabilityValues`) and credit score.

        **3. For Future Wealth Projections (e.g., "How much money will I have at 40?"):**
           - Assume a current age of 28 if not provided.
           - Use the `fetch_net_worth.netWorthResponse.totalAssets.units` value as the present value (PV).
           - Assume a conservative blended rate of return of 11% per year.
           - Use the future value formula: FV = PV * (1 + r)^t.
           - Present the final projected amount and state your assumptions.
        
        ---
        **USER'S QUESTION:** "{user_question}"
        ---

        Now, provide your expert, data-driven analysis based on the rules above. Structure your response clearly using Markdown.
        """
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"An error occurred with the AI model: {e}"

# --- Main Application UI ---
st.title("🤖 Your Personal AI Financial Advisor")

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input("Enter your Google AI API Key:", type="password", key="api_key")
    st.divider()
    
    persona_options = {
    "No Assets (Only Savings Account)": "1111111111",
    "All Assets (Large MF Portfolio - 9 funds)": "2222222222",
    "All Assets (Small MF Portfolio - 1 fund)": "3333333333",
    "All Assets + EPF with 2 UAN + 3 Banks": "4444444444",
    "All Assets Except Credit Score": "5555555555",
    "No Bank Accounts (Large MF Portfolio)": "6666666666",
    "Debt-Heavy Low Performer": "7777777777",
    "SIP Samurai (Disciplined Investor)": "8888888888",
    "Fixed Income Fanatic": "9999999999",
    "Precious Metal Believer": "1010101010",
    "Dormant EPF Earner": "1212121212",
    "Salary Sinkhole (High Spender)": "1414141414",
    "Balanced Growth Tracker": "1313131313",
    "Starter Saver (New Investor)": "2020202020",
    "Ghost Portfolio (Inactive User)": "1515151515",
    "Early Retirement Dreamer": "1616161616",
    "The Swinger (Short-Term Trader)": "1717171717",
    "Passive Contributor (No Income)": "1818181818",
    "Section 80C Strategist (Tax Planner)": "1919191919",
    "Dual Income Dynamo (Freelancer + Salary)": "2121212121",
    "Sudden Wealth Receiver": "2222222222",
    "Overseas Optimizer (NRI)": "2323232323",
    "Mattress Money Mindset (FD Lover)": "2424242424",
    "Live-for-Today (High Income, High Spend)": "2525252525"
}

    selected_persona_name = st.selectbox("Choose a user profile to analyze:", options=list(persona_options.keys()))

# --- Main Logic ---
if not api_key_input:
    st.warning("Please enter your Google AI API Key in the sidebar to begin.")
else:
    # Fetch data for the selected persona
    financial_data = get_financial_data(persona_options[selected_persona_name])
    
    if financial_data:
        # Display the financial snapshot in the sidebar AFTER data is fetched
        with st.sidebar:
            st.divider()
            st.header("Financial Snapshot")
            
            # Safely extract and display metrics
            net_worth_data = financial_data.get("fetch_net_worth", {}).get("netWorthResponse", {})
            net_worth = int(net_worth_data.get("totalNetWorthValue", {}).get("units", 0))
            total_assets = int(net_worth_data.get("totalAssets", {}).get("units", 0))
            total_liabilities = int(net_worth_data.get("totalLiabilities", {}).get("units", 0))
            
            st.metric(label="Net Worth", value=f"₹{net_worth:,}")
            st.metric(label="Total Assets", value=f"₹{total_assets:,}")
            st.metric(label="Total Liabilities", value=f"₹{total_liabilities:,}")

        # --- Main Chat Interface ---
        # Initialize or reset chat history when persona changes
        if "messages" not in st.session_state or st.session_state.get("current_persona") != selected_persona_name:
            st.session_state.current_persona = selected_persona_name
            st.session_state.messages = [{"role": "assistant", "content": f"Hello! I've loaded the financial snapshot for the **{selected_persona_name}**. How can I assist you today?"}]
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Get user input
        if user_prompt := st.chat_input(f"Ask a question for the {selected_persona_name}..."):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("🧠 Performing advanced analysis..."):
                    ai_response = get_ai_insights(
                        api_key=api_key_input,
                        user_question=user_prompt,
                        financial_data=financial_data,
                        persona_name=selected_persona_name
                    )
                    st.markdown(ai_response)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()
    else:
        # This message shows if the API key is in, but data fetching failed.
        st.error("Could not load financial data. Please ensure the mock server is running and accessible.")