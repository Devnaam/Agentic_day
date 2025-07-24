@echo off
echo Setting up the environment...

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate

REM Install Python dependencies
pip install streamlit requests python-dotenv google-generativeai

REM Start the Go server
start cmd /k "cd fi-server && go run main.go"

REM Start the Streamlit app
cd my_ai_advisor
streamlit run app.py
