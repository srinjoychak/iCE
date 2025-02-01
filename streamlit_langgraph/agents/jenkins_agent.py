from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
#from enterprise_llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
import json
import requests
from typing import Literal
from typing_extensions import TypedDict
from IPython.display import Image, display
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import utilities.jenkins.jenkins_util as jenkins_util
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from logger_config import logging

load_dotenv()

### Tools for Jenkins Agent Start ###

def registerJenkinsPipeline() -> dict:
    """
    This function helps the user in registering or configuring a Jenkins pipeline or automation.
    """
    logging.info("Registering Jenkins Pipeline")
    response = {"input_form": "register_jenkins_pipeline_form"}
    return response

def updateOrDeleteJenkinsPipeline() -> dict:
    """
    This function helps the user in updating or deleting a Jenkins pipeline or automation.
    """
    logging.info("Updating or Deleting Jenkins Pipeline")
    res = jenkins_util.get_jenkins_build_name()
    logging.info(res)
    if res["status"]:
        response = {"input_form": "update_delete_jenkins_pipeline_form"}
        return response
    else:
        return res

def executeJenkinsPipeline() -> dict:
    """
    This function helps the user in executing a Jenkins pipeline or automation.
    """
    logging.info("Executing Jenkins Pipeline")
    res = jenkins_util.get_jenkins_build_name()
    logging.info(res)
    if res["status"]:
        response = {"input_form": "execute_jenkins_pipeline_form"}
        return response
    else:
        return res

def getLatestBuildNumber(pipeline_name: str) -> dict:
    """
    This function helps user in getting latest Jenkins build number for a given pipeline or automation.
    """
    logging.info("Getting Latest Build Number")
    return jenkins_util.get_latest_build_no_by_job_name(pipeline_name=pipeline_name)

def select_pipeline_name() -> dict:
    """
    This function helps the user in selecting the Jenkins pipeline name for which they want to retrieve the latest build number.
    """
    logging.info("Selecting Pipeline Name")
    response = {"input_form": "select_pipeline_name_form"}
    return response

def get_stage_wise_execution_status(build_number: int, pipeline_name: str) -> dict:
    """
     Retrieves the stage IDs for a given build number along with stage-wise execution status of a Jenkins pipeline.

    Args:
        build_number (int): The build number of the Jenkins pipeline.
        pipeline_name (str): The name of the Jenkins pipeline.

    Returns:
        dict: A dictionary containing the stage IDs of each stage within the specified build number along with stage-wise execution status.
    """
    logging.info("Getting Execution Status")
    return jenkins_util.get_execution_status(pipeline_name=pipeline_name, build_number=build_number)

def get_execution_info_by_stage_id(build_number: int, pipeline_name: str, stage_id: str) -> dict:
    """
    Retrieves the logs and execution information of each node within a specific stage for a given stage ID and build number of a Jenkins pipeline.

    Args:
        build_number (int): The build number of the Jenkins pipeline.
        pipeline_name (str): The name of the Jenkins pipeline.
        stage_id (str): The ID of the stage to retrieve execution information for.

    Returns:
        dict: A dictionary containing the logs and execution information of each node within the specified stage including node IDs.
    """
    logging.info("Getting Stage Execution Info")
    return jenkins_util.get_stage_execution_info(pipeline_name=pipeline_name, build_number=build_number, stage_id=stage_id)

def get_execution_summary_by_node_id(build_number: int, pipeline_name: str, node_id: str) -> dict:
    """
    Retrieves the execution summary of a specific node for a given node ID and build number of a Jenkins pipeline.

    Args:
        build_number (int): The build number of the Jenkins pipeline.
        pipeline_name (str): The name of the Jenkins pipeline.
        node_id (str): The ID of the node to retrieve execution log for.

    Returns:
        dict: A dictionary containing the execution information of each stageFlowNodes within the specified node including stage flow node IDs.
    """
    logging.info("Getting Node Execution Log")
    return jenkins_util.get_node_execution_log(pipeline_name=pipeline_name, build_number=build_number, node_id=node_id)

def get_execution_log_by_stage_flow_node_id(build_number: int, pipeline_name: str, stage_flow_node_id: str) -> dict:
    """
    Retrieves the execution log of a specific stageFlowNode for a given stageFlowNode ID and build number of a Jenkins pipeline.

    Args:
        build_number (int): The build number of the Jenkins pipeline.
        pipeline_name (str): The name of the Jenkins pipeline.
        stage_flow_node_id (str): The ID of the stageFlowNode to retrieve execution log for.

    Returns:
        dict: A dictionary containing the execution log of the specified stageFlowNode.
    """
    logging.info("Getting Stage Flow Node Execution Log")
    return jenkins_util.get_stage_flow_node_execution_log(pipeline_name=pipeline_name, build_number=build_number, stage_flow_node_id=stage_flow_node_id)

### Tools for Jenkins Agent End ###

class JenkinsAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.tools = [
            executeJenkinsPipeline,
            getLatestBuildNumber,
            get_stage_wise_execution_status,
            registerJenkinsPipeline,
            get_execution_info_by_stage_id,
            get_execution_summary_by_node_id,
            get_execution_log_by_stage_flow_node_id,
            select_pipeline_name,
            updateOrDeleteJenkinsPipeline
        ]
        self.tools_with_forms = ["executeJenkinsPipeline", "registerJenkinsPipeline", "select_pipeline_name", "updateOrDeleteJenkinsPipeline"]
        self.llm_with_jenkins = self.llm.bind_tools(self.tools)
        self.jenkins_graph_agent = self.create_jenkins_graph_agent()

    class CustomAgentState(MessagesState):
        error_message: str
        next: str
        input_form: str

    def jenkins_tool_calling_llm(self, state: CustomAgentState):
        latest_message = state['messages'][-1]
        if latest_message.name in self.tools_with_forms:
            content_dict = json.loads(latest_message.content)
            if "input_form" in content_dict:
                state['input_form'] = content_dict["input_form"]
        jenkins_system_message = """
        You are a helpful assistant with a specialized set of tools for Jenkins.
        ### Interaction Guidelines:
        - After successfully executing a tool, confirm the action to the user.
        - Always suggest a relevant follow-up operation by referencing the tool names.
        - Encourage users to explore the full range of tools you have for comprehensive support.
        """
        system_message = SystemMessage(content=jenkins_system_message)
        message = self.llm_with_jenkins.invoke([system_message] + state['messages'])
        #message = self.llm_with_jenkins.invoke(state['messages'])
        state['messages'] = [message]
        return state

    def create_jenkins_graph_agent(self):
        graph_builder = StateGraph(self.CustomAgentState)

        graph_builder.add_node("jenkins_tool_calling_llm", self.jenkins_tool_calling_llm)
        graph_builder.add_node("tools", ToolNode(self.tools))

        graph_builder.add_edge(START, "jenkins_tool_calling_llm")
        graph_builder.add_conditional_edges("jenkins_tool_calling_llm", tools_condition)
        graph_builder.add_edge("tools", "jenkins_tool_calling_llm")
        # With Memory Saver
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        return graph