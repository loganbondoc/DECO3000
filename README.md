# A3 DECO3000


## To run the program:
### Use the following commands in the console:
- pip install exa_py
- pip install streamlit
- pip install python-dotenv
- Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
- .venv\Scripts\Activate

### Then to run the program use:
- streamlit run ur_trip.py

## Known Issues
- With the Amadeus API being the testing version, the amount of hotel offers that the "search_hotel_offers()" function is limited to specific cities with large populations such as New York City and London. This means that not all hotel id's retrieved from get_hotel_ids() are able to display the necessary information.

- The API is also shown to be inconsistent with its ability to attain hotel_ids, where the matching process of accomodation to amenities has been commented out and simulated within the WordWare program for the meantime