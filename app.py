from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
from flask_cors import CORS, cross_origin
from werkzeug.utils import  secure_filename
import os

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_PATH'] = 'upload'

botname='iCE'
chatbot = ChatBot(botname, 
	#storage_adapter='chatterbot.storage.SQLStorageAdapter',
	logic_adapters=[
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': 'I am sorry, but I do not understand.',
            'maximum_similarity_threshold': 0.8
        },
        {
            "import_path": "chatterbot.logic.MathematicalEvaluation",

        },
        {
            "import_path": "chatterbot.logic.UnitConversion",

        },
        {
            "import_path": "profanity_adapter.ProfanityAdapter",

        },
        {
            "import_path": "play_yt.PlayYtAdapter",

        },
        {
            "import_path": "get_joke.GetJoke",

        },
        {
            "import_path": "wikipedia_search.WikiSearchAdapter",

        },
        {
            "import_path": "get_k8s_pods.GetK8sPods",

        },
        {
            "import_path": "create_k8s_namespace.CreateK8sNamespace",
        },
        {
            "import_path": "create_k8s_deployment.CreateK8sDeployment",
        },
        {
            "import_path": "create_pipeline_git.GitManagement",
        },
        {
            "import_path": "create_assisted_coding.AssistDev",
        },
    ],
 )

@app.route("/")
def home():
    return render_template("index.html", botname=botname)

@app.route("/get")
def get_bot_response():
    userInput=request.args.get('msg')
    return str(chatbot.get_response(userInput))

@app.route('/upload')
def upload_file():
    return render_template('index.html')

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file_save():
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(app.config['UPLOAD_PATH'], secure_filename(f.filename)))
        return redirect(url_for('home'))



if __name__ == '__main__':
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(port=5500,debug=True) 

