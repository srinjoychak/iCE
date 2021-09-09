from chatterbot.logic import LogicAdapter

class GetJoke(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)

    def can_process(self, statement):
        words = ['tell','joke']
        if all(x in [i.lower() for i in statement.text.split()] for x in words):
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement
        import pyjokes

        joke = pyjokes.get_joke('en', 'all')
        if joke:
            confidence = 1
        else:
            confidence = 0
        response_statement = Statement(text=joke)
        response_statement.confidence = confidence
        return response_statement