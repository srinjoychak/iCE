import collections
from turtle import st
from github import Github
import os
from dotenv import load_dotenv
from logger_config import logging
from pymongo import MongoClient
import datetime


load_dotenv()
mongo_db = os.getenv("MONGODB_SERVER")
client = MongoClient(mongo_db)
db = client["ice"]


def search_code_in_github(git, key_word, extension):
    try:
        token = git["git_token"]
        base_url = git["git_url"]
        github_client = Github(base_url=base_url, login_or_token=token)
        user = github_client.get_user().login
        return perform_search(github_client, key_word, extension)
    except Exception as e:
        logging.error(f"Failed to authenticate or connect to GitHub: {e}")
        return {"status": False, "data": str(e)}


def perform_search(github_client, keyword, extension):
    try:
        extensionlist = [
            "All relevant matches",
            "all relevant matches",
            "all",
            "All",
            "",
        ]
        if extension not in extensionlist:
            return search_with_extension(github_client, keyword, extension)
        else:
            return search_without_extension(github_client, keyword)
    except Exception as e:
        logging.error(f"Error during search: {e}")
        return {"status": False, "data": str(e)}


def search_with_extension(github_client, keyword, extension):
    try:
        extensionsearchlist = []
        query = f"{keyword} in:file extension:{extension}"
        repositories = github_client.search_code(query, highlight=True)
        max_size = 20
        if repositories.totalCount > max_size:
            repositories = repositories[:max_size]
        for repo in repositories:
            extensionsearchlist.append(repo.html_url)
        if not extensionsearchlist:
            return {"status": False, "data": "No results found"}
        else:
            extensionsearchlist = [
                item
                for item, count in collections.Counter(extensionsearchlist).items()
                if count >= 1
            ]
            list_data = extensionsearchlist[:10]
            logging.info(list_data)
            result_string = f"Here are the top 10 results for the keyword {keyword} search with extension {extension}: \n {list_data}"
            return {"status": True, "data": result_string}
    except Exception as e:
        logging.error(f"Error during search with extension: {e}")
        return {"status": False, "data": str(e)}


def search_without_extension(github_client, keyword):
    try:
        query = keyword
        storeresults = []
        repositories = github_client.search_code(query, highlight=True)
        max_size = 100
        if repositories.totalCount > max_size:
            repositories = repositories[:max_size]
        for repo in repositories:
            storeresults.append(repo.html_url)
        file_filter = [
            file
            for file in storeresults
            if not file.endswith((".txt", ".csv", "README.md", ".gitignore", "."))
        ]
        res1 = [
            item
            for item, count in collections.Counter(file_filter).items()
            if count >= 1
        ]
        list_data = res1[:10]
        logging.info(list_data)
        result_string = f"Here are the top 10 results for the keyword {keyword} search: \n {list_data}"
        return {"status": True, "data": result_string}
    except Exception as e:
        logging.error(f"Error during search without extension: {e}")
        return {"status": False, "data": str(e)}

def save_github_details(git_name, git_url, git_username, git_token):
    try:
        existing_data = db.github_details.find_one({"git_name": git_name})
        if existing_data:
            return { "status": False, "data": f"Details already exist with {git_name}" }
        else:
            db.github_details.insert_one({
                "git_name": git_name,
                "git_url": git_url,
                "git_username": git_username,
                "git_token": git_token
            })
            return { "status": True, "data": f"Details saved successfully for {git_name}" }
    except Exception as e:
        logging.error(f"Error during saving git details: {e}")
        return { "status": False, "data": "Error during saving git details" }
    
def update_github_details(git_name, git_url, git_username, git_token):
    try:
        existing_data = db.github_details.find_one({"git_name": git_name})
        if existing_data:
            db.github_details.update_one(
                {"git_name": git_name},
                {
                    "$set": {
                        "git_url": git_url,
                        "git_username": git_username,
                        "git_token": git_token
                    }
                }
            )
            return { "status": True, "data": f"Details updated successfully for {git_name}" }
        else:
            return { "status": False, "data": f"No details found with {git_name}" }
    except Exception as e:
        logging.error(f"Error during editing git details: {e}")
        return { "status": False, "data": "Error during editing git details" }

def delete_github_details(git_name):
    try:
        existing_data = db.github_details.find_one({"git_name": git_name})
        if existing_data:
            db.github_details.delete_one({"git_name": git_name})
            return { "status": True, "data": f"Details deleted successfully for {git_name}" }
        else:
            return { "status": False, "data": f"No details found with {git_name}" }
    except Exception as e:
        logging.error(f"Error during deleting git details: {e}")
        return { "status": False, "data": "Error during deleting git details" }
    
def get_gihub_registration_names():
    try:
        github_urls = []
        github_urls_obj = db.github_details.find({}, {"git_name": 1, "_id": 0})
        for url in github_urls_obj:
            github_urls.append(url)
        if len(github_urls) == 0:
            return { "status": False, "data": "No GitHub Details found, please register one" }
        return { "status": True, "data": github_urls }
    except Exception as e:
        logging.error(f"Error during fetching git names: {e}")
        return { "status": False, "data": "Error during fetching git names" }
    
def get_github_details():
    try:
        github_list = {}
        github_details_obj = db.github_details.find({})
        for details in github_details_obj:
            github_list[details["git_name"]] = details
        if len(github_list) == 0:
            return { "status": False, "data": "No GitHub Details found, please register one" }
        return { "status": True, "data": github_list }
    except Exception as e:
        logging.error(f"Error during fetching git details: {e}")
        return { "status": False, "data": "Error during fetching git details" }