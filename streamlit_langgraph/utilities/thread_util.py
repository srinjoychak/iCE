thread_id = 1

def getConfig(thread_id=thread_id):
    return {"configurable": {"thread_id": str(thread_id)}}

def new_thread():
    global thread_id
    thread_id += 1
    return thread_id