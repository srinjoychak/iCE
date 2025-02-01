import streamlit as st
import multiprocessing
from langchain_core.messages import HumanMessage, AIMessage
import os
import time
import traceback
from rag_fusion.query import get_answer, clear_conversation_history
from rag_fusion.ingest import main
from rag_fusion.constants import SOURCE_DIRECTORY, release_model_memory
from logger_config import configure_logging

logger = configure_logging('logs', 'application.log')

# Constants
SOURCE_FOLDER = SOURCE_DIRECTORY

def initialize_session_state():
    """Initialize session state variables."""
    if 'rag_history' not in st.session_state:
        st.session_state['rag_history'] = []
    if 'ingest_button_disabled' not in st.session_state:
        st.session_state['ingest_button_disabled'] = False
    if 'user_input' not in st.session_state:
        st.session_state['user_input'] = ""

def handle_user_input():
    try:
        """Handle user input and update chat history."""
        with st.form(key="user_input_form", clear_on_submit=True):
            col1, col2 = st.columns([7,1])
            with col1:
                user_input = st.text_input("Query to Search in Docs", value=st.session_state.get("user_input", ""))
            with col2:
                st.empty()  # Add some empty space (a vertical gap)
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # Additional space with HTML (if needed)
                
                # The submit button
                submit_button = st.form_submit_button("Submit")

        response_placeholder = st.empty()

        if submit_button:
            if user_input.lower() in ['new', 'reset', 'restart', 'clear']:
                clear_conversation_history()
                st.session_state.clear()
                st.session_state.rag_history = []
                # response_placeholder.markdown("🤖**Assistant:** New session started")
                st.toast("New session started", icon="✅")
            elif user_input.strip():
                try:
                    response_placeholder.markdown(f"**👤**You:** {user_input}")
                    # Process the user input and stream response
                    answer = ""
                    for chunk in get_answer(user_input):
                        answer += chunk
                        response_placeholder.markdown(f"🤖**Assistant:** {answer}")
                    release_model_memory()
                    # Append interaction to chat history
                    st.session_state.rag_history.append(HumanMessage(user_input))
                    st.session_state.rag_history.append(AIMessage(answer))

                    # Clear the input box
                    st.session_state.user_input = ""
                except Exception as e:
                    st.toast("Something wrong!!!\nTry Ingest Again", icon="❌")
                    logger.error(f"Error processing user input: {e}")
    except Exception as e:
        logger.error(f"Error handling user input. Error: {e}")

def display_chat_history():
    try:
        """Display chat history in the sidebar."""
        st.sidebar.header("Chat History")
        for chat in st.session_state.rag_history:
            if isinstance(chat, HumanMessage):
                st.sidebar.markdown(f"👤**You:** {chat.content}")
            elif isinstance(chat, AIMessage):
                st.sidebar.markdown(f"🤖**Assistant:** {chat.content}")
    except Exception as e:
        logger.error(f"Error display chat history. Error: {e}")

def save_uploaded_documents(files):
    """Save uploaded documents to the source folder."""
    try:
        os.makedirs(SOURCE_FOLDER, exist_ok=True)
        for file in files:
            file_path = os.path.join(SOURCE_FOLDER, file.name)
            try:
                with open(file_path, "wb") as f:
                    f.write(file.read())
                st.toast(f"Uploaded {file.name} successfully!", icon="✅")
                logger.info(f"File '{file.name}' uploaded successfully.")
            except Exception as e:
                st.error(f"Failed to save {file.name}. Please try again.")
                logger.error(f"Error saving file '{file.name}': {e}")
    except Exception as e:
        st.error("Failed to initialize the upload process.")
        logger.critical(f"Error creating source folder '{SOURCE_FOLDER}': {e}")

def display_and_manage_documents():
    """Display available documents and allow deletion."""
    try:
        os.makedirs(SOURCE_FOLDER, exist_ok=True)
        files = os.listdir(SOURCE_FOLDER)
        with st.expander("Available Documents"):
            if files:
                for file in files:
                    file_path = os.path.join(SOURCE_FOLDER, file)
                    col1, col2 = st.columns([20, 3])
                    with col1:
                        st.text(file)
                    with col2:
                        if st.button("🗑", key=f"delete_{file}"):
                            try:
                                os.remove(file_path)
                                st.toast(f"Deleted {file} successfully!", icon="✅")
                                logger.info(f"File '{file}' deleted successfully.")
                            except Exception as e:
                                st.error(f"Failed to delete {file}.")
                                logger.error(f"Error deleting file '{file}': {e}")
                            time.sleep(2)
                            st.rerun()
            else:
                st.write("No documents available.")
                logger.info("No documents found in the source folder.")
    except Exception as e:
        st.error("Failed to display documents.")
        logger.critical(f"Error managing documents in folder '{SOURCE_FOLDER}': {e}")

def manage_documents_section():
    """Handle document uploads and management."""
    try:
        display_and_manage_documents()

        # Allowed file extensions
        allowed_extensions = [".pdf", ".txt", ".docx", ".xlsx", ".xls"]

        # Use a session state variable to track uploaded files
        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files = []

        # File uploader
        uploaded_files = st.file_uploader(
            "Upload files", accept_multiple_files=True, key="file_uploader"
        )

        # Upload button
        if st.button("Upload"):
            if uploaded_files:
                # Filter files based on allowed extensions
                valid_files = [
                    file for file in uploaded_files
                    if any(file.name.lower().endswith(ext) for ext in allowed_extensions)
                ]
                invalid_files = [
                    file.name for file in uploaded_files
                    if not any(file.name.lower().endswith(ext) for ext in allowed_extensions)
                ]

                if valid_files:
                    save_uploaded_documents(valid_files)
                    st.session_state.uploaded_files.extend([file.name for file in valid_files])
                    st.toast(f"Uploaded {len(valid_files)} file(s) successfully!", icon="✅")

                if invalid_files:
                    st.toast(
                        f"The following files are not supported: {', '.join(invalid_files)}. ",
                        icon="⚠️"
                    )
                    st.toast(f"Only {', '.join(allowed_extensions)} files are allowed.", icon="⚠️")
                time.sleep(2)
                st.rerun()  
            else:
                st.toast("No files selected for upload.")
                logger.warning("Upload button clicked without selecting files.")
    except Exception as e:
        logger.error(f"Error in Manage Document Section. Error: {e}")


def main_task(queue):
    """Main task for ingestion."""
    try:
        main(queue)
    except Exception as e:
        error_message = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Main task failed: {e}")
        if queue:
            queue.put(error_message)  # Send the full error message to the queue
        raise RuntimeError(f"Main task failed: {e}")

def run_process(task, *args):
    """Run a task in a separate process."""
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()  # Ensure the queue is created in the correct context
    process = ctx.Process(target=task, args=(queue, *args))
    process.start()
    process.join()
    return queue

def handle_ingestion():
    try:
        """Handle ingestion process and button states."""
        if st.button("Ingest", disabled=st.session_state.get("ingest_button_disabled", False)):
            if not os.listdir(SOURCE_FOLDER):
                st.toast("No files available to ingest. Please upload files.", icon="⚠️")
                logger.warning("Ingest button clicked, but no files found in the source folder.")
                return
            
            st.session_state["ingest_button_disabled"] = True
            with st.spinner("Loading..."):
                try:
                    # Run the subprocess and retrieve the queue
                    queue = run_process(main_task)
                    
                    # Retrieve all messages from the queue
                    error_messages = []
                    while not queue.empty():
                        error_message = queue.get()
                        error_messages.append(error_message)
                        logger.error(f"Ingest process failed: {error_message}")
                    
                    # all error messages or success
                    if error_messages:
                        for error in error_messages:
                            pass
                        st.toast("Ingest process failed", icon="❌") # Last Error Message
                    else:
                        st.toast("Ingest process completed successfully!", icon="✅")
                except Exception as e:
                    st.toast("Ingest process failed", icon="❌")
                    logger.error("Ingest process failed")
                finally:
                    clear_conversation_history()
                    st.session_state.clear()
                    st.session_state.rag_history = []
                    st.session_state["ingest_button_disabled"] = False
    except Exception as e:
        st.toast("Ingest process failed", icon="❌")
        logger.error("error Handle Ingestion. Error: {e}")

def rag_fusion():
    """Main application logic."""
    initialize_session_state()

    handle_user_input()
    toggle = st.toggle("Manage Documents")

    if toggle:
        manage_documents_section()
        handle_ingestion()

    display_chat_history()

if __name__ == "__main__":
    rag_fusion()
