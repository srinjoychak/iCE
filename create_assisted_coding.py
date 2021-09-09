from chatterbot.logic import LogicAdapter
from collections import defaultdict
import requests
import json
import re

class AssistDev(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)
        self.GIT_BASE_URL = 'https://wwwin-github.cisco.com'

    def can_process(self, statement):
        if 'Can you find sample'.lower() in statement.text.lower():
            return True
        elif 'Can you find me sample'.lower() in statement.text.lower():
            return True
        elif 'Show content'.lower() in statement.text.lower():
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement
        import webbrowser as web

        if 'can you find' in input_statement.text.lower():
            return_request = self.read_content_txt(input_statement.text)
            ret = return_request
        else:
            dest = input_statement.text.split(" ")[-1]
            web.open(dest, new=2)
            ret = 'ok sure'

        if ret:
            confidence = 1
        else:
            confidence = 0

        response_statement = Statement(text=ret)
        response_statement.confidence = confidence
        return response_statement


    def read_content_txt(self,request):
        search_param = self.refine_request(request)
        search_result = self.form_url(self.analyze_data(search_param ))
        data = ('*********** Top-Repositories *********** \n'+'\n'.join(search_result[0])+' \n*********** Specific-Links *********** \n'+'\n'.join(search_result[1])) if search_result[0] else 'Sorry Found Nothing'
        return data


    def analyze_data(self,search_param):
        analysis_results, dct = {}, defaultdict(list)

        for item in self.git_data():
            if all(i.lower() in item['name'].lower() for i in search_param):
                repo_name = (re.search('repos/(.*)/contents',item['repo_url'])).group(1)
                branch_name = item['repo_url'].split('?ref=')[-1]
                #dct[repo_name].append(branch_name)
                f_path = (re.search('contents/(.*)ref=',item['repo_url'])).group(1)
                file_br_path = branch_name + '/' + ''.join([i+'/' for i in f_path.split('/')][0:-1])
                dct[repo_name].append(file_br_path)

        for k,v in dct.items():
            analysis_results[k] = list(set(v))

        return analysis_results



    def git_data(self):
        json_data = []
        git_data_path = './Git_Data/GitContent_ALL'

        with open(git_data_path,'rb') as f:
            for line in f:
                try:
                    json_data.append(json.loads(line.strip()))
                except Exception as e:
                    print(e)
        return self.flatten(json_data)


    def refine_request(self,request):
        from nltk.corpus import stopwords

        ignr_w = ['models', 'model', 'code']
        s = set(stopwords.words('english'))
        txt = request.split('sample')[-1]
        data = list(filter(lambda w: not w in s, txt.split()))
        return ([ i for i in data if not i in ignr_w ])


    def form_url(self,data):
        top_repo, url_list = [], []
        for k,v in data.items():
            top_repo.append(self.GIT_BASE_URL + '/'+ k)
            [url_list.append(self.GIT_BASE_URL + '/'+ k + '/tree/' + items) for items in v]

        return [ top_repo,url_list ]


    def get_requests(self, url):
        #User needs to generate Git API token from https://wwwin-github.cisco.com/
        git_token = '6ccd14a3c5b7cb77d44ea9024102bf920a5b067a'
        headers = { "Accept":"application/vnd.github.v3+json","Authorization": "token %s"%git_token }
        try:
            r = requests.get(url,headers=headers)
        except Exception as e:
            print(e)
        data = r.json()
        return (data)


    def flatten(self,x):
        return [i for l in x for i in l]