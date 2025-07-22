import streamlit as st
from logic import get_financial_data, get_ai_insights

st.set_page_config(
    page_title="Your Personal AI Financial Advisor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; }
    .st-emotion-cache-1g6goon {
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 15px;
        background-color: #FFFFFF;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Your Personal AI Financial Advisor")

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

if not api_key_input:
    st.warning("Please enter your Google AI API Key in the sidebar to begin.")
else:
    financial_data = get_financial_data(persona_options[selected_persona_name])

    if financial_data:
        with st.sidebar:
            st.divider()
            st.header("Financial Snapshot")

            net_worth_data = financial_data.get("fetch_net_worth", {}).get("netWorthResponse", {})
            net_worth = int(net_worth_data.get("totalNetWorthValue", {}).get("units", 0))
            total_assets = int(net_worth_data.get("totalAssets", {}).get("units", 0))
            total_liabilities = int(net_worth_data.get("totalLiabilities", {}).get("units", 0))

            st.metric(label="Net Worth", value=f"₹{net_worth:,}")
            st.metric(label="Total Assets", value=f"₹{total_assets:,}")
            st.metric(label="Total Liabilities", value=f"₹{total_liabilities:,}")

        if "messages" not in st.session_state or st.session_state.get("current_persona") != selected_persona_name:
            st.session_state.current_persona = selected_persona_name
            st.session_state.messages = [{"role": "assistant", "content": f"Hello! I've loaded the financial snapshot for the **{selected_persona_name}**. How can I assist you today?"}]

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

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
        st.error("Could not load financial data. Please ensure the mock server is running and accessible.")
