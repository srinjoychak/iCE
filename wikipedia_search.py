from chatterbot.logic import LogicAdapter

class WikiSearchAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)

    def can_process(self, statement):
        self.words = ['what is','who is','how is','how to']
        if any(x in statement.text.lower() for x in self.words):
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement
        import wikipedia

        question = [(input_statement.text.lower()).replace(i,'') for i in [x for x in self.words if x in input_statement.text.lower()]][0]

        ret = wikipedia.summary(question, sentences=5)
        response_statement = Statement(text=ret)
        response_statement.confidence = 1
        return response_statement

