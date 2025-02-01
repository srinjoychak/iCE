import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agents.supervisor_agent import supervisor_graph_agent, get_new_supervisor_graph_agent
from utilities.thread_util import getConfig, new_thread
from utilities.jira.jira_util import switch_project_to_other_project, updating_primary_project, save_jira_project, get_epics_drop_down_values, create_jira_issue, get_issues_by_assignee, add_worklog, get_all_issues, register_jira_details
import utilities.jenkins.jenkins_util as jenkins_util
import os
from dotenv import load_dotenv
from logger_config import logging
import openai
from utilities.utilities import time_to_seconds, get_user_details
import json
from rag_fusion.rag_fusion import rag_fusion
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import datetime
from markdown2 import markdown
import utilities.github.git_hub_utils as git_hub_utils
import paramiko
import threading
from queue import Queue
import socket
import time
import traceback
user_icon = '<i class="fas fa-user user-icon"></i>'  # FontAwesome user icon (white)
bot_icon = "🤖"  # bot icon (for the bot's response)

load_dotenv()
email = os.getenv("EMAIL")
if email is not None:
    user_name = email.split("@")[0]
else:
    email, user_name = get_user_details()

welcome_message = "Welcome to iCE, your go-to assistant for managing JIRA projects and Jenkins pipelines. From creating JIRA issues to getting the latest build numbers, I've got you covered. Let's get started!"

st.markdown(
    """
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <style>
        .user-icon {
            color: #2879ff;
            padding-right: 6px;
        }
        # .bot-icon {
        #     color: #f39c12;  /* Yellow-orange for the bot icon */
        # }
        .chat-container {
            width: 100%;
            overflow: hidden;
        }
        .title {
            white-space: nowrap;
            font-size: 38px;
            font-weight: 600;
        }
        .user-message-container {
            display: block;
            justify-content: flex-end; /* Aligns the entire message container to the right */
            align-items: center; /* Vertically centers the icon with the message */
        }
        # .bot-message-container {
        #     display: block;
        #     justify-content: flex-start; /* Aligns the bot message and icon to the left */
        #     align-items: flex-start; /* Vertically centers the icon with the message */
        # }
        .user-message {
            background-color: #f0f0f0;    /* Light gray background for user messages */
            color: #000000;               /* Black text */
            border-radius: 20px;          /* Rounded corners */
            padding: 10px 15px;           /* Padding inside the bubble */
            margin: 10px 0;               /* Space between messages */
            max-width: 60%;               /* Limit the width of the message bubble */
            word-wrap: break-word;        /* Break long words */
            text-align: right;            /* Align text inside the bubble to the right */
            clear: both;                  /* Clear floats to prevent overlap */
            float: none;
        }
       .bot-message {
            background-color: #fff9c4;  /* Light yellow background */
            color: #000;               /* Black text */
            border-radius: 15px;
            padding: 10px 15px;
            margin: 10px 0;
            max-width: 100%;
            word-wrap: break-word;
            text-align: left;
            # white-space: pre-wrap;     /* Preserve line breaks and spaces */
            # box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .clearfix {
            clear: both;                  /* Ensure no overlap between floats */
        }
        .timestamp {
            font-size: 0.8em;
            color: #999999;
            margin-top: 5px;
            display: block;
        }
        /* Optional: Add some padding to the whole chat area */
        .chat-wrapper {
            padding: 20px;
        }
       
    </style>
    """,
    unsafe_allow_html=True,
)

# st.markdown(
#         '<h4 class="title">Welcome to iCE (intelligent Copilot Engine)</h4>',
#         unsafe_allow_html=True,
# )

# Queue to store terminal output
output_queue = Queue()
# def showChainOfThoughts(text_blocks):
#     toggle = st.toggle("Chain of thoughts")
#     print(toggle)
#     if not toggle:
#         print("inside the if confition=======")
#         cols = st.columns(2)  # Adjust the number of columns as needed

#         for i, block in enumerate(text_blocks):
#             with cols[i % 2]:  # Distribute across columns
#                 st.markdown("- " + block)


# Global flag to stop the command execution thread

# Function to execute commands on the virtual machine

def initialize_session_state(welcome_message):
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append(AIMessage(content=welcome_message))

    if 'display_switch_jira_project_form' not in st.session_state:
        st.session_state.display_switch_jira_project_form = False

    if 'display_execute_jenkins_pipeline_form' not in st.session_state:
        st.session_state.display_execute_jenkins_pipeline_form = False

    if 'display_register_jenkins_pipeline_form' not in st.session_state:
        st.session_state.display_register_jenkins_pipeline_form = False

    if 'display_register_jira_project_form' not in st.session_state:
        st.session_state.display_register_jira_project_form = False

    if 'display_create_jira_issue_form' not in st.session_state:
        st.session_state.display_create_jira_issue_form = False

    if 'display_get_my_jira_issues_form' not in st.session_state:
        st.session_state.display_get_my_jira_issues_form = False

    if 'display_get_current_sprint_issues_form' not in st.session_state:
        st.session_state.display_get_current_sprint_issues_form = False
    
    if 'display_github_code_search_form' not in st.session_state:
        st.session_state.display_github_code_search_form = False

    if 'display_register_jira_details_form' not in st.session_state:
        st.session_state.display_register_jira_details_form = False

    if 'display_register_github_details_form' not in st.session_state:
        st.session_state.display_register_github_details_form = False
    
    if 'display_invoke_terminal_form' not in st.session_state:
        st.session_state.display_invoke_terminal_form = False

    if 'display_select_pipeline_name_form' not in st.session_state:
        st.session_state.display_select_pipeline_name_form = False
    
    if 'display_update_delete_jenkins_pipeline_form' not in st.session_state:
        st.session_state.display_update_delete_jenkins_pipeline_form = False

    if 'display_update_delete_github_details_form' not in st.session_state:
        st.session_state.display_update_delete_github_details_form = False

    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = 1

    # Initialize session state for form submission
    if 'form_counter' not in st.session_state:
        st.session_state['form_counter'] = 0

    if 'form_data' not in st.session_state:
        st.session_state['form_data'] = None

# Function to add an AI message to a specific thread
def add_ai_message_to_thread(graph, thread_id, ai_message_content):
    # Get the current state of the thread
    current_state = graph.get_state(thread_id)
    state_values = current_state.values

    # Create a new AI message
    ai_message = AIMessage(content=ai_message_content)
    
    # Append the new AI message to the existing messages
    current_messages = state_values.get("messages", [])
    current_messages.append(ai_message)
    
    # Update the thread state with the new messages
    graph.update_state(thread_id, {"messages": current_messages})

def handle_response_with_llm(res):
    try:
        ai_message = AIMessage(content=res["data"])
        response = invoke_supervisor_agent(ai_message)
        state_snapshot = supervisor_graph_agent.get_state(getConfig(st.session_state.thread_id))
        state_values = state_snapshot.values
        chain_of_thought = state_values.get('chain_of_thought', [])
        logging.info(f"Chain of thought: {chain_of_thought}")
        ai_message = response['messages'][-1]
        st.session_state.chat_history.append(ai_message)
    except openai.RateLimitError as e:
        logging.error(f"Rate limit error: {e}")
        ai_message = AIMessage(content="Rate limit exceeded. Please try again later.")
        st.session_state.chat_history.append(ai_message)
    except openai.AuthenticationError as e:
        logging.error(f"Authentication error: {e}")
        ai_message = AIMessage(content="Authentication error. Error: " + str(e) + " New session started.")
        st.session_state.chat_history.append(ai_message)
        get_new_supervisor_graph_agent()
    except Exception as e:
        logging.error(f"Error invoking Supervisor Agent. Stack trace: {traceback.format_exc()}")
        ai_message = AIMessage(content="Something went wrong. Please try again.")
        st.session_state.chat_history.append(ai_message)

def switch_project(selected_value):
    logging.info(f"Switching to project: {selected_value}")
    updating_primary_project(user_name, selected_value)
    logging.info("Updated Primary Project")
    st.write(f"Switched to project {selected_value}.")

def construct_switch_project_form(form_key, dropdown_values):
    with st.chat_message("assistant"):
        with st.form(key=form_key, border=True):
            st.write("Select the project you want to switch to:")
            selected_value = st.selectbox("Select Project:", dropdown_values)
            submit_button = st.form_submit_button("Submit")
            if submit_button:
                switch_project(selected_value)
                return handle_response_with_llm({"data": f"Switched to project {selected_value}."})

def construct_jenkins_build_form(pipeline_name, form_key):
    with st.chat_message("assistant"):
        with st.form(key=form_key, border=True):
            st.write("Select the automation you want to execute and provide the branch:")
            selected_pipeline = st.selectbox("Automation to execute:", pipeline_name)
            branch = st.text_input("Branch:")
            submit_button = st.form_submit_button("Submit")
            if submit_button:
                logging.info(f"branch{branch}")
                logging.info(f"selected_build_name{selected_pipeline}")
                res = jenkins_util.execute_jenkins_build(branch, selected_pipeline)
                logging.info(f"res{res}")
                return handle_response_with_llm(res)

def construct_register_jenkins_pipeline_form(form_key):
    with st.chat_message("assistant"):
        info = """
                To obtain the URL for remote triggering, follow these steps:
                1. Open the pipeline and click "Configure."
                2. Under "Build Triggers," enable "Trigger builds remotely."
                3. Enter an "Authentication Token."
                4. Follow the example URL provided for remote triggering.
                """
        with st.form(key=form_key, border=True):
            st.info(info)
            st.write("Register a new automation:")
            pipeline_name = st.text_input("Name:")
            pipeline_description = st.text_area("Description:")
            jenkins_url = st.text_input("URL:")
            user = st.text_input("User:")
            token = st.text_input("Token:", type="password")
            submit_button = st.form_submit_button("Register")
            if submit_button:
                res = jenkins_util.save_jenkins_pipeline_details(pipeline_name, pipeline_description, jenkins_url, user, token)
                logging.info(f"res{res}")
                return handle_response_with_llm(res)

def construct_register_jira_project_form(form_key):
    with st.chat_message("assistant"):
        with st.form(key=form_key, border=True):
            st.write("Register a new JIRA project:")
            project_url = st.text_input("Backlog URL")
            submit_button = st.form_submit_button("Register Project")
            if submit_button:
                logging.info(f"project_url{project_url}")
                res = save_jira_project(project_url, user_name)
                logging.info(f"res{res}")
                if res["success"] == False or res["success"] == "False":
                    return handle_response_with_llm(res)
                else:
                    return handle_response_with_llm({"data": "JIRA Project registered successfully."})

def construct_create_jira_issue_form(form_key, epics, form_data=None):
    with st.chat_message("assistant"):
        with st.form(key=form_key, border=True):
            st.write("Create a new JIRA issue:")

            issue_summary = st.text_input(
                "Issue Summary", 
                value=form_data.get("issue_summary", "") if form_data else ""
            )
            issue_desc = st.text_area(
                "Issue Description", 
                value=form_data.get("issue_desc", "") if form_data else ""
            )
            acceptance_criteria = st.text_area(
                "Acceptance Criteria", 
                value=form_data.get("acceptance_criteria", "") if form_data else ""
            )

            epic_key, epic_data = epics[0], epics[1]
            issue_type = st.selectbox("Issue Type:", ["Task", "Bug", "Story"])
            if len(epic_data) == 0 and len(epic_key) == 0:
                epic_key = st.selectbox(
                    "Epic Key",
                    ["No Epic Found"],
                )
            else:
                epic_key = st.selectbox("Epic Key", epic_key)
                epic_key = epic_data[epic_key]
            submit_button = st.form_submit_button("Create Issue")
            if submit_button:
                logging.info(f"{epic_key}{issue_type}")
                res = create_jira_issue(
                    user_name,
                    issue_summary,
                    issue_desc,
                    acceptance_criteria,
                    issue_type,
                    epic_key,
                )
                logging.info(f"res{res}")
                return handle_response_with_llm(res)

def construct_get_jira_issues_form(form_key, filter_data, select_box_key):
    with st.chat_message("assistant"):
        st.write("Select the issue you want to view:")
        selected_issue = st.selectbox("Select Issue:", list(filter_data.keys()), key=select_box_key)
        if selected_issue in filter_data:
            issue = filter_data[selected_issue]
            with st.form(key=form_key, border=True):
                st.markdown(
                    f"<span style='color: black;'>User Story ID: </span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='color: blue;'>{selected_issue}</span>", unsafe_allow_html=True
                )
                st.markdown(
                    f"<span style='color: black;'>Issue Type: </span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='color: blue;'>{issue['Issue_Type']}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='color: black;'>User Story Summary: </span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='color: blue;'>{issue['Summary']}</span>",
                    unsafe_allow_html=True,
                )
                st.write("User Story Description : ")
                st.markdown(
                    f"<span style='color: green;'>{issue['Description']}</span>",
                    unsafe_allow_html=True,
                )
                comment = st.text_input(
                    f"Worklog Comment for {selected_issue}", placeholder="Add Worklog Comment"
                )
                hours = st.text_input(
                    f"Worklog Hours for {selected_issue}",
                    placeholder="Add Worklog Duration(e.g. 2h 30m)",
                )
                submit_button = st.form_submit_button(label="Submit")
                if submit_button:
                    print("Form Submitted")
                    worklog_hours = time_to_seconds(hours)
                    payload = {
                        "user_name": user_name,
                        "issue_key": selected_issue,
                        "comment": comment,
                        "worklog_comment": " ",
                        "worklog_duration": worklog_hours,
                    }
                    logging.info(f"payload {payload}")
                    res = add_worklog(user_name, payload)
                    logging.info(f"res{res}")
                    response_json = json.loads(res.text)
                    if (response_json["success"] == "true"or response_json["success"] == True):
                        return handle_response_with_llm({"data": f"{selected_issue} updated successfully."})
                    else:
                        return handle_response_with_llm({"data": f"Failed to update {selected_issue}."})

def construct_github_code_search_form(form_key, filter_data, select_box_key):
    logging.info("Constructing GitHub code search form")
    with st.chat_message("assistant"):
        selected_git = st.selectbox("Choose the Git Registration:", list(filter_data.keys()), key=select_box_key)
        if selected_git in filter_data:
            git = filter_data[selected_git]
            with st.form(key=form_key, border=True):
                key_word = st.text_input("Keyword to search")
                extension = st.text_input("Extension to search (e.g. .py, .java)")
                submit_button = st.form_submit_button("Search")
                if submit_button:
                    logging.info(f"key_word{key_word}")
                    logging.info(f"extension{extension}")
                    if extension is None:
                        extension = ""
                    res = git_hub_utils.search_code_in_github(git, key_word, extension)
                    logging.info(f"res{res}")
                    return handle_response_with_llm(res)
    
def construct_register_jira_details_form(form_key):
    logging.info("Constructing JIRA details form")
    with st.chat_message("assistant"):
        with st.form(key=form_key, border=True):
            st.write("Please provide the following JIRA details to enable JIRA features:")
            global email, user_name
            if email is None:
                email = st.text_input("Email")
            else:
                email = st.text_input("Email", value=email, disabled=True)
            jira_token = st.text_input("JIRA Token", type="password")
            submit_button = st.form_submit_button("Submit")
            if submit_button:
                logging.info("Submitting JIRA details")
                logging.info(f"email{email}")
                logging.info(f"jira_token{jira_token}")
                isRegistered = register_jira_details(email, jira_token)
                if isRegistered:
                    return handle_response_with_llm({"data": "JIRA details registered successfully. Do you want register your first project?"})
                else:
                    return handle_response_with_llm({"data": "Failed to register JIRA details. Please try again."})
                    
def construct_register_github_details_form(form_key, toggle_key):
    logging.info("Constructing GitHub details form")
    with st.chat_message("assistant"):
        selected_git_source = st.toggle("Enterprise GitHub?", False, key=toggle_key)
        with st.form(key=form_key, border=True):
            st.write("Provide the following GitHub details to enable GitHub features:")
            git_name = st.text_input("Reference Name")
            if selected_git_source:
                info =  """
                        If you are using GitHub Enterprise, the base_url will be different and will typically follow this pattern: 
                        https://[hostname]/api/v3
                        """
                st.info(info)
                git_url = st.text_input("GitHub URL")
            else:
                git_url = "https://api.github.com"
            git_username = st.text_input("GitHub Username")
            git_token = st.text_input("GitHub Token", type="password")
            submit_button = st.form_submit_button("Submit")
            if submit_button:
                logging.info("Submitting GitHub details")
                logging.info(f"git_url{git_url}")
                logging.info(f"git_username{git_username}")
                res = git_hub_utils.save_github_details(git_name, git_url, git_username, git_token)
                logging.info(f"res{res}")
                return handle_response_with_llm(res)


def construct_invoke_terminal_form(form_key):
    if "output" not in st.session_state:
        st.session_state.output = ""

    if "ssh_client" not in st.session_state:
        st.session_state.ssh_client = None

    with st.chat_message("assistant"):
        with st.form(key=form_key, border=True):
            host = st.text_input("Host")
            port = st.number_input("Port", value=22,)  # Port input
            username = st.text_input("Username", )
            password = st.text_input("Password", type="password")
            col1, col2, col3 = st.columns(3)
    
            with col1:
                connectButton = st.form_submit_button("Connect to VM")

            with col2:
                executeButton = st.form_submit_button("Execute Command")

            with col3:
                terminateButton = st.form_submit_button("Terminate Session")

            if connectButton:
                if host and port and username and password:
                    try:
                        ssh_client = paramiko.SSHClient()
                        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh_client.connect(hostname=host, port=port, username=username, password=password)
                        st.session_state.ssh_client = ssh_client  # Store the SSH client in session state
                        st.success("Connected to VM successfully!")
                    except paramiko.AuthenticationException:
                        st.error("Authentication failed. Please check your username and password.")
                    except paramiko.SSHException as e:
                        st.error(f"SSH connection failed: {e}")
                    except paramiko.socket.error as e:
                        st.error(f"Network error: {e}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                else:
                    st.warning("Please provide all required credentials.")
            
            if st.session_state.ssh_client:
                command = st.text_input("Enter command to execute on VM", placeholder="e.g., ls -l")

                if executeButton:
                    if command:
                        try:
                            stdin, stdout, stderr = st.session_state.ssh_client.exec_command(command)
                            output = stdout.read().decode()
                            error = stderr.read().decode()
                            # Handle no output case
                            if not output and not error:
                                output = "No output returned. The command may have completed with no results."
                            # Append the new output to the previous content
                            st.session_state.output += f"Accessing: {host}:{port}...\n{'-'*100}"
                            st.session_state.output += f"\nCommand: {command}\n{output}\n{error}\n{'-'*100}"
                            add_ai_message_to_thread(supervisor_graph_agent, getConfig(st.session_state.thread_id), st.session_state.output)  
                            # Display the appended content in the text area
                            st.text_area("Command Output", st.session_state.output, height=400)
                        except Exception as e:
                            st.error(f"Error executing command: {e}")
                    else:
                        st.warning("Please enter a command.")

          

            if terminateButton:
                    st.session_state.ssh_client.close()
                    st.session_state.ssh_client = None
                    # st.session_state.vm_output = ""  # Reset output on session termination
                    st.success("SSH session terminated successfully!")

    # st.text_area("Command Output", st.session_state.output, height=400)
      
    #                 add_ai_message_to_thread(supervisor_graph_agent, getConfig(st.session_state.thread_id), output_buffer)             

def construct_select_pipeline_name_form(form_key, dropdown_values):
    with st.chat_message("assistant"):
        with st.form(key=form_key, border=True):
            st.write("Select the pipeline:")
            selected_pipeline = st.selectbox("Pipeline:", dropdown_values)
            submit_button = st.form_submit_button("Submit")
            if submit_button:
                logging.info(f"selected_pipeline{selected_pipeline}")
                handle_response_with_llm({"data": f"Selected pipeline: {selected_pipeline}"})

def construct_update_delete_jenkins_pipeline_form(form_key, data, select_box_key):
    with st.chat_message("assistant"):
        st.write("Select the pipeline you want to update or delete:")
        selected_pipeline = st.selectbox("Select Pipeline:", list(data.keys()), key=select_box_key)
        if selected_pipeline in data:
            pipeline = data[selected_pipeline]
            with st.form(key=form_key, border=True):
                pipeline_description = st.text_area("Description", value=pipeline["pipeline_description"])
                jenkins_url = st.text_input("URL", value=pipeline["jenkins_url"])
                user = st.text_input("User", value=pipeline["user"])
                token = st.text_input("Token", value=pipeline["token"], type="password")
                submit_button = st.form_submit_button("Update")
                delete_button = st.form_submit_button("Delete")
                if submit_button:
                    logging.info(f"selected_pipeline{selected_pipeline}")
                    res = jenkins_util.update_jenkins_pipeline_details(selected_pipeline, pipeline_description, jenkins_url, user, token)
                    logging.info(f"res{res}")
                    return handle_response_with_llm(res)
                if delete_button:
                    logging.info(f"selected_pipeline{selected_pipeline}")
                    res = jenkins_util.delete_jenkins_pipeline(selected_pipeline)
                    logging.info(f"res{res}")
                    return handle_response_with_llm(res)
                
def construct_update_delete_github_details_form(form_key, data, select_box_key):
    with st.chat_message("assistant"):
        st.write("Select the Git Registration you want to update or delete:")
        selected_git = st.selectbox("Select Git Registration:", list(data.keys()), key=select_box_key)
        if selected_git in data:
            git = data[selected_git]
            with st.form(key=form_key, border=True):
                git_url = st.text_input("URL", value=git["git_url"])
                git_username = st.text_input("Username", value=git["git_username"])
                git_token = st.text_input("Token", value=git["git_token"], type="password")
                submit_button = st.form_submit_button("Update")
                delete_button = st.form_submit_button("Delete")
                if submit_button:
                    logging.info(f"selected_git{selected_git}")
                    res = git_hub_utils.update_github_details(selected_git, git_url, git_username, git_token)
                    logging.info(f"res{res}")
                    return handle_response_with_llm(res)
                if delete_button:
                    logging.info(f"selected_git{selected_git}")
                    res = git_hub_utils.delete_github_details(selected_git)
                    logging.info(f"res{res}")
                    return handle_response_with_llm(res)
                
def show_switch_project_form():
    project_data = switch_project_to_other_project(user_name)
    if project_data == "No Project Found":
        ai_message = AIMessage(content="No project found. Please register a project first.")
        st.session_state.chat_history.append(ai_message)
        # st.chat_message("assistant").write(ai_message.content)
        st.markdown(
                        f"""
                        <div class="chat-container" style="display: flex; align-items: flex-start;">
                            <span class="bot-icon">{bot_icon}</span>
                            <div class="bot-message">
                                {ai_message.content}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                )
    else:
        dropdown_values = project_data[0]
        form_key = f"switch_jira_project_form_{st.session_state['form_counter']}"
        st.session_state['form_counter'] += 1
        construct_switch_project_form(form_key, dropdown_values)
        form_object = { "form_key": form_key, "form_type": "switch_jira_project_form", "dropdown_values": dropdown_values }
        st.session_state.chat_history.append(form_object)
        st.session_state.display_switch_jira_project_form = False

def show_execute_jenkins_pipeline_form():
    res = jenkins_util.get_jenkins_build_name()
    if res["status"]:
        pipeline_name = res["data"]
        form_key = f"execute_jenkins_pipeline_form_{st.session_state['form_counter']}"
        st.session_state['form_counter'] += 1
        construct_jenkins_build_form(pipeline_name, form_key)
        form_object = { "form_key": form_key, "form_type": "execute_jenkins_pipeline_form", "dropdown_values": pipeline_name  }
        st.session_state.chat_history.append(form_object)
        st.session_state.display_execute_jenkins_pipeline_form = False
    else:
        ai_message = AIMessage(content=res["data"])
        st.session_state.chat_history.append(ai_message)
        st.chat_message("assistant").write(ai_message.content)
        st.session_state.display_execute_jenkins_pipeline_form = False

def show_register_jenkins_pipeline_form():
    form_key = f"register_jenkins_pipeline_form_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    construct_register_jenkins_pipeline_form(form_key)
    form_object = { "form_key": form_key, "form_type": "register_jenkins_pipeline_form" }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_register_jenkins_pipeline_form = False

def show_register_jira_project_form():
    form_key = f"register_jira_project_form_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    construct_register_jira_project_form(form_key)
    form_object = { "form_key": form_key, "form_type": "register_jira_project_form" }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_register_jira_project_form = False

def show_create_jira_issue_form():
    form_key = f"create_jira_issue_form_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    epics = get_epics_drop_down_values(user_name)
    form_data = st.session_state['form_data']
    construct_create_jira_issue_form(form_key, epics, form_data)
    form_object = { "form_key": form_key, "form_type": "create_jira_issue_form", "epics": epics, "form_data": form_data }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_create_jira_issue_form = False

def show_get_my_jira_issues_form():
    form_key = f"get_my_jira_issues_form_{st.session_state['form_counter']}"
    select_box_key = f"get_my_jira_issues_select_box_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    filter_data = get_issues_by_assignee(user_name)
    construct_get_jira_issues_form(form_key, filter_data, select_box_key)
    form_object = { "form_key": form_key, "form_type": "get_my_jira_issues_form", "filter_data": filter_data, "select_box_key": select_box_key }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_get_my_jira_issues_form = False

def show_get_current_sprint_issues_form():
    form_key = f"get_current_sprint_issues_form_{st.session_state['form_counter']}"
    select_box_key = f"get_current_sprint_issues_select_box_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    data = get_all_issues(user_name)
    construct_get_jira_issues_form(form_key, data, select_box_key)
    form_object = { "form_key": form_key, "form_type": "get_current_sprint_issues_form", "filter_data": data, "select_box_key": select_box_key }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_get_current_sprint_issues_form = False

def show_github_code_search_form():
    logging.info("Showing GitHub code search form")
    form_key = f"github_code_search_form_{st.session_state['form_counter']}"
    select_box_key = f"github_code_search_select_box_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    data = git_hub_utils.get_github_details()
    if data["status"]:
        construct_github_code_search_form(form_key, data["data"], select_box_key)
        form_object = { "form_key": form_key, "form_type": "github_code_search_form", "filter_data": data["data"], "select_box_key": select_box_key }
        st.session_state.chat_history.append(form_object)
        st.session_state.display_github_code_search_form = False
    else:
        ai_message = AIMessage(content=data["data"])
        st.session_state.chat_history.append(ai_message)
        st.chat_message("assistant").write(ai_message.content)
        st.session_state.display_github_code_search_form = False

def show_register_jira_details_form():
    form_key = f"register_jira_details_form_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    construct_register_jira_details_form(form_key)
    form_object = { "form_key": form_key, "form_type": "register_jira_details_form" }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_register_jira_details_form = False

def show_register_github_details_form():
    form_key = f"register_github_details_form_{st.session_state['form_counter']}"
    toggle_key = f"register_github_details_toggle_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    construct_register_github_details_form(form_key, toggle_key)
    form_object = { "form_key": form_key, "form_type": "register_github_details_form", "toggle_key": toggle_key }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_register_github_details_form = False

def show_invoke_terminal_form():
    form_key = f"invoke_terminal_form_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    construct_invoke_terminal_form(form_key)
    form_object = { "form_key": form_key, "form_type": "invoke_terminal_form" }
    st.session_state.chat_history.append(form_object)
    st.session_state.display_invoke_terminal_form = False

def show_select_pipeline_name_form():
    form_key = f"select_pipeline_name_form_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    res = jenkins_util.get_jenkins_build_name()
    if res["status"]:
        pipeline_name = res["data"]
        construct_select_pipeline_name_form(form_key, pipeline_name)
        form_object = { "form_key": form_key, "form_type": "select_pipeline_name_form", "dropdown_values": pipeline_name  }
        st.session_state.chat_history.append(form_object)
        st.session_state.display_select_pipeline_name_form = False
    else:
        ai_message = AIMessage(content=res["data"])
        st.session_state.chat_history.append(ai_message)
        st.chat_message("assistant").write(ai_message.content)
        st.session_state.display_select_pipeline_name_form = False

def show_update_delete_jenkins_pipeline_form():
    form_key = f"update_delete_jenkins_pipeline_form_{st.session_state['form_counter']}"
    select_box_key = f"update_delete_jenkins_pipeline_select_box_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    data = jenkins_util.get_all_jenkins_pipelines()
    if data["status"]:
        construct_update_delete_jenkins_pipeline_form(form_key, data["data"], select_box_key)
        form_object = { "form_key": form_key, "form_type": "update_delete_jenkins_pipeline_form", "filter_data": data["data"], "select_box_key": select_box_key  }
        st.session_state.chat_history.append(form_object)
        st.session_state.display_update_delete_jenkins_pipeline_form = False
    else:
        ai_message = AIMessage(content=data["data"])
        st.session_state.chat_history.append(ai_message)
        st.chat_message("assistant").write(ai_message.content)
        st.session_state.display_update_delete_jenkins_pipeline_form = False

def show_update_delete_github_details_form():
    form_key = f"update_delete_github_details_form_{st.session_state['form_counter']}"
    select_box_key = f"update_delete_github_details_select_box_{st.session_state['form_counter']}"
    st.session_state['form_counter'] += 1
    data = git_hub_utils.get_github_details()
    if data["status"]:
        construct_update_delete_github_details_form(form_key, data["data"], select_box_key)
        form_object = { "form_key": form_key, "form_type": "update_delete_github_details_form", "filter_data": data["data"], "select_box_key": select_box_key  }
        st.session_state.chat_history.append(form_object)
        st.session_state.display_update_delete_github_details_form = False
    else:
        ai_message = AIMessage(content=data["data"])
        st.session_state.chat_history.append(ai_message)
        st.chat_message("assistant").write(ai_message.content)
        st.session_state.display_update_delete_github_details_form = False

def show_form(input_form):
    if input_form == "switch_jira_project_form":
        st.session_state.display_switch_jira_project_form = True
    elif input_form == "execute_jenkins_pipeline_form":
        st.session_state.display_execute_jenkins_pipeline_form = True
    elif input_form == "register_jenkins_pipeline_form":
        st.session_state.display_register_jenkins_pipeline_form = True
    elif input_form == "register_jira_project_form":
        st.session_state.display_register_jira_project_form = True
    elif input_form == "create_jira_issue_form":
        st.session_state.display_create_jira_issue_form = True
    elif input_form == "get_my_jira_issues_form":
        st.session_state.display_get_my_jira_issues_form = True
    elif input_form == "get_current_sprint_issues_form":
        st.session_state.display_get_current_sprint_issues_form = True
    elif input_form == "github_code_search_form":
        st.session_state.display_github_code_search_form = True
    elif input_form == "register_jira_details_form":
        st.session_state.display_register_jira_details_form = True
    elif input_form == "register_github_details_form":
        st.session_state.display_register_github_details_form = True
    elif input_form == "invoke_terminal_form":
        # Check if isTerminateSession is False before displaying the form
        # if st.session_state.get("isTerminated", False):
        #     st.session_state.display_invoke_terminal_form = False
        #     print("Session is already terminated. Not displaying the terminal form.")
        # else:
        #     print("inside the else statement=====.")
        st.session_state.display_invoke_terminal_form = True
    elif input_form == "select_pipeline_name_form":
        st.session_state.display_select_pipeline_name_form = True
    elif input_form == "update_delete_jenkins_pipeline_form":
        st.session_state.display_update_delete_jenkins_pipeline_form = True
    elif input_form == "update_delete_github_details_form":
        st.session_state.display_update_delete_github_details_form = True
        

def prepare_velocity_chart_and_table(data, ai_message_content, toggle_key):
    # Convert JSON data to a DataFrame
    def json_to_dataframe(data):
        records = []
        for sprint, details in data.items():
            record = {
                'Sprint': sprint,
                'Sprint Goal': details.get('Sprint_Goal', ''),
                'Completed Story Points': details.get('Completed_Issues_Story_Points', 0.0),
                'Estimated Story Points': details.get('Estimated_Story_Points', 0.0),
                'Issues in Sprint': ', '.join(details.get('Issues in Sprint', [])),  # Convert list to string
            }
            records.append(record)
        return pd.DataFrame(records)

    df = json_to_dataframe(data)
    df.index = df.index + 1
    # Verify and adjust for missing columns
    required_columns = ['Key', 'Status', 'Summary', 'Assignee', 'Total Worklog Effort (hours)']
    for col in required_columns:
        if col not in df.columns:
            df[col] = None  # Add missing columns with default values

    with st.chat_message("assistant"):
        show_ai_message = st.toggle("Show Report Summary", value=False, key=toggle_key)
        if show_ai_message:
            st.write(ai_message_content)
        else:
            # Display the DataFrame as a table
            st.title("Velocity Report - Table View")
            st.dataframe(df)

            # Create a chart for story points
            st.title("Velocity Report - Chart View")
            chart_data = df[['Sprint', 'Completed Story Points', 'Estimated Story Points']].set_index('Sprint')
            st.bar_chart(chart_data)



def prepare_burnup_chart_and_table(data):
    # Display the chart
    st.subheader(f"Burnup Chart - {data['sprint_name']}")
    def generate_burnup_chart(data):
        start_date = datetime.datetime.strptime(data["startDate"], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(data["endDate"], "%Y-%m-%d")

        # Generate a date range for the sprint
        date_range = pd.date_range(start=start_date, end=end_date)

        # Calculate cumulative story points completed
        total_story_points = sum(
            item[2]["story_points"] or 0 for item in data.values() if isinstance(item, list)
        )
        completed_points = [0]  # Start with zero completed
        cumulative_points = 0

        for current_date in date_range:
            for key, value in data.items():
                if isinstance(value, list) and value[1]["closed_date"]:
                    closed_date = datetime.datetime.strptime(
                        value[1]["closed_date"], "%Y-%m-%d"
                    )
                    if closed_date <= current_date:
                        cumulative_points += value[2]["story_points"] or 0
            completed_points.append(cumulative_points)

        # Total work scope is constant
        total_scope = [total_story_points] * len(date_range)

        # Burnup DataFrame
        df = pd.DataFrame(
            {
                "Date": date_range,
                "Work Completed": completed_points[:-1],  # Exclude extra point
                "Total Scope": total_scope,
            }
        )
        return df
    df = generate_burnup_chart(data)
    fig = px.line(
        df,
        x="Date",
        y=["Work Completed", "Total Scope"],
        markers=True,
        title=f"Burnup Chart - {data['sprint_name']}",
        labels={"value": "Story Points", "Date": "Sprint Day"},
        template="plotly_dark",
    )
    st.plotly_chart(fig)

    # Display the table
    st.subheader("Burnup Table View")
    table_data = []
    for key, value in data.items():
        if isinstance(value, list):
            issue_summary = value[0].get("issue_summary", "N/A")
            closed_date = value[1].get("closed_date", "N/A")
            story_points = value[2].get("story_points", "N/A")
            table_data.append([key, issue_summary, closed_date, story_points])

    df_table = pd.DataFrame(
        table_data, columns=["Issue ID", "Issue Summary", "Closed Date", "Story Points"]
    )
    df_table.index = df_table.index + 1
    st.table(df_table)

def prepare_burndown_chart_and_table(data):
    # Function to map hours to story points (you may adjust the logic)
    def hours_to_story_points(hours):
        if 'h' in hours and 'd' in hours:
            days, hours = hours.split('d')
            # Return the value without trailing zeros
            return round((int(days) * 8) + (int(hours.replace("h", "")) / 8), 2)
        elif 'h' in hours:
            return round(int(hours.replace("h", "")) / 8, 2)  # Assuming 8 hours per story point
        elif 'd' in hours:
            return int(hours.replace("d", ""))  # One full day equals one story point
        return 0

    def generate_burndown_data(data):
        start_date = datetime.datetime.strptime(data["startDate"], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(data["endDate"], "%Y-%m-%d")
        total_days = (end_date - start_date).days

        total_story_points = sum(
            issue[2]["story_points"]
            for issue in data.values()
            if isinstance(issue, list) and issue[2]["story_points"] is not None
        )

        # Ideal burndown calculation
        ideal_burndown = [
            total_story_points - (i * (total_story_points / total_days))
            for i in range(total_days + 1)
        ]
        actual_burndown = [total_story_points]  # Start with total story points

        # Simulate actual burndown
        completed_points = 0
        for issue_key, issue_details in data.items():
            if isinstance(issue_details, list) and issue_details[1]["updated_date"]:
                for date_str, hours in issue_details[1]["updated_date"].items():
                    date = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d")
                    days_since_start = (date - start_date).days
                    if days_since_start <= total_days:
                        completed_points += hours_to_story_points(hours)  # Custom function to map hours to story points
                        actual_burndown.append(total_story_points - completed_points)

        # Fill the rest of the days in actual burndown
        actual_burndown += [actual_burndown[-1]] * (total_days + 1 - len(actual_burndown))
        dates = [start_date + datetime.timedelta(days=i) for i in range(total_days + 1)]

        # Create DataFrame
        df = pd.DataFrame(
            {
                "Date": dates,
                "Ideal Burndown": ideal_burndown,
                "Actual Burndown": actual_burndown,
            }
        )
        return df

    df = generate_burndown_data(data)

    # Format the burndown values to remove trailing zeros
    df["Ideal Burndown"] = df["Ideal Burndown"].apply(lambda x: int(x) if x.is_integer() else round(x, 2))
    df["Actual Burndown"] = df["Actual Burndown"].apply(lambda x: int(x) if x.is_integer() else round(x, 2))

    # Plot the Burndown Chart using Plotly
    fig = px.line(
        df,
        x="Date",
        y=["Ideal Burndown", "Actual Burndown"],
        markers=True,
        title=f"Burndown Chart - {data['sprint_name']}",
        labels={"value": "Story Points", "Date": "Sprint Day"},
        template="plotly_dark",
    )
    st.plotly_chart(fig)

    # Display the table
    st.subheader("Burndown Table View")
    table_data = []
    for key, value in data.items():
        if isinstance(value, list):
            issue_summary = value[0].get("issue_summary", "N/A")
            updated_date = value[1].get("updated_date", "N/A")
            story_points = value[2].get("story_points", "N/A")

            formatted_dates = (
                ", ".join(
                    [
                        f"{datetime.datetime.fromisoformat(date.split('.')[0]).strftime('%Y-%m-%d')} ({hours})"
                        for date, hours in updated_date.items()
                    ]
                )
                if updated_date != "N/A"
                else "N/A"
            )

            table_data.append([key, issue_summary, formatted_dates, story_points])

    df_table = pd.DataFrame(
        table_data,
        columns=["Issue ID", "Issue Summary", "Updated Date", "Story Points"],
    )
    df_table.index = df_table.index + 1
    st.table(df_table)


def prepare_scrum_chart_and_table(data):
    all_tasks = []
    for user, tasks in data.items():
        for task in tasks:
            task["User"] = user  # Add user column
            all_tasks.append(task)

    # Create the DataFrame
    overall_df = pd.DataFrame(all_tasks)

    # Check if the DataFrame is empty
    if overall_df.empty:
        return st.warning("No scrum data available to display.")

    # Display Tabular Data with Sequential Indexes for Each User
    for user in overall_df["User"].unique():
        user_specific_df = overall_df[overall_df["User"] == user].copy()
        user_specific_df.reset_index(drop=True, inplace=True)
        user_specific_df.index += 1  # Set index starting from 1 for each table
        user_specific_df.index.name = None  # Remove index column name

        st.subheader(f"Task Details for {user}")
        st.dataframe(user_specific_df)

    # Plot the Pie Chart for Task Summary
    st.subheader("Summary - Task Distribution per User")
    tasks_per_user = overall_df["User"].value_counts()

    # Plotting the pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(tasks_per_user.values, labels=tasks_per_user.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
    plt.title("Task Distribution per User")
    st.pyplot(plt)  # Display the pie chart in Streamlit

def prepare_sprint_chart_and_table(data, ai_message_content, toggle_key):
    # Extract summary and users progress
    summary = data.get('summary', {})
    users_progress = data.get('users_progress', [])
    sprint_summary_df = pd.DataFrame({
        
        "Metric": [
            "Sprint Name", "Start Date", "End Date", 
            "Remaining Days", "Duration Completion (%)", 
            "Work Completion (%)", "Scope Change (%)"
        ],
        "Value": [
            summary.get('sprint_name', 'Unknown Sprint'),
            summary.get('sprint_startdate', 'N/A'),
            summary.get('sprint_enddate', 'N/A'),
            summary.get('remaining_days', 'N/A'),
            summary.get('duration_completion_percentage', '0'),
            summary.get('work_completion_percentage', '0'),
            summary.get('scope_change_percentage', '0')
        ]
    })

    # Prepare progress DataFrame
    df = pd.DataFrame(users_progress)
    df.index = df.index + 1  # Adjust index to start from 1

    status_counts = summary.get('Not Started', 0.0), summary.get('In Progress', 0.0), summary.get('Done', 0.0)
    statuses = ['Not Started', 'In Progress', 'Done']
    plt.figure(figsize=(8, 5))
    sns.barplot(x=statuses, y=status_counts, palette='viridis')
    plt.title("Effort Distribution by Status")
    plt.xlabel("Status")
    plt.ylabel("Effort Hours")

    with st.chat_message("assistant"):
        # Toggle button to switch between AI message content and existing content
        show_ai_message = st.toggle("Show Report Summary", value=False, key=toggle_key)

        if show_ai_message:
            st.write(ai_message_content)
        else:
            # Display summary as a table
            st.write("### Sprint Summary")
            st.table(sprint_summary_df)

            # Display task table
            st.write("### Task Details")
            st.dataframe(df[['Key', 'Status', 'Summary', 'Assignee', 'Total Worklog Effort (hours)']], use_container_width=True)

            # Chart for sprint progress
            st.write("### Effort Hours by Status")
            st.pyplot(plt)

# Display previous messages
def handle_chat_messages():
    for message in st.session_state.chat_history:
        if isinstance(message, HumanMessage):
            st.markdown(
                f"""
                <div class="user-message-container" style="display: flex; justify-content: flex-end;">
                    <p class="user-message">{message.content}</p>
                    <span style="margin-left: 10px;">{user_icon}</span>
                </div>
                <div class="clearfix"></div>
                """,
                unsafe_allow_html=True,
            )
        elif isinstance(message, AIMessage):
            # Convert content to Markdown (or handle if it's a dict)
            if isinstance(message.content, dict):
                formatted_content = str(message.content)  # Convert dict to string
            elif isinstance(message.content, str):
                formatted_content = markdown(message.content).strip()  # Convert Markdown to HTML
            else:
                formatted_content = ""

            # Only render meaningful content
            if formatted_content.strip():
                st.markdown(
                    f"""
                    <div class="chat-container" style="display: flex; align-items: flex-start;">
                        <span class="bot-icon">{bot_icon}</span>
                        <div class="bot-message">
                            {formatted_content}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
        )
        else:
            chart_key = message.get("chart_key", None)
            chart_type = message.get("chart_type", None)
            form_key = message.get("form_key", None)
            form_type = message.get("form_type", None)
            if form_key and form_type:
                if form_type == "switch_jira_project_form":
                    dropdown_values = message.get("dropdown_values", [])
                    construct_switch_project_form(form_key, dropdown_values)
                elif form_type == "execute_jenkins_pipeline_form":
                    dropdown_values = message.get("dropdown_values", [])
                    construct_jenkins_build_form(dropdown_values, form_key)
                elif form_type == "register_jenkins_pipeline_form":
                    construct_register_jenkins_pipeline_form(form_key)
                elif form_type == "register_jira_project_form":
                    construct_register_jira_project_form(form_key)
                elif form_type == "create_jira_issue_form":
                    epics = message.get("epics", [])
                    form_data = message.get("form_data", None)
                    construct_create_jira_issue_form(form_key, epics, form_data)
                elif form_type == "get_my_jira_issues_form":
                    filter_data = message.get("filter_data", {})
                    select_box_key = message.get("select_box_key", None)
                    construct_get_jira_issues_form(form_key, filter_data, select_box_key)
                elif form_type == "get_current_sprint_issues_form":
                    filter_data = message.get("filter_data", {})
                    select_box_key = message.get("select_box_key", None)
                    construct_get_jira_issues_form(form_key, filter_data, select_box_key)
                elif form_type == "github_code_search_form":
                    filter_data = message.get("filter_data", {})
                    select_box_key = message.get("select_box_key", None)
                    construct_github_code_search_form(form_key, filter_data, select_box_key)
                elif form_type == "register_jira_details_form":
                    construct_register_jira_details_form(form_key)
                elif form_type == "register_github_details_form":
                    toggle_key = message.get("toggle_key", None)
                    construct_register_github_details_form(form_key, toggle_key)
                elif form_type == "invoke_terminal_form":
                    construct_invoke_terminal_form(form_key)
                elif form_type == "select_pipeline_name_form":
                    dropdown_values = message.get("dropdown_values", [])
                    construct_select_pipeline_name_form(form_key, dropdown_values)
                elif form_type == "update_delete_jenkins_pipeline_form":
                    data = message.get("filter_data", {})
                    select_box_key = message.get("select_box_key", None)
                    construct_update_delete_jenkins_pipeline_form(form_key, data, select_box_key)
                elif form_type == "update_delete_github_details_form":
                    data = message.get("filter_data", {})
                    select_box_key = message.get("select_box_key", None)
                    construct_update_delete_github_details_form(form_key, data, select_box_key)
            elif chart_key and chart_type:
                if chart_type == "sprint_report":
                    values = message.get("values", [])
                    ai_message_content = message.get("ai_message_content", "")
                    toggle_key = message.get("toggle_key", None)
                    prepare_sprint_chart_and_table(values, ai_message_content, toggle_key)
                elif chart_type == "velocity_report":
                    values = message.get("values", [])
                    ai_message_content = message.get("ai_message_content", "")
                    toggle_key = message.get("toggle_key", None)
                    prepare_velocity_chart_and_table(values, ai_message_content, toggle_key)
                elif chart_type == "burnup_report":
                    values = message.get("values", [])
                    prepare_burnup_chart_and_table(values)
                elif chart_type == "burndown_report":
                    values = message.get("values", [])
                    prepare_burndown_chart_and_table(values)
                elif chart_type == "scrum_report":
                    values = message.get("values", [])
                    prepare_scrum_chart_and_table(values)

def handle_chat_input():
    if user_input := st.chat_input("What is up?"):
        human_message = HumanMessage(content=user_input)
        st.session_state.chat_history.append(human_message)
         #st.chat_message("user").write(human_message.content)

        st.markdown(
                f"""
                <div class="user-message-container" style="display: flex; justify-content: flex-end;">
                    <p class="user-message">{human_message.content}</p>
                    <span style="margin-left: 10px;">{user_icon}</span>
                </div>
                <div class="clearfix"></div>
                """,
                unsafe_allow_html=True,
            )
        if user_input.lower() in ["new", "reset", "restart"]:
            st.session_state.thread_id += 1
            ai_message = AIMessage(content="New session started.")
            st.session_state.chat_history.append(ai_message)
            # st.chat_message("assistant").write(ai_message.content)
            st.markdown(
                f"""
                <div class="chat-container" style="display: flex; align-items: flex-start;">
                            <span class="bot-icon">{bot_icon}</span>
                            <div class="bot-message">
                                {ai_message.content}
                            </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            try:
                response = invoke_supervisor_agent(human_message)
                state_snapshot = supervisor_graph_agent.get_state(getConfig(st.session_state.thread_id))
                state_values = state_snapshot.values
                input_form = state_values.get('input_form', None)
                isSprintReport = state_values.get('sprint_report', None)
                isVelocityReport = state_values.get('velocity_report', None)
                isBurnupReport = state_values.get('burnup_report', None)
                isBurndownReport = state_values.get('burndown_report', None)
                isScrumReport = state_values.get('scrum_report', None)
                isFormData = state_values.get('form_data', None)
                chain_of_thought = state_values.get('chain_of_thought', [])
                logging.info(f"Chain of thought: {chain_of_thought}")
                 # Check if the reports are not None before accessing their data
                if isSprintReport:
                    if isSprintReport.get('data'):
                        ai_message = response['messages'][-1]
                        toggle_key = f"sprint_report_toggle_{st.session_state['form_counter']}"
                        st.session_state['form_counter'] += 1                        
                        prepare_sprint_chart_and_table(isSprintReport['data'], ai_message.content, toggle_key)
                        state_values['sprint_report'] = None
                        supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                        chart_object = {"chart_key": "chart", "chart_type": "sprint_report", "values": isSprintReport['data'], "ai_message_content": ai_message.content, "toggle_key": toggle_key}
                        st.session_state.chat_history.append(chart_object)
                    else:
                        st.error("Sprint Report data is missing or invalid.")
                
                elif isVelocityReport:
                    if isVelocityReport.get('data'):
                        ai_message = response['messages'][-1]
                        toggle_key = f"velocity_report_toggle_{st.session_state['form_counter']}"
                        st.session_state['form_counter'] += 1
                        prepare_velocity_chart_and_table(isVelocityReport['data'], ai_message.content, toggle_key)
                        state_values['velocity_report'] = None
                        supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                        chart_object = {"chart_key": "chart", "chart_type": "velocity_report", "values": isVelocityReport['data'], "ai_message_content": ai_message.content, "toggle_key": toggle_key}
                        st.session_state.chat_history.append(chart_object)
                    else:
                        st.error("Velocity Report data is missing or invalid.")

                elif isBurnupReport:
                    if isBurnupReport.get('data'):
                        prepare_burnup_chart_and_table(isBurnupReport['data'])
                        state_values['burnup_report'] = None
                        supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                        chart_object = {"chart_key": "chart", "chart_type": "burnup_report", "values": isBurnupReport['data']}
                        st.session_state.chat_history.append(chart_object)
                    else:
                        st.error("Burnup Report data is missing or invalid.")
                
                elif isBurndownReport:
                    if isBurndownReport.get('data'):
                        prepare_burndown_chart_and_table(isBurndownReport['data'])
                        state_values['burndown_report'] = None
                        supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                        chart_object = {"chart_key": "chart", "chart_type": "burndown_report", "values": isBurndownReport['data']}
                        st.session_state.chat_history.append(chart_object)
                    else:
                        st.error("Burndown Report data is missing or invalid.")
                
                elif isScrumReport:
                
                        prepare_scrum_chart_and_table(isScrumReport['data'])
                        state_values['scrum_report'] = None
                        supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                        chart_object = {"chart_key": "chart", "chart_type": "scrum_report", "values": isScrumReport['data']}
                        st.session_state.chat_history.append(chart_object)
                    
                elif isFormData and input_form:
                    if isFormData.get('data'):
                        form_data = isFormData['data']
                        st.session_state.chat_history.append(form_data)
                        st.session_state['form_data']= form_data
                        show_form(input_form)
                        state_values['input_form'] = None
                        state_values['form_data'] = None
                        supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                    else:
                        show_form(input_form)
                        state_values['input_form'] = None
                        supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                
                elif input_form:
                    show_form(input_form)
                    state_values['input_form'] = None
                    supervisor_graph_agent.update_state(getConfig(st.session_state.thread_id), state_values, None)
                else:
                    ai_message = response['messages'][-1]
                    st.session_state.chat_history.append(ai_message)
                    # st.markdown(
                    #     f"""
                    #     <div class="bot-message-container" style="display: block; justify-content: flex-start;">
                    #         <span style="margin-right: 10px;">{bot_icon}</span>
                    #         <p class="bot-message">{ai_message.content}</p>
                    #     </div>
                    #     <div class="clearfix"></div>
                    #     """,
                    #     unsafe_allow_html=True,
                    # )
                    st.markdown(
                        f"""
                        <div class="chat-container" style="display: flex; align-items: flex-start;">
                            <span class="bot-icon">{bot_icon}</span>
                            <div class="bot-message">
                                {ai_message.content}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                  # Initialize session state
                    # if 'show_details' not in st.session_state:
                    #     st.session_state.show_details = True

                    # Button to toggle visibility
                    # if st.toggle("Chain of thoughts"):
                    #     st.session_state.show_details = True
                    
                    # Display details if the user wants to see them
                    # showChainOfThoughts(text_blocks)
                    
                    # display_message(bot_icon, ai_message, text_blocks)

            except openai.RateLimitError as e:
                logging.error(f"Rate limit error: {e}")
                ai_message = AIMessage(content="Rate limit exceeded. Please try again later.")
                st.session_state.chat_history.append(ai_message)
                st.markdown(
                    f"""
                    <div class="chat-container" style="display: flex; align-items: flex-start;">
                            <span class="bot-icon">{bot_icon}</span>
                            <div class="bot-message">
                                {ai_message.content}
                            </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except openai.AuthenticationError as e:
                logging.error(f"Authentication error: {e}")
                ai_message = AIMessage(content="Authentication error. Error: " + str(e) + " New session started.")
                st.session_state.chat_history.append(ai_message)
                st.markdown(
                    f"""
                    <div class="chat-container" style="display: flex; align-items: flex-start;">
                            <span class="bot-icon">{bot_icon}</span>
                            <div class="bot-message">
                                {ai_message.content}
                            </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                get_new_supervisor_graph_agent()
            except Exception as e:
                logging.error(f"Error invoking Supervisor Agent. Stack trace: {traceback.format_exc()}")
                ai_message = AIMessage(content="Something went wrong. Please try again.")
                st.session_state.chat_history.append(ai_message)
                st.markdown(
                    f"""
                    <div class="chat-container" style="display: flex; align-items: flex-start;">
                            <span class="bot-icon">{bot_icon}</span>
                            <div class="bot-message">
                                {ai_message.content}
                            </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

def invoke_supervisor_agent(human_message):
    max_retries = 5
    retry_delay = 1  # Initial delay in seconds

    for attempt in range(max_retries):
        try:
            response = supervisor_graph_agent.invoke({"messages": human_message}, getConfig(st.session_state.thread_id))
            return response
        except openai.RateLimitError as e:
            if attempt < max_retries - 1:
                logging.warning(f"Rate limit error: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logging.error(f"Rate limit error: {e}. Max retries exceeded.")
                raise
            

def display_active_forms():
    if st.session_state.display_switch_jira_project_form:
        show_switch_project_form()
        st.session_state.display_switch_jira_project_form = False

    if st.session_state.display_execute_jenkins_pipeline_form:
        show_execute_jenkins_pipeline_form()
        st.session_state.display_execute_jenkins_pipeline_form = False

    if st.session_state.display_register_jenkins_pipeline_form:
        show_register_jenkins_pipeline_form()
        st.session_state.display_register_jenkins_pipeline_form = False

    if st.session_state.display_register_jira_project_form:
        show_register_jira_project_form()
        st.session_state.display_register_jira_project_form = False

    if st.session_state.display_create_jira_issue_form:
        show_create_jira_issue_form()
        st.session_state.display_create_jira_issue_form = False

    if st.session_state.display_get_my_jira_issues_form:
        show_get_my_jira_issues_form()
        st.session_state.display_get_my_jira_issues_form = False

    if st.session_state.display_get_current_sprint_issues_form:
        show_get_current_sprint_issues_form()
        st.session_state.display_get_current_sprint_issues_form = False
    
    if st.session_state.display_github_code_search_form:
        show_github_code_search_form()
        st.session_state.display_github_code_search_form = False
    
    if st.session_state.display_register_jira_details_form:
        show_register_jira_details_form()
        st.session_state.display_register_jira_details_form = False
    
    if st.session_state.display_register_github_details_form:
        show_register_github_details_form()
        st.session_state.display_register_github_details_form = False
    
    if st.session_state.display_invoke_terminal_form:
        show_invoke_terminal_form()
        st.session_state.display_invoke_terminal_form = False

    if st.session_state.display_select_pipeline_name_form:
        show_select_pipeline_name_form()
        st.session_state.display_select_pipeline_name_form = False

    if st.session_state.display_update_delete_jenkins_pipeline_form:
        show_update_delete_jenkins_pipeline_form()
        st.session_state.display_update_delete_jenkins_pipeline_form = False
    
    if st.session_state.display_update_delete_github_details_form:
        show_update_delete_github_details_form()
        st.session_state.display_update_delete_github_details_form = False

col1, col2 = st.columns([18, 4])  # Adjust the ratio to control the column width
with col2:
    toggle = st.toggle("Doc Search")

st.markdown(
        '<h4 class="title">Welcome to iCE (intelligent Copilot Engine)</h4>',
        unsafe_allow_html=True,
)

if toggle:
    rag_fusion()
    logging.info("Doc Search")
else:
    initialize_session_state(welcome_message)

    #print("thread_id", st.session_state.thread_id)

    handle_chat_messages()

    handle_chat_input()

    display_active_forms()