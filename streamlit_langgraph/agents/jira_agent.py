from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
import json
import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import utilities.jira.jira_util as jira_util
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.chat_models import HumanMessage
from logger_config import logging
from pydantic import BaseModel

class IssueData(BaseModel):
    issue_summary: str
    issue_desc: str
    acceptance_criteria: str
    issue_type: list
    epic_key: list


load_dotenv()

email = os.getenv("EMAIL")
if email is not None:
    user_name = email.split("@")[0]
else:
    user_name = None

def getSprintReport() -> dict:
    """
    This function gets the JIRA sprint report
    Output:
        sprint_report: dict
    """
    try:
        print("Getting Sprint Report")
        response = jira_util.get_sprint_report(user_name)
        response.raise_for_status()
    except requests.RequestException as e:
        print(e)
        return {"status": False, "data": "Failed to fetch the sprint report. Please try again later."}
    except Exception as e:
        print(e)
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    # Mocking the sprint report
    return {"status": True, "report_type": "sprint_report", "data": response.json()}

def switch_jira_project() -> dict:
    """
    This function helps user to switch or change the JIRA project
    """
    return {"input_form": "switch_jira_project_form"}

def register_jira_project() -> dict:
    """
    This function helps the user in registering or configuring a JIRA project.
    """
    return {"input_form": "register_jira_project_form"}

def get_velocity_report() -> dict:
    """
    This function helps user in getting velocity report of a JIRA project.
    """
    try:
        response = jira_util.get_velocity_report(user_name)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"status": False, "data": "Failed to fetch the velocity report. Please try again later."}
    except Exception as e:
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    return {"status": True, "report_type": "velocity_report", "data": response.json()}

def get_daily_scrum_report() -> dict:
    """
    This function helps user in getting daily scrum report of a JIRA project.
    """
    try:
        response = jira_util.get_daily_scrum_report(user_name)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"status": False, "data": "Failed to fetch the daily scrum report. Please try again later."}
    except Exception as e:
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    return {"status": True, "report_type": "scrum_report", "data": response.json()}

def get_epics() -> dict:
    """
    This function helps user in getting epics of a JIRA project.
    """
    try:
        response = jira_util.get_epics(user_name)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"status": False, "data": "Failed to fetch the epics. Please try again later."}
    except Exception as e:
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    return response.json()

def create_jira_issue() -> dict:
    """
    This function helps user in creating a JIRA issue for type Task or Bug or Story.
    """
    return {"input_form": "create_jira_issue_form"}

def view_backlog_issues() -> dict:
    """
    This function helps user in viewing backlog issues of a JIRA project.
    """
    try:
        response = jira_util.view_backlogs(user_name)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"status": False, "data": "Failed to fetch the backlogs. Please try again later."}
    except Exception as e:
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    return response.json()

def get_my_jira_issues() -> dict:
    """
    This function helps user in getting his JIRA issues of a JIRA project.
    """
    return {"input_form": "get_my_jira_issues_form"}

def get_current_sprint_issues() -> dict:
    """
    This function helps user in getting all the issues of the current sprint of a JIRA project.
    """
    return {"input_form": "get_current_sprint_issues_form"}

def get_burn_up_report() -> dict:
    """
    This function helps user in getting burn up report of a JIRA project.
    """
    try:
        response = jira_util.get_burn_up_report(user_name)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"status": False, "data": "Failed to fetch the burn up report. Please try again later."}
    except Exception as e:
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    return {"status": True, "report_type": "burnup_report", "data": response.json()}

def get_burn_down_report() -> dict:
    """
    This function helps user in getting burn down report of a JIRA project.
    """
    try:
        response = jira_util.get_burn_down_report(user_name)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"status": False, "data": "Failed to fetch the burn down report. Please try again later."}
    except Exception as e:
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    return {"status": True, "report_type": "burndown_report", "data": response.json()}

def get_issue_details(issue_key) -> dict:
    """
    This function helps user in getting details of a JIRA issue by issue key.
    """
    try:
        response = jira_util.get_issue_details(user_name, issue_key)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"status": False, "data": "Failed to fetch the issue details. Please try again later."}
    except Exception as e:
        return {"status": False, "data": "An unexpected error occurred. Please try again later. Error: " + str(e)}
    return {"status": True, "data": response.json()}

class JiraAgent:
    def __init__(self, llm: BaseChatModel):
        self.email = os.getenv("EMAIL")
        if self.email is not None:
            self.user_name = self.email.split("@")[0]
        else:
            self.user_name = None
        self.mongo_db = os.getenv("MONGODB_SERVER")
        self.SERVER_IP = os.getenv("HOST_IP")
        self.PORT = os.getenv("PORT")
        self.token = os.getenv("JIRA_API_TOKEN")

        self.llm = llm
        self.client = MongoClient(self.mongo_db)
        self.db = self.client["ice"]

        self.tools = [
            getSprintReport,
            switch_jira_project,
            register_jira_project,
            get_velocity_report,
            get_daily_scrum_report,
            get_epics,
            create_jira_issue,
            view_backlog_issues,
            get_my_jira_issues,
            get_current_sprint_issues,
            get_burn_up_report,
            get_burn_down_report,
            get_issue_details
        ]

        self.tools_with_form = [
            "switch_jira_project",
            "register_jira_project",
            "create_jira_issue",
            "get_my_jira_issues",
            "get_current_sprint_issues",
            "register_jira_details"
        ]

        self.tools_with_reports = [
            "getSprintReport",
            "get_velocity_report",
            "get_burn_up_report",
            "get_daily_scrum_report",
            "get_burn_down_report"
            
        ]

        self.llm_with_jira = self.llm.bind_tools(self.tools)
        self.jira_graph_agent = self.create_jira_graph_agent()

    class CustomAgentState(MessagesState):
        sprint_report: dict
        velocity_report: dict
        burnup_report: dict
        burndown_report: dict
        scrum_report: dict
        error_message: str
        input_form: str
        form_data: dict

    # def jira_tool_calling_llm(self, state: CustomAgentState):
    #     latest_message = state['messages'][-1]
    #     if latest_message.name in self.tools_with_form:
    #         content_dict = json.loads(latest_message.content)
    #         # print("latest commit======", content_dict)
    #         if "status" in content_dict:
    #             status = content_dict["status"]
    #             if status == True:
    #                 state['sprint_report'] = content_dict["data"]
    #             elif status == False:
    #                 state['error_message'] = content_dict["data"]
    #         elif "input_form" in content_dict:
    #             state['input_form'] = content_dict["input_form"]
    #     message = self.llm_with_jira.invoke(state['messages'])
    #     state['messages'] = [message]
    #     return state

    def verify_jira_details(self, state: CustomAgentState):
        logging.info("Verifying JIRA Details")
        if self.email is None or self.user_name is None or self.token is None:
            user_details = self.db.user_details.find_one()
            if user_details is None:
                logging.info("User Details not found")
                state["messages"] = [HumanMessage(content=json.dumps({"input_form": "register_jira_details_form"}), name="register_jira_details")]
                state["input_form"] = "register_jira_details_form"
            else:
                logging.info("User Details found")
                self.email = user_details["email"]
                self.user_name = user_details["user_name"]
                os.environ["EMAIL"] = self.email
                global user_name, email
                user_name = self.user_name
                email = self.email
                jira_util.email_address = self.email
                jira_util.username = self.user_name
            jira_details = self.db.jira_details.find_one()
            if jira_details is None:
                logging.info("JIRA Details not found")
                state["messages"] = [HumanMessage(content=json.dumps({"input_form": "register_jira_details_form"}), name="register_jira_details")]
                state["input_form"] = "register_jira_details_form"
            else:
                logging.info("JIRA Details found")
                token = jira_details["api_token"]
                os.environ["JIRA_API_TOKEN"] = token
                jira_util.token = token
        return state

    def jira_tool_calling_llm(self, state: CustomAgentState):
        if "input_form" in state and state["input_form"] is not None:
            return state
        latest_message = state['messages'][-1]
        print("latest_message.name",latest_message.name, self.tools_with_reports, latest_message.name in self.tools_with_reports)
        if latest_message.name in self.tools_with_form:
            print("inside the if block")
            content_dict = json.loads(latest_message.content)
            # print("latest commit======", content_dict)
            if "status" in content_dict:
                status = content_dict["status"]
                if status == False:
                    state['error_message'] = content_dict["data"]
            elif "input_form" in content_dict:
                if content_dict['input_form'] == 'create_jira_issue_form':
                    prompt = """Understand the Instructions properly and Provide the required Predefined data in a structured format, only if the user asked to. if the required information 
                    is already available only in the recent conversation, else provide the empty data even if the required data available in the conversation"""
                    messages = [
                        {"role": "system", "content": prompt},
                    ] + state["messages"]
                    data = self.llm.with_structured_output(IssueData).invoke(messages)
                    data = {'data': json.loads(data.model_dump_json())}                    
                    state['form_data'] = data
                    state['input_form'] = content_dict["input_form"]
                else:
                    state['input_form'] = content_dict["input_form"]
        elif latest_message.name in self.tools_with_reports:
            print("inside the else block")
            content_dict = json.loads(latest_message.content)
            print("latest commit======", content_dict, content_dict.get("report_type"))
            if "status" in content_dict:
                status = content_dict["status"]
                if status:
                    report_type = content_dict.get("report_type")
                    if report_type == "sprint_report":
                        state['sprint_report'] = content_dict["data"]
                    elif report_type == "velocity_report":
                        state['velocity_report'] = content_dict["data"]
                    elif report_type == "scrum_report":
                        state['scrum_report'] = content_dict["data"]
                    elif report_type == "burnup_report":
                        state['burnup_report'] = content_dict["data"]
                    elif report_type == "burndown_report":
                        state['burndown_report'] = content_dict["data"]
                    else:
                        state[f'{report_type}_report'] = content_dict["data"]
            elif "input_form" in content_dict:
                state['input_form'] = content_dict["input_form"]
        message = self.llm_with_jira.invoke(state['messages'])
        state['messages'] = [message]
        return state
    
    # def jira_tool_calling_llm(self, state: CustomAgentState):
    #     latest_message = state['messages'][-1]
    #     print("latest commit======",latest_message,latest_message.name in self.tools_with_form)

    #     if latest_message.name in self.tools_with_form:
    #         content_dict = json.loads(latest_message.content)
    #         if "status" in content_dict:
    #             status = content_dict["status"]
    #             if status:
    #                 report_type = content_dict.get("report_type")
    #                 if report_type == "sprint_report":
    #                     state['sprint_report'] = content_dict["data"]
    #                 elif report_type == "velocity_report":
    #                     state['velocity_report'] = content_dict["data"]
    #                 elif report_type == "scrum_report":
    #                     state['scrum_report'] = content_dict["data"]
    #                 elif report_type == "burnup_report":
    #                     state['burnup_report'] = content_dict["data"]
    #                 elif report_type == "burndown_report":
    #                     state['burndown_report'] = content_dict["data"]
    #                 else:
    #                     state[f'{report_type}_report'] = content_dict["data"]
    #             else:
    #                 state['error_message'] = content_dict["data"]
    #         elif "input_form" in content_dict:
    #             state['input_form'] = content_dict["input_form"]
    #     message = self.llm_with_jira.invoke(state['messages'])
    #     state['messages'] = [message]
    #     return state

    def create_jira_graph_agent(self):
        graph_builder = StateGraph(self.CustomAgentState)

        graph_builder.add_node("tool_calling_llm", self.jira_tool_calling_llm)
        graph_builder.add_node("tools", ToolNode(self.tools))
        graph_builder.add_node("verify_jira_details", self.verify_jira_details)

        graph_builder.add_edge(START, "verify_jira_details")
        graph_builder.add_edge("verify_jira_details", "tool_calling_llm")
        graph_builder.add_conditional_edges("tool_calling_llm", tools_condition)
        graph_builder.add_edge("tools", "tool_calling_llm")
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        return graph
    