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

# Can be attributed to Week 6 tutorial
def do_wordware(prompt_id, inputs_wordware, api_key):
    ''' Takes prompt_id url, inputs for agents and API key to call WordWare API '''

    response = requests.post(
        f"https://app.wordware.ai/api/released-app/{prompt_id}/run",
        json={"inputs": inputs_wordware},
        headers={"Authorization": f"Bearer {api_key}"},
        stream=True,
    )
    if response.status_code != 200:
        st.error(f"Request failed with status code {response.status_code}.")
        return "[]"  # Return an empty JSON array as a string on failure
    else:
        # Successful API call
        text_output = ""
        for line in response.iter_lines():
            if line:
                content = json.loads(line.decode("utf-8"))
                value = content["value"]
                if value["type"] == "chunk":
                    text_output += value["value"]
        st.session_state['output_text'] = text_output + st.session_state['output_text']
        return text_output or "[]"  # Ensure it returns a string


# Step 1: Function to get hotel IDs from Hotel List API with filters
def get_hotel_ids(city_code, amenities=None, max_ids=10):
    ''' Takes city code, amenities and max amount of ids to
    retrieve Hotel IDs from Amadeus Hotel List API '''

    token = get_access_token()
    if not token:
        return None

    url = f"https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "cityCode": city_code,
        "hotelSource": "ALL",
        "amenities": ",".join(amenities) if amenities else None  # Use amenities as a filter
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        hotels = response.json().get("data", [])
        hotel_ids = [hotel["hotelId"] for hotel in hotels]
        return hotel_ids[:max_ids]
    else:
        st.error(f"Failed to retrieve hotel IDs: {response.status_code}")
        return None



# Step 2: Function to search for hotel offers using Hotel Offers API
def search_hotel_offers(hotel_ids, check_in_date, check_out_date, adults):
    ''' Takes hotel_ids, check in date, check out date, no. of adults
    to search for specific hotel offers '''

    token = get_access_token()
    if not token:
        return None

    url = f"https://test.api.amadeus.com/v3/shopping/hotel-offers"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "hotelIds": hotel_ids,
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        hotel_offers = response.json()
        return hotel_offers
    else:
        st.error(f"Failed to retrieve hotel offers: {response.status_code}")
        return None

# New function to fetch tours and activities including booking link
def get_tours_and_activities(latitude, longitude, max_activities=30):
    token = get_access_token()
    if not token:
        return None

    url = f"https://test.api.amadeus.com/v1/shopping/activities"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": 10  # Radius in kilometers
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        activities = response.json().get("data", [])
        return activities[:max_activities]  # Limit the number of activities displayed
    else:
        st.error(f"Failed to retrieve tours and activities: {response.status_code}")
        return None

# # Function to call WordWare API to categorize traveler
# def categorize_traveler(user_data):
#     categorization_inputs = {
#         "Group Type": user_data["group_type"],
#         "Interests": ", ".join(user_data.get("interests", [])),
#         "Accessibility Needs": user_data.get("accessibility_needs", "N/A"),
#         "Purpose of Travel": user_data.get("purpose_of_travel", "N/A")
#     }
#     prompt_id = "56d08b77-96b5-4ef4-8339-dcb772ee93f3"  # Replace with your actual prompt ID
#     category_filters = do_wordware(prompt_id, categorization_inputs, wordware_api_key)
    
#     try:
#         # Parse category_filters as amenities
#         amenities = json.loads(category_filters) if category_filters else []
#         return amenities
#     except json.JSONDecodeError:
#         st.error("Failed to parse amenities.")
#         return []




# Streamlit interface for hotel search and activity suggestions based on JSON user data
st.title("UrTrip Travel Webpage")

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
        if st.button(f"Search Hotels and Activities for {selected_user}"):
            st.write(f"Searching hotels and activities for {selected_user} traveling to {selected_user_data['destination']}...")

            # Ugly hard coded locations for hotel and activity search
            if selected_user_data['destination'] == "Japan (Hokkaido)":
                location_code = "SPK"
                latitude, longitude = 43.0667, 141.3500
            elif selected_user_data['destination'] == "Japan (Tokyo)":
                location_code = "TYO"
                latitude, longitude = 35.6895, 139.6917
            elif selected_user_data['destination'] == "USA (New York City)":
                location_code = "NYC"
                latitude, longitude = 40.7128, -74.0060
            elif selected_user_data['destination'] == "UK (London)":
                location_code = "LON"
                latitude, longitude = 51.5074, -0.1278
            elif selected_user_data['destination'] == "France (Paris)":
                location_code = "PAR"
                latitude, longitude = 48.8566, 2.3522
            else:
                location_code, latitude, longitude = None, None, None

            # Hotel search by location code
            if location_code:
                # Call categorize_traveler to get amenities
                # amenities = categorize_traveler(selected_user_data)
                # Pass amenities to get_hotel_ids
                
                if location_code:
                    # hotel_ids = get_hotel_ids(location_code, amenities=amenities)
                    hotel_ids = get_hotel_ids(location_code)

                
                if hotel_ids:
                    hotel_offers = search_hotel_offers(
                        hotel_ids,
                        selected_user_data['dates']['check_in'],
                        selected_user_data['dates']['check_out'],
                        selected_user_data['travel_group_size']
                    )

                    if hotel_offers:
                        st.write(f"Hotel Offers for {selected_user}:")
                        for offer in hotel_offers.get("data", []):
                            hotel_name = offer.get("hotel", {}).get("name", "N/A")
                            hotel_address = offer.get("hotel", {}).get("address", {}).get("lines", ["N/A"])[0]
                            price = offer.get("offers", [{}])[0].get("price", {}).get("total", "N/A")
                            currency = offer.get("offers", [{}])[0].get("price", {}).get("currency", "N/A")

                            st.subheader(hotel_name)
                            st.write(f"Address: {hotel_address}")
                            st.write(f"Price: {currency} {price}")
                            st.write("---")
                    else:
                        st.write(f"No hotel offers found for {selected_user}.")
                else:
                    st.write("No hotels found in the selected city.")
            else:
                st.write(f"Unknown location for {selected_user_data['destination']}.")

            # Activity search by latitude and longitude
            if latitude and longitude:
                activities = get_tours_and_activities(latitude, longitude)
                activities_json = json.dumps(activities[:10])  # Format and limit activities as JSON
                if activities:
                    st.write(f"Travel Information for {selected_user} in {selected_user_data['destination']}:")
                    for activity in activities:
                        activity_name = activity.get("name", "N/A")
                        activity_description = activity.get("shortDescription", "No description available")
                        activity_price = activity.get("price", {}).get("amount", "N/A")
                        activity_currency = activity.get("price", {}).get("currencyCode", "N/A")
                        booking_link = activity.get("bookingLink", "No booking link available")

                        print(activity_name)
                        print(f"Description: {activity_description}")
                        print(f"Price: {activity_currency} {activity_price}")
                        print(f"[Book this activity]({booking_link})")
                        print("-------------------------------------------")


                else:
                    st.write("No tours and activities found for the selected city.")
            
            inputs_wordware = {
                "Destination": selected_user_data["destination"],
                "Persona_Name": selected_user_data["name"],
                "Persona_Occupation": selected_user_data.get("occupation", "N/A"),
                "Persona_Location": selected_user_data["home_country"],
                "Persona_StayLength": selected_user_data["duration_of_stay"],
                "Persona_Date": selected_user_data["dates"]["check_in"],
                "Travel_Group_Type": selected_user_data["group_type"],
                "Persona_Nationality": selected_user_data["nationality"],
                "Persona_TravelHistory": ", ".join(selected_user_data["past_purchase_history"]),
                "Persona_Stay_Preference": selected_user_data["price_sensitivity"],
                "Persona_Budget": selected_user_data["PERSONA_STAY_PREFERENCE"],
                "Traveler_Experience": selected_user_data["PERSONA_STAY_PREFERENCE"],
                "Interests": selected_user_data["TRAVELER_EXPERIENCE"],
                "Activities_JSON": activities_json
            }

            prompt_id = "367ad832-13de-4e0f-953a-4a1262a578ce"
            output_text = do_wordware(prompt_id, inputs_wordware, wordware_api_key)
            st.write("Generated Information:", output_text)
