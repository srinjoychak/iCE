import email
import re
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

mongo_db = os.getenv("MONGODB_SERVER")
client = MongoClient(mongo_db)
db = client["ice"]

def time_to_seconds(time):
    try:
        total_seconds = 0
        # Define a dictionary to map time units to seconds
        unit_mapping = {"w": 5 * 8 * 60 * 60, "d": 8 * 60 * 60, "h": 60 * 60, "m": 60}

        # Use regex to extract time components
        matches = re.findall(r"(\d+)([wdhm]?)", time)

        if not matches:
            raise ValueError("Invalid time format")

        for value, unit in matches:
            total_seconds += int(value) * unit_mapping.get(unit, 1)

        return total_seconds

    except ValueError as ve:
        return None
    except Exception as e:
        return None
    
def get_user_details():
    user_details = db.user_details.find_one()
    if user_details is not None:
        email = user_details["email"]
        user_name = user_details["user_name"]
        os.environ["EMAIL"] = email
        return email, user_name
    return None, None