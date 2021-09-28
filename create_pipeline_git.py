from chatterbot.logic import LogicAdapter
import git
#from git import Repo, RemoteReference
import json
import requests

class GitManagement(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)

        self.repo_base_dir = './git-test/'
        self.git_api_url_new_repo = 'https://wwwin-github.cisco.com/api/v3/user/repos'
        self.git_api_url_ice_master = 'https://wwwin-github.cisco.com/api/v3/repos/srinjcha/iCE_Master/contents'

        self.pipeline_dict = {
            'default nso' : 'NSO_cisco_internal.groovy',
            'docker image pull' : 'DockerPublish.groovy',
            'image pull s3' : 'Image_pull_S3',
            'corona scan' : 'corona-integration.groovy'
        }

    def can_process(self, statement):
        if 'Create github repository with repo name'.lower() in statement.text.lower():
            return True
        elif all(i in statement.text.lower().split(' ') for i in 'upload in the git repo'.lower().split(' ')):
            return True
        elif all(i in statement.text.lower().split(' ') for i in 'upload file to git repo'.lower().split(' ')):
            return True
        elif all(i in statement.text.lower().split(' ') for i in 'Can you clone the file'.lower().split(' ')):
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement
        import re
        import os
        import shutil

        file_base_dir = './upload/'
        ret = ''
        stmt = input_statement.text

        if 'Create github repository with repo name'.lower() in stmt.lower():
            new_repo_name = stmt.split(' ')[-1]
            new_repo = self.create_git_repo(new_repo_name)
            ret = "New repo created %s"%new_repo['git_url']
        elif all(i in stmt.lower().split(' ') for i in 'upload file to git repo'.lower().split(' ')):
            branch_name = ''
            if 'in branch' in stmt.lower():
                f_name = (re.search('file (.*) to',stmt.lower())).group(1)
                c_repo = (re.search('repo (.*) in',stmt.lower())).group(1)
                branch_name = (re.search('branch (.*)',stmt.lower())).group(1)
            else:
                f_name = (re.search('file (.*) to',stmt.lower())).group(1)
                c_repo = (re.search('repo (.*)',stmt.lower())).group(1)

            c_repo_name = (c_repo.split('/'))[-1].replace('.git','')
            c_repo_path = '{}{}'.format(self.repo_base_dir,c_repo_name)
            f_path = '{}{}'.format(file_base_dir,f_name)
            repo_cloned = os.path.exists(c_repo_path)
            print("Repo exists") if repo_cloned else self.git_clone(c_repo)
            os.replace(f_path,'{}/{}'.format(c_repo_path,f_name))
            ret = (self.git_push(c_repo_path,'User file uploaded by iCE',branch_name,f_name) if branch_name else self.git_push(c_repo_path,'User file uploaded by iCE'))+" in repo "+c_repo
            print("Next should be deleting the cloned repo but there is os.remove issue with Windows system, hence its disabled.")
            #shutil.rmtree(c_repo_path)

        elif all(i in stmt.lower().split(' ') for i in 'upload pipeline in the git repo'.lower().split(' ')):
            branch_name = ''
            if 'in branch' in stmt.lower():
                p_name = self.pipeline_dict[(re.search('upload (.*) pipeline',stmt.lower())).group(1)]
                c_repo = (re.search('repo (.*) in',stmt.lower())).group(1)
                branch_name = (re.search('branch (.*)',stmt.lower())).group(1)
            else:
                p_name = self.pipeline_dict[(re.search('upload (.*) pipeline',stmt.lower())).group(1)]
                c_repo = (re.search('repo (.*)',stmt.lower())).group(1)

            c_repo_name = (c_repo.split('/'))[-1].replace('.git','')
            c_repo_path = '{}{}'.format(self.repo_base_dir,c_repo_name)

            #Clone customer Repo
            repo_cloned = os.path.exists(c_repo_path)
            print("Repo exists") if repo_cloned else self.git_clone(c_repo)

            #Download requested pipeline from Master repo
            self.file_download_masterepo(p_name,c_repo_path)

            #Push file to requested repository at requested branch
            ret = (self.git_push(c_repo_path,'iCE committed this',branch_name,p_name) if branch_name else self.git_push(c_repo_path,'iCE committed this'))+" in repo "+c_repo

            print("Next should be deleting the cloned repo but there is os.remove issue with Windows system, hence its disabled.")
            #shutil.rmtree(c_repo_path)

        elif all(i in stmt.lower().split(' ') for i in 'Can you clone the file'.lower().split(' ')):
            branch_name = ''

            if 'in branch' in stmt.lower():
                f_name = (re.search('file (.*) from',stmt)).group(1)
                s_repo = (re.search('repo (.*) to',stmt)).group(1)
                d_repo = (re.search('to (.*) in',stmt)).group(1)
                branch_name = stmt.split(' ')[-1]
            else:
                f_name = (re.search('file (.*) from',stmt)).group(1)
                s_repo = (re.search('repo (.*) to',stmt)).group(1)
                d_repo = (re.search('to (.*)',stmt)).group(1)

            s_br_name = (s_repo.split('tree/')[-1]).split('/')[0]
            d_repo_name = (d_repo.split('/'))[-1].replace('.git','')
            d_repo_path = '{}{}'.format(self.repo_base_dir,d_repo_name)

            item = self.find_dld_url(f_name,s_br_name)
            repo_cloned = os.path.exists(d_repo_path)
            print("Repo exists") if repo_cloned else self.git_clone(d_repo)
            self.download_file(item['name'],item['repo_url'],d_repo_path)
            ret = (self.git_push(d_repo_path,'iCE committed this',branch_name,f_name) if branch_name else self.git_push(d_repo_path,'iCE committed this'))+" in repo "+d_repo


        if ret:
            confidence = 1
        else:
            confidence = 0

        response_statement = Statement(text=ret)
        response_statement.confidence = confidence
        return response_statement



    def create_git_repo(self,repo_name):
        #User needs to generate Git API token from https://wwwin-github.cisco.com/
        token = '<Update_GIT_API-Token>'
        headers = {"Authorization": "token %s"%token, "Accept":"application/vnd.github.v3+json"}
        payload = '{ \"name\":\"%s\" }'%repo_name

        r = requests.post(self.git_api_url_new_repo, data=payload, headers=headers)
        data = r.json()
        g_url = data['git_url'].replace('git://','https://')
        git_details = { 'html_url' : data['html_url'], 'git_url' : g_url }
        return (git_details)

    def get_file_list_master_repo(self):
        headers = {"Accept":"application/vnd.github.v3+json"}
        r = requests.get(self.git_api_url_ice_master)
        data = r.json()
        return (data)

    def git_clone(self,repo_url):
        git.Git(self.repo_base_dir).clone(repo_url)
        print('Successfully cloned')

    def file_download_masterepo(self,p_name,c_repo_path):
        for item in self.get_file_list_master_repo():
            if item['name'] == p_name:
                self.download_file(item['name'], item['download_url'], c_repo_path)

    def download_file(self,f_name,f_url,repo_path):
        f = '{}/{}'.format(repo_path,f_name)
        r = requests.get(f_url, allow_redirects=True)
        open(f,'wb').write(r.content)
        print('Successfully downloaded the file')

    def git_push(self,repo_path,commit_msg,branch=None,filenames=None):
        branch_name = branch if branch else 'master'
        repo = git.Repo(repo_path)
        origin = repo.remote(name='origin')
        repo.git.checkout(branch_name) if branch_name in [h.name for h in repo.heads] else repo.git.checkout('-b', branch_name)
        repo.remote().fetch()
        file_s = filenames if filenames else '--all'
        repo.git.add(file_s)
        repo.git.commit('-m', commit_msg)
        origin.push(branch_name)
        return ('Successfully pushed the files to branch %s'%branch_name)

    def git_data(self):
        json_data = []
        #There is a separate scanner program recursively pulling data from all Git orgs, their repos and from each branch.
        # The data will be stored in a NoSQL DB, but for the POC we are using a flat-file and storing data as JSON.

        with open('./Git_Data/GitContent_ALL','rb') as f:
            for line in f:
                try:
                    json_data.append(json.loads(line.strip()))
                except Exception as e:
                    print(e)
        return self.flatten(json_data)

    def find_dld_url(self,file_name,branch_name):
        for item in self.git_data():
            if file_name == item['name']:
                br_name = (item['repo_url'].split('?ref='))[-1]
                if branch_name == br_name:
                    return item

    def flatten(self,x):
        return [i for l in x for i in l]
