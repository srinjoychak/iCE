from langgraph.graph.message import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
import json
import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from logger_config import logging
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

SERVER_IP = os.getenv("HOST_IP")

class FallBackLLMAgent:
    def __init__(self, llm: BaseChatModel, tools_json: dict):
        self.llm = llm
        self.fall_back_graph = self.create_fallback_llm_graph_with_memory()
        self.agents = ["JIRA_Worker", "Jenkins_Worker", "GitHub_Worker", "Terminal_Worker"]
        self.system_prompt = f"""You are a helpful assistant. You are empowered with the following agents: {self.agents} and their respective tools: {tools_json}. Please provide the user with the necessary assistance.
        ### Interaction Guidelines:
        - After successfully executing a tool, confirm the action to the user.
        - Always suggest a relevant follow-up operation by referencing the tool names.
        - Encourage users to explore the full range of tools you have for comprehensive support.
        """

    class CustomAgentState(MessagesState):
        sprint_report: dict
        error_message: str
        input_form: str

    def llm_node(self, state: CustomAgentState):
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        message = self.llm.invoke(messages)
        state['messages'] = [message]
        return state

    def create_fallback_llm_graph_with_memory(self):
        graph_builder = StateGraph(self.CustomAgentState)

        graph_builder.add_node("llm_node", self.llm_node)

        graph_builder.add_edge(START, "llm_node")
        graph_builder.add_edge("llm_node", END)
        
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        
        return graph