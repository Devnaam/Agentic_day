import requests
import json
import uuid
import google.generativeai as genai
import streamlit as st

@st.cache_data(ttl=300)
def get_financial_data(persona_phone_number):
    session = requests.Session()
    session_id = f"mcp-session-{uuid.uuid4()}"
    base_url = "http://localhost:8080"
    stream_url = f"{base_url}/mcp/stream"
    login_url = f"{base_url}/login"

    headers = {
        "Content-Type": "application/json",
        "Mcp-Session-Id": session_id
    }

    tools_to_fetch = [
        "fetch_net_worth",
        "fetch_credit_report",
        "fetch_epf_details",
        "fetch_mf_transactions"
    ]

    try:
        initial_payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tools_to_fetch[0], "arguments": {}}}
        initial_response = session.post(stream_url, headers=headers, json=initial_payload)
        if initial_response.status_code != 200:
            st.error(f"Initial API call failed! Status: {initial_response.status_code}")
            return None

        login_data = {'sessionId': session_id, 'phoneNumber': persona_phone_number, 'passcode': '1234'}
        login_response = session.post(login_url, data=login_data)
        if login_response.status_code != 200:
            st.error(f"Login failed! Status: {login_response.status_code}")
            return None

        full_financial_profile = {}
        for tool_name in tools_to_fetch:
            payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool_name, "arguments": {}}}
            data_response = session.post(stream_url, headers=headers, json=payload)
            if data_response.status_code == 200:
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
    if not financial_data:
        return "Could not get AI insights due to missing financial data."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        full_prompt = f"""
        You are \"Fi-nancial Advisor\", a top-tier AI financial analyst. Your analysis must be sharp, data-driven, and highly personalized to the user's persona.

        **USER PERSONA:** You are advising a **{persona_name}**. All your advice must be tailored to this context.

        **AVAILABLE FINANCIAL DATA:**
        ```json
        {json.dumps(financial_data, indent=2)}
        ```

        **YOUR TASK:**
        Based on the user's question and their COMPLETE financial data, perform one of the following analytical tasks. Always state your assumptions clearly.

        **1. For General Questions:**
           - Analyze the trends in assets and liabilities.
           - Cross-reference with credit score.
           - Provide summary and 2-3 actionable suggestions.

        **2. For Loan Affordability Questions:**
           - Use credit score to assess worthiness.
           - Estimate EMI using 8.5% rate over 20 years.
           - Conclude feasibility with reason.

        **3. For Wealth Projections:**
           - Assume current age 28.
           - Use net worth as present value.
           - Use FV = PV * (1 + r)^t with r = 11%.
           - Present projected value.

        ---
        **USER'S QUESTION:** \"{user_question}\"
        ---

        Provide expert, data-driven response using Markdown.
        """

        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        return f"An error occurred with the AI model: {e}"
