# intelligent ChatOps Engine (iCE)

## Introducing iCE
iCE (Intelligent ChatOps Engine) is a voice enabled chatbot engine, which can assist users perfrom several Dev and operational (Ops) functions through voice or chat interactions.  Backed by powerful AI/ML model, iCE can help teams/individuals with complete Kubernetes environment management, Flexible devops and Assisted development for developers among several functions. 

iCE is developed using [Python Chatterbot library](https://chatterbot.readthedocs.io/en/stable/), NLTK modules, Python Flask, Kubernetes API, GitHub API for its various functions.
![iCE Architecture](https://user-images.githubusercontent.com/19473736/132937378-3f77cf8e-8255-4a80-8d98-fe9163e36d1b.png)



Multi-environment management, assisted development and flexible devops are some of its key features to name.\
The apparatus is available as a ChatOps software-as-a-service and can be integrated through REST APIs to chat systems such as Webex/MS Teams, Slack etc.

Sharing some of the commands below which can requested using voice commands also. There are many more functions available...

NLP based chatbot.\
Run "pip install -r requirements.txt"\
Run "python train.py"\
Then run "python app.py"\
Launch browser and run http://127.0.0.1:5500/ 





General Conversation and Assistance
______________________________________

hi how are you \
what's your name \
what are you\
what can you do for me

what is your age\
Who is your boss\
what are your favorite topics\
what is your programming language\
can you eat


What is Cisco\
Who is Chuck Robbins





K8s Management: 
(a 4 node K8s environment have been setup in CALO Lab for this POC)
___________________________________________________________________________

What is kubernetes\
Can you play on YouTube how to install kubernetes

can you get me pods from all namespaces\
Can you get me pods from specific namespace\
get me pods from namespace test-namespace

can you create a namespace\
can you delete a namespace


Can you help me with deployment\
Can you please delete a deployment

Please create namespace with file test-namespace.yaml and assign quota test-namespace-quota.yaml\
Deploy with file nginx-deployment.yaml in namespace test-namespace





Assisted DevOps: 
_______________________________

can you create a git repository\
Create github repository with repo name Test-Repo-iceDemo


Upload file to github repo\
Upload file nginx-deployment.yaml to git repo repo_url\
Upload file file_name to git repo repo_url in branch branch_name


what are the available pipelines\
what are the available NSO pipelines?

upload default NSO pipeline in the git repo repo_url\
upload docker image pull pipeline in the git repo repo_url\
upload corona scan pipeline in the git repo repo_url

upload default NSO pipeline in the git repo repo_url in branch branch_name





Assisted development: 
_______________________________
Can you find me sample yang model for l3vpn\
can you find me sample yang model for RFS microservice\
can you find me sample code for RFS microservice\
Can you find sample code for rfs\
Can you find sample yang models for cfs\
Can you find sample yang module for cfs\
Can you find sample java code for cfs\
Can you find sample code for l3vpn


[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/srinjoychak/iCE)
