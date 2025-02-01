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

### Tools for Terminal Agent Start ###

def invoke_terminal() -> dict:
    """
    This function helps the user in invoking/connecting to the terminal or server.
    """
    logging.info("Invoking the terminal or server")
    response = {"input_form": "invoke_terminal_form"}
    return response

### Tools for Terminal Agent End ###

class TerminalAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.tools = [invoke_terminal]
        self.tools_with_forms = ["invoke_terminal"]
        self.llm_with_github = self.llm.bind_tools(self.tools)
        self.terminal_graph_agent = self.create_terminal_agent_graph()

    class CustomAgentState(MessagesState):
        error_message: str
        next: str
        input_form: str
                

    def terminal_tool_calling_llm(self, state: CustomAgentState):
        latest_message = state['messages'][-1]
        if latest_message.name in self.tools_with_forms:
            content_dict = json.loads(latest_message.content)
            if "input_form" in content_dict:
                state['input_form'] = content_dict["input_form"]
        messages = self.llm_with_github.invoke(state['messages'])
        state['messages'] = [messages]
        return state

    def create_terminal_agent_graph(self):
        graph_builder = StateGraph(self.CustomAgentState)

        graph_builder.add_node("terminal_tool_calling_llm", self.terminal_tool_calling_llm)
        graph_builder.add_node("tools", ToolNode(self.tools))

        graph_builder.add_edge(START, "terminal_tool_calling_llm")
        graph_builder.add_conditional_edges("terminal_tool_calling_llm", tools_condition)
        graph_builder.add_edge("tools", "terminal_tool_calling_llm")
        
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        
        return graph