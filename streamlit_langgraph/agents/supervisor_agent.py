from git import Git
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
from .jira_agent import JiraAgent
from .jenkins_agent import JenkinsAgent
from .fall_back_llm_agent import FallBackLLMAgent
from .terminal_agent import TerminalAgent
from langchain_ollama import ChatOllama
import os
from openai import AuthenticationError
from dotenv import load_dotenv
import llm.llm_provider as llm_provider
from .git_hub_agent import GitHubAgent

load_dotenv()

class CustomAgentState(MessagesState):
    sprint_report: dict
    velocity_report: dict
    burnup_report: dict
    burndown_report: dict
    scrum_report: dict
    error_message: str
    next: str
    input_form: str
    form_data: dict
    chain_of_thought: list

from typing import TypedDict, Literal, List

class Router(TypedDict):
    """
    Worker to route to next. If no workers needed or identified, strictly route to FINISH.
    
    Attributes:
        next: The next worker to route to. Can be one of "JIRA_Worker", "Jenkins_Worker", 
              "GitHub_Worker", "Terminal_Worker", "LLM_Worker", or "FINISH".
        chain_of_thought: A list of strings representing the chain of thought.
    """
    next: Literal["JIRA_Worker", "Jenkins_Worker", "GitHub_Worker", "Terminal_Worker", "LLM_Worker", "FINISH"]
    chain_of_thought: List[str]

class SupervisorAgent:
    def __init__(self):
        self.SERVER_IP = os.getenv("HOST_IP")
        #self.llm = ChatOllama(base_url=f"http://{self.SERVER_IP}:11436", model="llama3.3:latest")
        self.llm = llm_provider.get_llm_by_mode()
        self.jenkins_graph_agent_object = JenkinsAgent(self.llm)
        self.jenkins_graph_agent = self.jenkins_graph_agent_object.jenkins_graph_agent
        self.jira_graph_agent_object = JiraAgent(self.llm)
        self.jira_graph_agent = self.jira_graph_agent_object.jira_graph_agent
        self.github_agent_object = GitHubAgent(self.llm)
        self.github_agent = self.github_agent_object.github_graph_agent
        self.terminal_agent_object = TerminalAgent(self.llm)
        self.terminal_agent = self.terminal_agent_object.terminal_graph_agent
        self.members = ["JIRA_Worker", "Jenkins_Worker", "GitHub_Worker", "Terminal_Worker", "LLM_Worker"]
        self.combined_tools = [self.jira_graph_agent_object.tools, self.jenkins_graph_agent_object.tools, self.github_agent_object.tools, self.terminal_agent_object.tools, []]
        self.tools_json = self.generate_tools_json()
        self.fall_back_graph = FallBackLLMAgent(self.llm, self.tools_json).fall_back_graph
        self.system_prompt = (
            "You are a supervisor tasked with managing a conversation between the"
            " workers. Understand the user input properly, analyze the user intention, and select the appropriate Agent to proceed. If not, provide the proper response."
            " Make sure to select the proper worker based on the prompt, else try to explain the available features."
            f" Following workers: {self.members} with the following set of tools respectively: {self.tools_json}. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH."
            " If the user prompt does not match the available workers, respond accordingly by explaining the available features."
            " Also, keep track of the chain of thoughts you have gone through."
        )
        self.supervisor_graph_agent = self.create_supervisor_graph_agent()

    def generate_tools_json(self):
        tools_json = {}
        for worker, tools in zip(self.members, self.combined_tools):
            tools_json[worker] = []
            for tool in tools:
                tool_info = {
                    "name": tool.__name__,
                    "description": tool.__doc__
                }
                tools_json[worker].append(tool_info)
        return tools_json

    def supervisor_node(self, state: CustomAgentState) -> CustomAgentState:
        if "input_form" in state:
            state["next"] = "__end__"
            return state
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]
        try:
            response = self.llm.with_structured_output(Router).invoke(messages)
        except AuthenticationError as e:
            self.llm = llm_provider.get_llm_by_mode()
            response = self.llm.with_structured_output(Router).invoke(messages)
        print("response", response)
        if response == None:
            next_ = "FINISH"
        else:
            if "chain_of_thought" not in state:
                state["chain_of_thought"] = []
            state["chain_of_thought"].append(response["chain_of_thought"])
            next_ = response["next"]
        if next_ == "FINISH":
            if "next" not in state or state["next"] == "__end__":
                print("Next is LLM worker")
                next_ = "LLM_Worker"
            else:
                print("state['next']", state["next"])
                print("Next is END")
                next_ = "__end__"
        state["next"] = next_
        return state

    def call_jenkins_agent(self, state: CustomAgentState) -> CustomAgentState:
        return self.jenkins_graph_agent.invoke({"messages": state["messages"]})

    def call_jira_agent(self, state: CustomAgentState) -> CustomAgentState:
        return self.jira_graph_agent.invoke({"messages": state["messages"]})
    
    def call_github_agent(self, state: CustomAgentState) -> CustomAgentState:
        return self.github_agent.invoke({"messages": state["messages"]})
    
    def call_terminal_agent(self, state: CustomAgentState) -> CustomAgentState:
        return self.terminal_agent.invoke({"messages": state["messages"]})

    def call_fall_back_agent(self, state: CustomAgentState) -> CustomAgentState:
        return self.fall_back_graph.invoke({"messages": state["messages"]})

    def create_supervisor_graph_agent(self):
        supervisor_builder = StateGraph(CustomAgentState)

        # Add the supervisor node
        supervisor_builder.add_node("supervisor", self.supervisor_node)

        # Add the agent calls
        supervisor_builder.add_node("Jenkins_Worker", self.call_jenkins_agent)
        supervisor_builder.add_node("JIRA_Worker", self.call_jira_agent)
        supervisor_builder.add_node("GitHub_Worker", self.call_github_agent)
        supervisor_builder.add_node("LLM_Worker", self.call_fall_back_agent)
        supervisor_builder.add_node("Terminal_Worker", self.call_terminal_agent)

        # Define the control flow
        supervisor_builder.add_edge(START, "supervisor")
        supervisor_builder.add_conditional_edges("supervisor", lambda state: state["next"])
        supervisor_builder.add_edge("Jenkins_Worker", "supervisor")
        supervisor_builder.add_edge("JIRA_Worker", "supervisor")
        supervisor_builder.add_edge("GitHub_Worker", "supervisor")
        supervisor_builder.add_edge("Terminal_Worker", "supervisor")
        supervisor_builder.add_edge("LLM_Worker", "supervisor")

        # Compile the supervisor graph
        supervisor_graph = supervisor_builder.compile(checkpointer=MemorySaver())
        return supervisor_graph

# Instantiate the SupervisorAgent
supervisor_graph_agent = SupervisorAgent().supervisor_graph_agent


def get_new_supervisor_graph_agent():
    global supervisor_graph_agent
    supervisor_graph_agent = SupervisorAgent().supervisor_graph_agent
    return supervisor_graph_agent