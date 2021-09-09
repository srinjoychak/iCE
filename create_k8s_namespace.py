from chatterbot.logic import LogicAdapter
from kubernetes import client, config, watch
from kubernetes.client import ApiException
from os import path
import yaml
import json

class CreateK8sNamespace(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)

    def can_process(self, statement):
        if 'Please create namespace with file'.lower() in statement.text.lower():
            return True
        elif 'Please delete namespace'.lower() in statement.text.lower():
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement

        k8s_config = config.load_kube_config('config')
        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()
        base_dir = './upload/'
        ret = ''

        s_str = input_statement.text.split(' ')

        if 'Please delete namespace'.lower() in input_statement.text.lower():
            ns_name = s_str[-1]
            delete_ns = self.delete_namespace(ns_name)
            ret = 'Deleted namespace %s'%ns_name if delete_ns else 'Failed to delete namespace %s'%ns_name
        elif 'assign quota' in input_statement.text.lower():
            ns_file = '{}{}'.format(base_dir,s_str[5])
            ns_quota_file = '{}{}'.format(base_dir,s_str[-1])
            ns_name = self.create_namespace(ns_file)
            if ns_name:
                ns_quota = self.define_ns_quota(ns_name,ns_quota_file)
                ret = 'Created namespace %s with quota'%ns_name if ns_quota else 'Failed to create namespace %s with quota'%ns_name
            else:
                ret = 'Failed to create namespace'
        else:
            ns_file = '{}{}'.format(base_dir,s_str[-1])
            ns_name = self.create_namespace(ns_file)
            ret = 'Created namespace %s'%ns_name if ns_name else 'Failed to create namespace %s'%ns_name

        if ret:
            confidence = 1
        else:
            confidence = 0

        response_statement = Statement(text=ret)
        response_statement.confidence = confidence
        return response_statement

    def create_namespace(self,ns_file):
        try:
            with open(path.join(path.dirname(__file__), ns_file)) as f:
                dep = yaml.safe_load(f)
                resp = self.k8s_core_v1.create_namespace(body=dep)
                if resp.status.phase == 'Active':
                    return (resp.metadata.name)
        except ApiException as e:
            return False

    def define_ns_quota(self, ns_name,ns_quota_file):
        try:
            with open(path.join(path.dirname(__file__), ns_quota_file)) as f:
                dep = yaml.safe_load(f)
                resp = self.k8s_core_v1.create_namespaced_resource_quota(ns_name,dep)
                return True
        except ApiException as e:
            err = json.loads(e.body)
            return False #(err['message'])


    def delete_namespace(self,ns):
        try:
            resp = self.k8s_core_v1.delete_namespace(ns)
            if resp.status == "{'phase': 'Terminating'}":
                return True
        except ApiException as e:
            err = json.loads(e.body)
            return False #(err['message'])