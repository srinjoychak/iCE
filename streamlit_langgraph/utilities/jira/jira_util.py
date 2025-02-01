import os
from dotenv import load_dotenv
from pymongo import MongoClient
from logger_config import logging
import requests
import json
import datetime

load_dotenv()

mongo_db = os.getenv("MONGODB_SERVER")

email_address = os.getenv("EMAIL")
token = os.getenv("JIRA_API_TOKEN")
SERVER_IP = os.getenv("HOST_IP")
PORT = os.getenv("PORT")
mongo_db = os.getenv("MONGODB_SERVER")
if email_address is not None:
    username = email_address.split("@")[0]
else:
    username = None
client = MongoClient(mongo_db)
db = client["ice"]

def switch_project_to_other_project(user_name):
    try:
        data = db.ice_user_data.find(
            {"user_name": user_name},
            {"my_jira_projects": 1, "my_primary_projects": 1, "_id": 0},
        )

        projects_list = []
        primaryproject = None

        for i in data:
            projects_data = i.get("my_jira_projects", [])
            primaryproject = i.get("my_primary_projects", None)

            if not projects_data:
                raise ValueError("No Project Found")
            if not primaryproject:
                raise ValueError("No Project Found")

            for j in projects_data:
                for k in j.values():
                    projects_list.append(k)

        if len(projects_list) == 0:
            return "No Project Found"
        else:
            return [projects_list, primaryproject]

    except ValueError as ve:
        return str(ve)
    except Exception as e:
        return str(e)
    
def get_primary_project(user_name):
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    
    for record in data:
        my_primary_project = record.get("my_primary_projects")
    return my_primary_project

def updating_primary_project(user_name, selected_project):
    logging.info(f"Updating Primary Project: {selected_project}")
    db.ice_user_data.update_one(
        {"user_name": user_name},
        {"$set": {"my_primary_projects": selected_project}},
    )
    logging.info(f"Primary Project Updated: {selected_project}")
    return True

def save_jira_project(project_url, user_name):
    end_url = "http://{0}:{1}/jiraapi/project_registartion/".format(SERVER_IP, PORT)
    payload = {
        "user_name": user_name,
        "url": project_url,
        "github_url": "",
        "token": token,
        "username": username,
        "scrum_master": username,
        "email_address": email_address,
    }
    logging.info(f"Payload: {payload}")
    # Prepare the payload for the API request
    payload = json.dumps(
        payload
    )
    headers = {"Content-Type": "application/json"}
    response = requests.post( end_url, data=payload, headers=headers)
    data = response.json()
    message = data
    return message

def get_epics(user_name) -> requests.Response:
    # Construct the URL for the JIRA API request
        url = "http://{0}:{1}/jiraapi/getepicissues/".format(SERVER_IP, PORT)
        headers = {"Content-Type": "application/json"}

        # Query the database for the user's primary projects
        data = db.ice_user_data.find(
            {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
        )

        # Check if the user has any primary projects
        my_primary_project = None
        for record in data:
            if not record["my_primary_projects"]:
                return "No primary project found Please Register a project first"
            else:
                my_primary_project = record["my_primary_projects"]

        # If no primary project is found, return an error message
        if not my_primary_project:
            return [None,"No primary project found Please Register a project first"]

        # Prepare the payload for the API request
        payload = json.dumps(
            {"project_name": my_primary_project, "user_name": user_name}
        )

        # Make the API request to JIRA
        response = requests.post(url, headers=headers, data=payload)
        return response

def get_epics_drop_down_values(user_name):
    try:
        get_epics_response = get_epics(user_name)
        # Check if the response is successful
        if get_epics_response.status_code == 200:
            response_json = get_epics_response.json()
            if response_json.get("success"):
                epic_data = response_json.get("data", {})
                keys_tuple = tuple(epic_data.keys())
                return keys_tuple, epic_data
            else:
                return [None, "No epic found"]
        else:
            return [
                None,
                f"Failed to fetch epic data, status code: {get_epics_response.status_code}",
            ]
    except requests.RequestException as e:
        # Handle any request-related exceptions
        return [None, f"An error occurred while making the API request: {e}"]

    except Exception as e:
        # Handle any other exceptions
        return [None, f"An unexpected error occurred: {e}"]
    
def create_jira_issue(
    user_name,
    issue_summary,
    issue_desc,
    acceptance_criteria,
    issue_type,
    key,
):
    try:
        # Fetch user data
        data = db.ice_user_data.find(
            {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
        )

        my_primary_project = None
        for record in data:
            if not record["my_primary_projects"]:
                return {"status": False, "data": "No primary project found. Please register a project first."}
            else:
                my_primary_project = record["my_primary_projects"]

        # Prepare the payload
        payload = json.dumps(
            {
                "project_name": my_primary_project,
                "user_name": user_name,
                "summary": issue_summary,
                "description": issue_desc,
                "acceptance_criteria": acceptance_criteria,
                "issue_type": issue_type,
                "epic_key": key,
            }
        )

        # Set headers
        headers = {"Content-Type": "application/json"}

        # Make the request
        url = f"http://{SERVER_IP}:{PORT}/jiraapi/createissue/"
        response = requests.post(url, headers=headers, data=payload)

        # Check the response
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                issue_link = response_data.get("data")
                return {"status": True, "data": "Issue created successfully. Issue link: " + issue_link}
            else:
                return {"status": False, "data": response_data.get("message", "Issue creation failed")}
        else:
            return {"status": False, "data": f"Failed to create issue, status code: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"status": False, "data": f"An error occurred while making the API request: {e}"}
    except json.JSONDecodeError as e:
        return {"status": False, "data": f"An error occurred while decoding the response: {e}"}
    except Exception as e:
        return {"status": False, "data": f"An unexpected error occurred: {e}"}
    
def get_daily_scrum_report(user_name) -> requests.Response:
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/dailystatusreport/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return {"status": False, "data": "No primary project found. Please register a project first."}
        else:
            my_primary_project = record["my_primary_projects"]
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=payload)
    return response

def get_velocity_report(user_name) -> requests.Response:
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/velocityreport/"
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return {"status": False, "data": "No primary project found. Please register a project first."}
        else:
            my_primary_project = record["my_primary_projects"]
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=payload)
    return response

def get_sprint_report(user_name) -> requests.Response:
    my_primary_project = get_primary_project(user_name)

    if not my_primary_project:
        return {"status": False, "data": "No primary project found. Please register a project first."}
    
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/datasprint/"
    payload = json.dumps({
        "project_key": my_primary_project,
        "user_name": user_name,
    })
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=payload)
    return response

def view_backlogs(user_name) -> requests.Response:
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return "No primary project found Please Register a project first"
        else:
            my_primary_project = record["my_primary_projects"]
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/viewbacklog/"
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response

def get_issues_by_assignee(user_name):
    data = get_all_issues(user_name)
    fileter_data = filter_by_assignee(data, email_address)
    return fileter_data

def get_all_issues(user_name):
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return {"status": False, "data": "No primary project found. Please register a project first."}
        else:
            my_primary_project = record["my_primary_projects"]

    url = f"http://{SERVER_IP}:{PORT}/jiraapi/getissues/"
    payload = json.dumps(
        {
            "project_name": my_primary_project,
            "user_name": user_name,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()["data"]
    return data

def get_burn_up_report(user_name) -> requests.Response:
    my_primary_project = get_primary_project(user_name)

    if not my_primary_project:
        return {"status": False, "data": "No primary project found. Please register a project first."}

    url = f"http://{SERVER_IP}:{PORT}/jiraapi/burnupreport/"
    payload = json.dumps({"project_name": my_primary_project, "user_name": user_name})
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=payload)
    return response

def get_burn_down_report(user_name) -> requests.Response:
    my_primary_project = get_primary_project(user_name)

    if not my_primary_project:
        return {"status": False, "data": "No primary project found. Please register a project first."}

    url = f"http://{SERVER_IP}:{PORT}/jiraapi/burndownreport/"
    payload = json.dumps({"project_name": my_primary_project, "user_name": user_name})
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=payload)
    return response

def get_issue_details(user_name, issue_key):
    my_primary_project = get_primary_project(user_name)

    if not my_primary_project:
        return {"status": False, "data": "No primary project found. Please register a project first."}
    
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/getissuedetails/"
    payload = json.dumps({"project_name": my_primary_project, "user_name": user_name, "issue_key": issue_key})
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=payload)
    return response

def filter_by_assignee(data, assignee_name):

    filtered_data = {
        key: value for key, value in data.items() if value["Assignee"] == assignee_name
    }
    return filtered_data

def add_worklog(user_name, payload):
    data = db.ice_user_data.find(
        {"user_name": user_name}, {"my_primary_projects": 1, "_id": 0}
    )
    for record in data:
        if not record["my_primary_projects"]:
            return {"status": False, "data": "No primary project found. Please register a project first."}
        else:
            my_primary_project = record["my_primary_projects"]
    payload["project_name"] = my_primary_project
    url = f"http://{SERVER_IP}:{PORT}/jiraapi/update_jira_issues/"
    response = requests.post(url,data=payload)
    return response

def register_jira_details(email, jira_token):
    logging.info(f"Registering Jira details for {email}")
    try:
        user_details = db.user_details.find_one()
        if user_details is None:
            user_name = email.split("@")[0]
            db.user_details.insert_one({"email": email, "user_name": user_name})
            db.ice_user_data.insert_one(
                {
                    "user_name": user_name,
                    "username": user_name,
                    "email": email,
                    "iCE_cred_properties": {
                        "sso_auth": "",
                        "sonar_cube": "",
                        "git_token": "",
                        "k8s_config_file": "",
                        "jenkins_token": "",
                        "api_token": "",
                    },
                    "my_primary_projects": "",
                    "my_jira_projects": [],
                    "usercreated": datetime.datetime.today().strftime("%d-%m-%Y %I:%M %p"),
                    "lastActivity": datetime.datetime.today().strftime("%d-%m-%Y %I:%M %p"),
                }
            )
        else:
            db.user_details.update_one({"_id": user_details["_id"]}, {"$set": {"email": email, "user_name": user_name}})
        data = db.jira_details.find_one()
        if data is None:
            user_name = email.split("@")[0]
            db.jira_details.insert_one({"email": email, "user_name": user_name, "api_token": jira_token})
        else:
            db.jira_details.update_one({"_id": data["_id"]}, {"$set": {"email": email, "user_name": user_name, "api_token": jira_token}})
        return True
    except Exception as e:
        logging.error(f"Error while registering Jira details: {e}")
        return False
    