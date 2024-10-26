import requests
import json
import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
wordware_api_key = os.getenv('WORDWARE_API_KEY')
amadeus_api_key = os.getenv("AMADEUS_API_KEY")
amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")

# Amadeus authentication URL
auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"

# Initialize session state for output
if 'output_text' not in st.session_state:
    st.session_state['output_text'] = "Start"

def remove_backticks(input_string):
    return input_string.replace('`', '')

# Function to get Amadeus API access token
def get_access_token():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": amadeus_api_key,
        "client_secret": amadeus_api_secret
    }
    
    response = requests.post(auth_url, headers=headers, data=data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        return token
    else:
        st.error(f"Failed to get access token: {response.status_code}")
        return None

# Step 1: Function to get hotel IDs from Hotel List API
def get_hotel_ids(city_code):
    token = get_access_token()
    if not token:
        return None

    url = f"https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "cityCode": city_code,
        "hotelSource": "ALL"  # Include all hotels
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        hotels = response.json().get("data", [])
        hotel_ids = [hotel["hotelId"] for hotel in hotels]
        return hotel_ids
    else:
        st.error(f"Failed to retrieve hotel IDs: {response.status_code}")
        return None

# Step 2: Function to search for hotel offers using Hotel Offers API
def search_hotel_offers(hotel_ids, check_in_date, check_out_date, adults):
    token = get_access_token()
    if not token:
        return None

    url = f"https://test.api.amadeus.com/v3/shopping/hotel-offers"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "hotelIds": ','.join(hotel_ids),
        "adults": adults,
        "checkInDate": check_in_date,
        "checkOutDate": check_out_date,
        "countryOfResidence": "AUS",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        hotel_offers = response.json()
        return hotel_offers
    else:
        st.error(f"Failed to retrieve hotel offers: {response.status_code}")
        return None

# Streamlit interface for hotel search based on JSON user data
st.title("Personalized Hotel Search for Predefined Users")

# Load user data from users.json
def load_user_data(file_path="users.json"):
    try:
        with open(file_path, 'r') as file:
            user_data = json.load(file)
        return user_data["users"]
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON file: {e}")
        return None

users = load_user_data()

# Dropdown for selecting a user
if users:
    user_names = [user['name'] for user in users]
    selected_user = st.selectbox("Select a user", user_names)
    
    selected_user_data = next((user for user in users if user['name'] == selected_user), None)
    
    if selected_user_data:
        if st.button(f"Search Hotels for {selected_user}"):
            st.write(f"Searching hotels for {selected_user} traveling to {selected_user_data['destination']}...")

            # Get hotel IDs based on city code
            if selected_user_data['destination'] == "Japan (Hokkaido)":
                location_code = "SPK"  # Example IATA city code for Sapporo, Hokkaido
            else:
                location_code = None

            if location_code:
                hotel_ids = get_hotel_ids(location_code)
                print(hotel_ids)
                
                if hotel_ids:
                    # Use hotel IDs to get hotel offers
                    hotel_offers = search_hotel_offers(
                        hotel_ids,
                        selected_user_data['dates']['check_in'],
                        selected_user_data['dates']['check_out'],
                        selected_user_data['travel_group_size']
                    )

                    if hotel_offers:
                        st.write(f"Hotel Offers for {selected_user}:")
                        st.write(json.dumps(hotel_offers, indent=4))
                    else:
                        st.write(f"No hotel offers found for {selected_user}.")
                else:
                    st.write("No hotels found in the selected city.")
            else:
                st.write(f"Unknown location for {selected_user_data['destination']}.")
