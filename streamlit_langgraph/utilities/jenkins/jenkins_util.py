import os
from dotenv import load_dotenv
from pymongo import MongoClient
from logger_config import logging
import requests
import base64
from requests.auth import HTTPBasicAuth
import datetime

load_dotenv()

mongo_db = os.getenv("MONGODB_SERVER")



client = MongoClient(mongo_db)
db = client["ice"]

def get_all_jenkins_pipelines():
    try:
        pipeline_list = {}
        pipeline_obj = db.jenkins_details.find({})
        for pipeline in pipeline_obj:
            pipeline_list[pipeline["pipeline_name"]] = pipeline
        if len(pipeline_list) == 0:
            return { "status": False, "data": "No pipelines found. Please register a pipeline."}
        return { "status": True, "data": pipeline_list}
    except Exception as e:
        logging.error(f"Error in fetching pipeline list {str(e)}")
        return { "status": False, "data": f"Failed to fetch pipeline list with exception as {str(e)}"}

def get_pipeline_details(pipeline_name):
    try:
        pipeline_details = db.jenkins_details.find_one({"pipeline_name": pipeline_name})
        if pipeline_details is None:
            return {"status": False, "data": f"Pipeline details not found for {pipeline_name}."}
        return {"status": True, "data": pipeline_details}
    except Exception as e:
        logging.error(f"Error in fetching pipeline details: {str(e)}")
        return {"status": False, "data": "Failed to fetch pipeline details."}

def get_jenkins_build_name():
    try:
        pipeline_list = []
        pipeline_obj = db.jenkins_details.find({}, {"pipeline_name": 1, "_id": 0})
        for pipeline in pipeline_obj:
            pipeline_list.append(pipeline["pipeline_name"])
        if len(pipeline_list) == 0:
            return { "status": False, "data": "No pipelines found. Please register a pipeline."}
        return { "status": True, "data": pipeline_list}
    except Exception as e:
        logging.error(f"Error in fetching service_name_list {str(e)}")
        return { "status": False, "data": f"Failed to fetch service name list with exception as {str(e)}"}
    
def execute_jenkins_build(branch, selected_pipeline):
    try:
        pipe_line_details = get_pipeline_details(selected_pipeline)
        if not pipe_line_details["status"]:
            return {"log": None, "data": pipe_line_details["data"]}
        user = pipe_line_details["data"]["user"]
        token = pipe_line_details["data"]["token"]
        build_parameter = get_jenkins_build_parameters(selected_pipeline)
        logging.info(f"Build Parameter: {build_parameter}")
        if len(build_parameter) != 0:
            #auth_token = build_parameter[0]
            jenkins_url = build_parameter[0]
            build_url = build_parameter[1]
            logging.info(f"Build URL: {build_url}")
            param_map = {}
            param_map["git_branch"] = branch
            if param_map:
                for name, value in param_map.items():
                    jenkins_url += f"&{name}={value}"
            logging.info(f"Jenkins URL: {jenkins_url}")
            logging.info(f"Jenkins User: {user}")
            response = requests.post(jenkins_url, auth=HTTPBasicAuth(user, token))
            logging.info(f"Jenkins Response: {response.status_code}")
            if response.status_code == 401:
                # Handle invalid credentials
                return {"log": None, "data": "Invalid username or password."}
            elif response.status_code == 403:
                # Handle unauthorized access
                return {
                    "log": None,
                    "data": "Access to the requested resource was forbidden.",
                }
            elif response.status_code == 201:
                return { "log": response, "data": f"Jenkins build triggered successfully for the pipeline {selected_pipeline}."}
            return {"log": None, "data": "Something went wrong. Please try again later."}
    except Exception as e:
        logging.error(f"Error in jenkins_build_ai_analysis: {str(e)}")
        return {"log": None, "data": f"Jenkins build failed with exception as {str(e)}"}
    
def get_jenkins_build_parameters(pipeline_name):
    try:
        jenkins_details = db.jenkins_details.find_one({"pipeline_name": pipeline_name})
        if jenkins_details is None:
            return [None, "Pipeline details not found."]
        jenkins_url = jenkins_details["jenkins_url"]

        # Remove parameters from URL
        build_url = remove_parameters_from_url(jenkins_url)

        logging.info(f"Jenkins URL: {jenkins_url}")
        return [jenkins_url, build_url]
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return [None, "An error occurred while fetching Jenkins build parameters."]
    
def generate_basic_token(username, token):
    # Concatenate the username and token with a colon separator
    credentials = f"{username}:{token}"
    # Encode the credentials using base64
    encoded_credentials = base64.b64encode(credentials.encode("utf-8"))
    # Convert the encoded credentials to a string
    basic_token = encoded_credentials.decode("utf-8")

    return "Basic" + " " + basic_token

def remove_parameters_from_url(input_url):
    output_url = input_url
    # Check if the input URL contains "buildWithParameters?token="
    if "buildWithParameters?token=" in input_url:
        # Find the starting index of the "buildWithParameters?token=" substring
        start_index = input_url.find("buildWithParameters?token=")
        # Extract the portion of the URL before the "buildWithParameters?token=" substring
        output_url = input_url[:start_index]
        # Return the output URL
    elif "build?token=" in input_url:
        start_index = input_url.find("/build?token=")
        output_url = input_url[:start_index]
    
    # If the input URL doesn't contain "buildWithParameters?token=" return the original URL
    return output_url

def get_latest_build_no_by_job_name(pipeline_name):
    try:
        pipe_line_details = get_pipeline_details(pipeline_name)
        if not pipe_line_details["status"]:
            return {"log": None, "data": pipe_line_details["data"]}
        user = pipe_line_details["data"]["user"]
        token = pipe_line_details["data"]["token"]
        build_parameter = get_jenkins_build_parameters(pipeline_name)
        logging.info(f"Build Parameter: {build_parameter}")
        if len(build_parameter) != 0:
            url = build_parameter[0]
            build_url = build_parameter[1]
            logging.info(f"Build URL: {build_url}")
            get_build_no_url = f"{build_url}/lastBuild/buildNumber"
            logging.info(f"Get Build No URL: {get_build_no_url}")
            response = requests.get(get_build_no_url, auth=HTTPBasicAuth(user, token))
            logging.info(f"Jenkins Response: {response.status_code}")
            if response.status_code == 401:
                # Handle invalid credentials
                return {"status": False, "data": "Invalid username or password."}
            elif response.status_code == 403:
                # Handle unauthorized access
                return {"status": False, "data": "Access to the requested resource was forbidden."}
            elif response.status_code == 200:
                return { "status": True, "data": response.json()}
    except requests.RequestException as e:
        logging.error(f"Failed to get latest build number: {str(e)}")
        return {"status": False, "data": "Failed to get latest build number."}
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return {"status": False, "data": "An error occurred while fetching latest build number."}
    
def get_execution_status_by_build_number(pipeline_name, build_number):
    try:
        pipe_line_details = get_pipeline_details(pipeline_name)
        if not pipe_line_details["status"]:
            return {"log": None, "data": pipe_line_details["data"]}
        user = pipe_line_details["data"]["user"]
        token = pipe_line_details["data"]["token"]
        build_parameter = get_jenkins_build_parameters(pipeline_name)
        logging.info(f"Build Parameter: {build_parameter}")
        if len(build_parameter) != 0:
            url = build_parameter[0]
            build_url = build_parameter[1]
            logging.info(f"Build URL: {build_url}")
            get_build_status_url = f"{build_url}/{build_number}/api/json"
            logging.info(f"Get Build Status URL: {get_build_status_url}")
            response = requests.get(get_build_status_url, auth=HTTPBasicAuth(user, token))
            logging.info(f"Jenkins Response: {response.status_code}")
            if response.status_code == 401:
                # Handle invalid credentials
                return {"status": False, "data": "Invalid username or password."}
            elif response.status_code == 403:
                # Handle unauthorized access
                return {"status": False, "data": "Access to the requested resource was forbidden."}
            elif response.status_code == 200:
                return { "status": True, "data": response.json()}
    except requests.RequestException as e:
        logging.error(f"Failed to get execution status: {str(e)}")
        return {"status": False, "data": "Failed to get execution status."}
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return {"status": False, "data": "An error occurred while fetching execution status."}
    
def save_jenkins_pipeline_details(pipeline_name, pipeline_description, jenkins_url, user, token):
    try:
        existing_pipeline = db.jenkins_details.find_one({"pipeline_name": pipeline_name})
        if existing_pipeline:
            return {"status": False, "data": f"Pipeline with name {pipeline_name} already exists."}
        else:
            db.jenkins_details.insert_one(
                {
                    "pipeline_name": pipeline_name,
                    "pipeline_description": pipeline_description,
                    "jenkins_url": jenkins_url,
                    "user": user,
                    "token": token,
                }
            )
            return {"status": True, "data": f"Pipeline {pipeline_name} details saved successfully."}
    except Exception as e:
        logging.error(f"Error in saving Jenkins pipeline details: {str(e)}")
        return {"status": False, "data": "Failed to save Jenkins pipeline details."}
    
def update_jenkins_pipeline_details(pipeline_name, pipeline_description, jenkins_url, user, token):
    try:
        existing_pipeline = db.jenkins_details.find_one({"pipeline_name": pipeline_name})
        if existing_pipeline:
            db.jenkins_details.update_one(
                {"pipeline_name": pipeline_name},
                {
                    "$set": {
                        "pipeline_description": pipeline_description,
                        "jenkins_url": jenkins_url,
                        "user": user,
                        "token": token,
                    }
                },
            )
            return {"status": True, "data": f"Pipeline {pipeline_name} details updated successfully."}
        else:
            return {"status": False, "data": f"Pipeline with name {pipeline_name} does not exist."}
    except Exception as e:
        logging.error(f"Error in updating Jenkins pipeline details: {str(e)}")
        return {"status": False, "data": "Failed to update Jenkins pipeline details."}
    
def delete_jenkins_pipeline(pipeline_name):
    try:
        existing_pipeline = db.jenkins_details.find_one({"pipeline_name": pipeline_name})
        if existing_pipeline:
            db.jenkins_details.delete_one({"pipeline_name": pipeline_name})
            return {"status": True, "data": f"Pipeline {pipeline_name} deleted successfully."}
        else:
            return {"status": False, "data": f"Pipeline with name {pipeline_name} does not exist."}
    except Exception as e:
        logging.error(f"Error in deleting Jenkins pipeline: {str(e)}")
        return {"status": False, "data": "Failed to delete Jenkins pipeline."}
    
def get_all_stages_execution_info(pipeline_name, build_number):
    try:
        pipe_line_details = get_pipeline_details(pipeline_name)
        if not pipe_line_details["status"]:
            return {"log": None, "data": pipe_line_details["data"]}
        user = pipe_line_details["data"]["user"]
        token = pipe_line_details["data"]["token"]
        build_parameter = get_jenkins_build_parameters(pipeline_name)
        logging.info(f"Build Parameter: {build_parameter}")
        if len(build_parameter) != 0:
            url = build_parameter[0]
            build_url = build_parameter[1]
            logging.info(f"Build URL: {build_url}")
            anlalysis_url = f"{build_url}/{build_number}/wfapi/describe"
            logging.info(f"Analysis URL: {anlalysis_url}")
            response = requests.get(anlalysis_url, auth=HTTPBasicAuth(user, token))
            logging.info(f"Jenkins Response: {response.status_code}")
            if response.status_code == 401:
                return {"status": False, "data": "Invalid username or password."}
            elif response.status_code == 403:
                return {
                    "status": False,
                    "data": "Access to the requested resource was forbidden.",
                }
            elif response.status_code == 200:
                return { "status": True, "data": response.json()}
    except Exception as e:
        logging.error(f"Error in analyzing Jenkins pipeline: {str(e)}")
        return {"status": False, "data": "Failed to analyze the Jenkins pipeline."}
    
def get_execution_status(pipeline_name, build_number):
    execution_status_response = get_execution_status_by_build_number(pipeline_name, build_number)
    if execution_status_response and execution_status_response["status"]:
        response = {}
        response["execution_status"] = execution_status_response["data"]
        all_stages_execution_info = get_all_stages_execution_info(pipeline_name, build_number)
        if all_stages_execution_info and all_stages_execution_info["status"]:
            all_stages_execution_info = all_stages_execution_info["data"]
            response["all_stages_execution_info"] = all_stages_execution_info
            if "stages" in all_stages_execution_info:
                stages = all_stages_execution_info["stages"]
                ids = []
                for stage in stages:
                    ids.append(stage["id"])
                response["stage_ids"] = ids
        return response
    
def get_stage_execution_info(pipeline_name, build_number, stage_id):
    try:
        pipe_line_details = get_pipeline_details(pipeline_name)
        if not pipe_line_details["status"]:
            return {"log": None, "data": pipe_line_details["data"]}
        user = pipe_line_details["data"]["user"]
        token = pipe_line_details["data"]["token"]
        build_parameter = get_jenkins_build_parameters(pipeline_name)
        logging.info(f"Build Parameter: {build_parameter}")
        if len(build_parameter) != 0:
            url = build_parameter[0]
            build_url = build_parameter[1]
            logging.info(f"Build URL: {build_url}")
            stage_url = f"{build_url}/{build_number}/execution/node/{stage_id}/wfapi/describe"
            logging.info(f"Stage URL: {stage_url}")
            response = requests.get(stage_url, auth=HTTPBasicAuth(user, token))
            logging.info(f"Jenkins Response: {response.status_code}")
            if response.status_code == 401:
                return {"status": False, "data": "Invalid username or password."}
            elif response.status_code == 403:
                return {
                    "status": False,
                    "data": "Access to the requested resource was forbidden.",
                }
            elif response.status_code == 200:
                return { "status": True, "data": response.json()}
    except Exception as e:
        logging.error(f"Error in fetching stage execution information: {str(e)}")
        return {"status": False, "data": "Failed to fetch stage execution information."}
    
def get_node_execution_log(pipeline_name, build_number, node_id):
    try:
        pipe_line_details = get_pipeline_details(pipeline_name)
        if not pipe_line_details["status"]:
            return {"log": None, "data": pipe_line_details["data"]}
        user = pipe_line_details["data"]["user"]
        token = pipe_line_details["data"]["token"]
        build_parameter = get_jenkins_build_parameters(pipeline_name)
        logging.info(f"Build Parameter: {build_parameter}")
        if len(build_parameter) != 0:
            url = build_parameter[0]
            build_url = build_parameter[1]
            logging.info(f"Build URL: {build_url}")
            log_url = f"{build_url}/{build_number}/execution/node/{node_id}/wfapi/log"
            logging.info(f"Log URL: {log_url}")
            response = requests.get(log_url, auth=HTTPBasicAuth(user, token))
            logging.info(f"Jenkins Response: {response.status_code}")
            if response.status_code == 401:
                return {"status": False, "data": "Invalid username or password."}
            elif response.status_code == 403:
                return {
                    "status": False,
                    "data": "Access to the requested resource was forbidden.",
                }
            elif response.status_code == 200:
                return { "status": True, "data": response.json()}
    except Exception as e:
        logging.error(f"Error in fetching execution log: {str(e)}")
        return {"status": False, "data": "Failed to fetch execution log."}
    
def get_stage_flow_node_execution_log(pipeline_name, build_number, stage_flow_node_id):
    try:
        pipe_line_details = get_pipeline_details(pipeline_name)
        if not pipe_line_details["status"]:
            return {"log": None, "data": pipe_line_details["data"]}
        user = pipe_line_details["data"]["user"]
        token = pipe_line_details["data"]["token"]
        build_parameter = get_jenkins_build_parameters(pipeline_name)
        logging.info(f"Build Parameter: {build_parameter}")
        if len(build_parameter) != 0:
            url = build_parameter[0]
            build_url = build_parameter[1]
            logging.info(f"Build URL: {build_url}")
            log_url = f"{build_url}/{build_number}/execution/node/{stage_flow_node_id}/log"
            logging.info(f"Log URL: {log_url}")
            response = requests.get(log_url, auth=HTTPBasicAuth(user, token))
            logging.info(f"Jenkins Response: {response.status_code}")
            if response.status_code == 401:
                return {"status": False, "data": "Invalid username or password."}
            elif response.status_code == 403:
                return {
                    "status": False,
                    "data": "Access to the requested resource was forbidden.",
                }
            elif response.status_code == 200:
                return { "status": True, "data": response.text}
    except Exception as e:
        logging.error(f"Error in fetching stage execution log: {str(e)}")
        return {"status": False, "data": "Failed to fetch stage execution log."}
    