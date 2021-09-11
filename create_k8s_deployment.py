from chatterbot.logic import LogicAdapter
from kubernetes import client, config, watch
from kubernetes.client import ApiException
from os import path
import yaml
import json


class CreateK8sDeployment(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)

    def can_process(self, statement):
        if 'Deploy with file'.lower() in statement.text.lower():
            return True
        elif 'Please delete deployment'.lower() in statement.text.lower():
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement

        k8s_config = config.load_kube_config('./upload/config')
        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()
        base_dir = './upload/'
        ret = ''

        s_str = input_statement.text.split(' ')

        if 'Deploy with file'.lower() in input_statement.text.lower():
            depl_file = '{}{}'.format(base_dir,s_str[3])
            ns_name = s_str[-1]
            deployment_ns = self.create_deployment(depl_file,ns_name)
            ret = 'Deployment created successfully Deployment Name: {} Namespace: {}'.format(deployment_ns,ns_name) if deployment_ns else 'Failed to create deployment in namespace {} with failure: {}'.format(ns_name,deployment_ns)
        elif 'Please delete deployment'.lower() in input_statement.text.lower():
            deployment_name = s_str[3]
            ns_name = s_str[-1]
            #delete_dep = self.delete_deployment(deployment_name,ns_name)
            ret = self.delete_deployment(deployment_name,ns_name)

        if ret:
            confidence = 1
        else:
            confidence = 0

        response_statement = Statement(text=ret)
        response_statement.confidence = confidence
        return response_statement

    def create_deployment(self,file,ns):
        with open(path.join(path.dirname(__file__), file)) as f:
            dep = yaml.safe_load(f)
            try:
                resp = self.k8s_apps_v1.create_namespaced_deployment(
                    body=dep, namespace=ns)
                return (resp.metadata.name)
            except ApiException as e:
                err = json.loads(e.body)
                return (err['message'])



    def delete_deployment(self,name,namespace):
        try:
            ret = self.k8s_apps_v1.delete_namespaced_deployment( name=name,namespace=namespace)
            return ret.status
        except ApiException as e:
            err = json.loads(e.body)
            return (err['message'])