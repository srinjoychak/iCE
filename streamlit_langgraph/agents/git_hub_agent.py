from pyexpat.errors import messages
from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
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
import utilities.github.git_hub_utils as git_hub_utils
import utilities.jenkins.jenkins_util as jenkins_util
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from logger_config import logging


load_dotenv()

### Tools for Git Hub Agent Start ###

def register_github_details_form() -> dict:
    """
    This function helps the user in registering GitHub details.
    """
    logging.info("Registering GitHub Details")
    response = {"input_form": "register_github_details_form"}
    return response

def update_or_delete_github_details_form() -> dict:
    """
    This function helps the user in updating or deleting GitHub details.
    """
    logging.info("Updating or Deleting GitHub Details")
    res = git_hub_utils.get_gihub_registration_names()
    logging.info(res)
    if res["status"]:
        response = {"input_form": "update_delete_github_details_form"}
        return response
    else:
        return res

def github_code_search() -> dict:
    """
    This function helps the user in searching for code in a GitHub repository.
    """
    logging.info("Searching for code in a GitHub repository")
    res = git_hub_utils.get_gihub_registration_names()
    logging.info(res)
    if res["status"]:
        response = {"input_form": "github_code_search_form"}
        return response
    else:
        return res

### Tools for Git Hub Agent End ###

class GitHubAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.tools = [github_code_search, register_github_details_form, update_or_delete_github_details_form]
        self.tools_with_forms = ["github_code_search", "register_github_details_form", "update_or_delete_github_details_form"]
        self.llm_with_github = self.llm.bind_tools(self.tools)
        self.github_graph_agent = self.create_github_agent_graph()

    class CustomAgentState(MessagesState):
        error_message: str
        next: str
        input_form: str
                

    def github_tool_calling_llm(self, state: CustomAgentState):
        latest_message = state['messages'][-1]
        if latest_message.name in self.tools_with_forms:
            content_dict = json.loads(latest_message.content)
            if "input_form" in content_dict:
                state['input_form'] = content_dict["input_form"]
        github_system_prompt = f"""You are a helpful assistant with specialized set of tools for GitHub.
        ### Interaction Guidelines:
        - After successfully executing a tool, confirm the action to the user.
        - Always suggest a relevant follow-up operation by referencing the tool names.
        - Encourage users to explore the full range of tools you have for comprehensive support.
        """
        system_message = SystemMessage(content=github_system_prompt)
        messages = self.llm_with_github.invoke([system_message] + state['messages'])
        state['messages'] = [messages]
        return state

    def create_github_agent_graph(self):
        graph_builder = StateGraph(self.CustomAgentState)

        graph_builder.add_node("github_tool_calling_llm", self.github_tool_calling_llm)
        graph_builder.add_node("tools", ToolNode(self.tools))

        graph_builder.add_edge(START, "github_tool_calling_llm")
        graph_builder.add_conditional_edges("github_tool_calling_llm", tools_condition)
        graph_builder.add_edge("tools", "github_tool_calling_llm")
        
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        
        return graph