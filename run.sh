#!/bin/bash
echo "Setting up the environment..."

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install streamlit requests python-dotenv google-generativeai

# Start the Go server in the background
cd fi-server
go run main.go &

# Start the Streamlit app
cd ../my_ai_advisor
streamlit run app.py
