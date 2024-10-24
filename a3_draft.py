import requests
import json
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
wordware_api_key = os.getenv('WORDWARE_API_KEY')

# Initialize session state for output
if 'output_text' not in st.session_state:
    st.session_state['output_text'] = "Start"

def remove_backticks(input_string):
    return input_string.replace('`', '')

def do_wordware(prompt_id, inputs_wordware, api_key):
    # Construct the API endpoint URL
    url = f"https://app.wordware.ai/api/released-app/{prompt_id}/run"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Print debugging information
    print(f"Request URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps({'inputs': inputs_wordware, 'version': '^1.0'}, indent=4)}")

    # Attempt to send POST request with the required version
    try:
        response = requests.post(
            url,
            json={
                "inputs": inputs_wordware,
                "version": "^1.0"  # Adjust the version if needed
            },
            headers=headers
        )
        
        # Check for status code
        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}.")
            print(f"Response content: {response.content.decode('utf-8')}")
            st.error(f"Request failed with status code {response.status_code}.")
            return None
        else:
            # Process successful response
            text_output = ""
            for line in response.iter_lines():
                if line:
                    content = json.loads(line.decode("utf-8"))
                    value = content["value"]
                    if value["type"] == "chunk":
                        text_output += value["value"]
            st.session_state['output_text'] = text_output + st.session_state['output_text']
            return text_output
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        print(f"Request Exception: {e}")
        return None

def load_user_data(file_path="users.txt"):
    with open(file_path, 'r') as file:
        user_data = file.read()
    return user_data

def load_accommodation_data(file_path="accommodation.txt"):
    try:
        with open(file_path, 'r') as file:
            accommodation_data = json.load(file)
        return accommodation_data
    except json.JSONDecodeError as e:
        st.error(f"Failed to load accommodation data: {e}")
        print(f"JSON Decode Error: {e}")
        return None

# Streamlit interface
st.header("Personalized Travel Page Generator")

if st.button("Generate"):
    # Load data from text files
    user_data = load_user_data()
    accommodation_data = load_accommodation_data()

    if user_data and accommodation_data:
        # Step 1: Create a detailed user persona
        inputs = {
            "task": "Create a detailed user persona",
            "user_data": user_data
        }
        persona = do_wordware("225b9fa4-f1c9-4fac-b1a1-0b38ae5efc81", inputs, wordware_api_key)
        st.write("Persona:", persona)
        
        # Step 2: Evaluate cultural differences
        inputs = {
            "task": "Evaluate cultural differences",
            "user_data": user_data,
            "destination": "Hokkaido, Japan"
        }
        cultural_differences = do_wordware("225b9fa4-f1c9-4fac-b1a1-0b38ae5efc81", inputs, wordware_api_key)
        st.write("Cultural Differences:", cultural_differences)
        
        # Step 3: Match user to accommodation and activities
        inputs = {
            "task": "Match user to accommodations and activities",
            "user_persona": persona,
            "accommodation_data": accommodation_data
        }
        recommendations = do_wordware("225b9fa4-f1c9-4fac-b1a1-0b38ae5efc81", inputs, wordware_api_key)
        st.write("Recommendations:", recommendations)
        
        # Step 4: Generate a user-friendly travel page
        inputs = {
            "task": "Generate travel page",
            "user_persona": persona,
            "cultural_differences": cultural_differences,
            "recommendations": recommendations,
            "additional_info": {
                "health_and_safety": "Include relevant health and safety tips for the destination.",
                "travel_documents": "Include passport and visa requirements for the destination."
            }
        }
        travel_page = do_wordware("travel-page-prompt-id", inputs, wordware_api_key)
        st.write("Generated Travel Page:", travel_page)

st.write(st.session_state['output_text'])
