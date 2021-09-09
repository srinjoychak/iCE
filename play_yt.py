from chatterbot.logic import LogicAdapter
from flask import Flask, render_template, request


class PlayYtAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)

    def can_process(self, statement):
        words = ['play','on','youtube']
        if all(x in [i.lower() for i in statement.text.split()] for x in words):
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement
        import requests
        from datetime import date, timedelta
        import json
        import webbrowser as web
        import pywhatkit

        song = (input_statement.text.lower()).replace('play on youtube ', '')
        song = song.replace('can you ','')
        response_statement = Statement(text='Started playing {} on Youtube'.format(song.title()))
        pywhatkit.playonyt(song)

        response_statement.confidence = 1
        return response_statement