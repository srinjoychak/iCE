# intelligent ChatOps Engine (iCE)

## Introducing iCE
iCE (Intelligent ChatOps Engine) is a voice enabled chatbot engine, which can assist users perfrom several Dev and operational (Ops) functions through voice or chat interactions.  Backed by powerful AI/ML engine, iCE can help teams/individuals with complete Kubernetes environment management, Flexible devops and Assisted development for developers among several functions. 

To summarize, the functionality available in iCE includes:

**Multi-Platform Administration and Monitoring**
  - Integrate, manage and operate different cloud platforms. Current feature only supports kubernetes administration and management. Feature enhancement for AWS integration is under development.
  - Collaboratively work on setting up required infra (requester, dev teams and operations teams)
  - Quicker allocation of resources (Resource Reservation), optimizing enterprise resource utilization
  - Interactivly deployment of services through chatbot
  - View statistics for any metric from chat 
  - Get real-time server alarms and notifications from iCE


**Code Reusability and Assisted Development**
  - iCE analyzes each git repo within an enterprise. It then catagorize and catalog available code across. Classification is done based on intent and function of the code.
  - It can help search most relevant code across the enterprise and generate a template code for a given intent. This helps maximize code-reusability within an Enterprise, reducing dev effort while improving code-quality.
  - iCE can help search internet and find a suitable code for a given intent if none matching inside the enterprise code inventory
  - For Cisco development effort iCE enables seamless SonarQube and Corona integration for developed code quality and vulnerabilities.


**Flexible DevOps Assistance**
  - Creating GitHub repositories for team
  - Quicker code commits and pull requests
  - Clone any file from any repo to any repo
  - Assisted pipeline development and template pipeline generation based on user intent
  - Declarative pipeline execution and tracking execution
  - Immediate failure notifications and defect/issue creation from chat window

iCE is developed using [Python Chatterbot library](https://chatterbot.readthedocs.io/en/stable/), NLTK modules, Python Flask, Kubernetes API, GitHub API for its various functions.
![iCE Architecture](https://user-images.githubusercontent.com/19473736/132937558-40118392-7f18-4b4c-988d-d770214361aa.jpg)


## Quick Start
You can use our sample web-based chat client interface to interact with any iCE application.
Assuming you have pip installed with Python 3.7 or higher:

```
git clone https://github.com/srinjoychak/iCE.git
cd iCE
pip install -r requirements.txt
python train.py
python app.py
```
Launch browser and run http://127.0.0.1:5500/ 

![iCE chatbot](https://user-images.githubusercontent.com/19473736/132938237-3c79478b-9842-4038-a7fa-d33f5974bca9.jpg)


## iCE Sample Conversations 
Currently iCE has been developed to operate only inside Cisco network. So the user has to be connected to Cisco VPN or network. 
For Kubernetes administration, the user first have to upload the config file to iCE.


**General Conversation and Assistance**
  - hi how are you 
  - what's your name 
  - what are you
  - what can you do for me

  - what is your age
  - Who is your boss
  - what are your favorite topics
  - what is your programming language
  - can you eat
  
  - What is Cisco
  - Who is Chuck Robbins


**K8s Management**\
A 4 node K8s environment have been setup in CALO Lab for this POC. The config file for the POC setup can be shared upon request.\
Please contact us at [srinjcha@cisco.com](mailto:srinjcha@cisco.com).
Sample files for namespace creation and deployment of a service can be found inside [test-data folder](https://github.com/srinjoychak/iCE/tree/master/test-data).

  - What is kubernetes
  - Can you play on YouTube how to install kubernetes

  - can you get me pods from all namespaces
  - Can you get me pods from specific namespace
  - get me pods from namespace test-namespace

  - can you create a namespace
  - can you delete a namespace

  - Can you help me with deployment
  - Can you please delete a deployment

  - Please create namespace with file test-namespace.yaml and assign quota test-namespace-quota.yaml
  - Deploy with file nginx-deployment.yaml in namespace test-namespace


**Assisted DevOps**
  - can you create a git repository
  - Create github repository with repo name Test-Repo-iceDemo

  - Upload file to github repo
  - Upload file nginx-deployment.yaml to git repo repo_url
  - Upload file file_name to git repo repo_url in branch branch_name

  - what are the available pipelines
  - what are the available NSO pipelines?

  - upload docker image pull pipeline in the git repo repo_url
  - upload corona scan pipeline in the git repo repo_url
  - upload default NSO pipeline in the git repo repo_url in branch branch_name


**Assisted development**
  - Can you find me sample yang model for l3vpn
  - can you find me sample yang model for RFS microservice
  - can you find me sample code for RFS microservice
  - Can you find sample code for rfs
  - Can you find sample yang models for cfs
  - Can you find sample yang module for cfs
  - Can you find sample java code for cfs
  - Can you find sample code for l3vpn
  - show content <repo_url>


## Feedback or Support Questions

Please contact us at [srinjcha@cisco.com](mailto:srinjcha@cisco.com).


[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/srinjoychak/iCE)
