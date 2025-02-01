import gc
from sklearn.metrics.pairwise import cosine_similarity
from rag_fusion.prompts import output_prompt, multi_query_history_prompt, no_data_prompt
from rag_fusion.constants import EMBEDDINGS, release_model_memory, PERSIST_DIRECTORY, CHROMA_SETTINGS, Chroma, DB
from logger_config import configure_logging
from rag_fusion.llm import generate_non_streaming_response, generate_streaming_response

# Configure logging
logger = configure_logging('logs', 'rag_query.log')

# Conversation history (global variable)
conversation_history = []

# Utility functions
def append_to_conversation_history(user_query, response, max_length=10):
    """Update conversation history with the latest query and response."""
    global conversation_history
    conversation_history.append({"user": user_query, "assistant": response})
    if len(conversation_history) > max_length:
        conversation_history.pop(0)

def clear_conversation_history():
    """Clear conversation history and release memory."""
    global conversation_history
    conversation_history = []
    release_model_memory()
    gc.collect()
    logger.info("Conversation history and cache cleared.")

# Core functions
def fetch_docs(question, top_k=4):
    """Fetch documents relevant to the given question."""
    try:
        # Initialize database
        DB = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=EMBEDDINGS,
            client_settings=CHROMA_SETTINGS,
        )
        try:
            collection = DB.get()
            if len(collection["ids"])== 0:
                return None
        except Exception:
            return None
        retriever = DB.as_retriever(search_kwargs={"k": top_k})
        result = retriever.invoke(question)
        logger.info(f"Successfully fetched documents for question: {question}")
        return result
    except Exception as e:
        logger.error(f"Error fetching documents for question: {question}. Error: {e}")
        error_message = f"Error fetching documents for question: {question}. Error: {str(e)}"
        raise RuntimeError(error_message) from e

def generate_relevant_questions(prompt, user_query):
    """Generate a list of relevant questions based on the user query."""
    try:
        logger.debug(f"Generating relevant questions for user query: {user_query}")
        response = generate_non_streaming_response(prompt, user_query)
        questions = response.strip().split("\n")
        logger.info(f"Generated {len(questions)} questions for user query.")
        return questions
    except Exception as e:
        logger.error(f"Error generating questions for user query: {user_query}. Error: {e}")
        return []

def re_rank_documents(query, documents):
    """Re-rank documents based on cosine similarity to the query."""
    try:
        logger.debug(f"Re-ranking documents for query: {query}")

        # Compute embeddings
        query_embedding = EMBEDDINGS.embed_documents([query])[0]
        doc_embeddings = EMBEDDINGS.embed_documents([doc.page_content for doc in documents])

        # Compute similarity scores
        similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
        ranked_docs = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)

        # Add similarity scores to document metadata
        for doc, score in ranked_docs:
            doc.metadata['similarity_score'] = score

        logger.info(f"Ranked {len(ranked_docs)} documents for query: {query}")
        del query_embedding, doc_embeddings, similarities
        return [doc for doc, _ in ranked_docs]
    except Exception as e:
        error_message = f"Error during document re-ranking for query: {query}. Error: {str(e)}"
        logger.error(f"Error during document re-ranking for query: {query}. Error: {e}")
        raise RuntimeError(error_message) from e

def fetch_relevant_documents(questions):
    """Fetch and re-rank relevant documents for a list of questions."""
    try:
        logger.debug("Fetching and ranking documents for questions.")

        # Fetch documents for each question
        question_doc_map = {}
        for question in filter(str.strip, questions):  
            if (docs := fetch_docs(question)) is None:      
                return  None
            question_doc_map[question] = docs  

        # Re-rank documents for each question
        all_ranked_docs = [re_rank_documents(q, docs) for q, docs in question_doc_map.items()]

        # Flatten and remove duplicates
        unique_docs = []
        seen_ids = set()
        for doc_list in all_ranked_docs:
            for doc in doc_list:
                doc_id = doc.metadata.get("id", hash(doc.page_content))
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_docs.append(doc)

        # Sort by similarity score
        sorted_docs = sorted(unique_docs, key=lambda d: d.metadata.get('similarity_score', 0), reverse=True)

        # Return top documents as a single string
        return "\n".join([doc.page_content for doc in sorted_docs[:5]])
    except Exception as e:
        logger.error(f"Error fetching relevant documents. Error: {e}")
        error_message = f"Error fetching relevant documents. Error: {str(e)}"
        raise RuntimeError(error_message) from e

def fetch_answer(prompt, user_query, streaming=True):
    """Fetch answer to a user query based on the final prompt."""
    try:
        logger.debug(f"Fetching answer for user query: {user_query}")
        if streaming:
            answer = ""
            for chunk in generate_streaming_response(prompt, user_query):
                answer += chunk
                yield chunk
            append_to_conversation_history(user_query, answer)
        else:
            answer = generate_non_streaming_response(prompt, user_query)
            append_to_conversation_history(user_query, answer)
            return answer
    except Exception as e:
        logger.error(f"Error fetching answer for user query: {user_query}. Error: {e}")
        yield "Error: Failed to generate an answer"

# Main pipeline function
def get_answer(user_query, streaming=True):
    """Main pipeline to handle user query and generate an answer."""
    try:
        if not user_query:
            logger.error("User query is required but was not provided.")
            return "Error: User query is required"

        logger.debug(f"Processing user query: {user_query}")

        # Include conversation history in query
        query_with_history = f"Previous Conversation History in Order : {conversation_history}\n\nUser Query: {user_query}"

        # Generate relevant questions
        questions = generate_relevant_questions(multi_query_history_prompt, query_with_history)

        # Fetch relevant documents
        relevant_documents = fetch_relevant_documents(questions)
        if relevant_documents is None:
            return fetch_answer(no_data_prompt, query_with_history, streaming)
        # Prepare final prompt
        final_prompt = f"{output_prompt}\n{relevant_documents}"

        # Generate and return the answer
        return fetch_answer(final_prompt, query_with_history, streaming)
    except Exception as e:
        logger.error(f"Error in get_answer function. Error: {e}")
        error_message = f"Error in get_answer function for query: {user_query}. Error: {str(e)}"
        logger.error(error_message)
        raise RuntimeError(error_message) from e
    finally:
        release_model_memory()
        gc.collect()

