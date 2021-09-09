from chatterbot.logic import LogicAdapter
from kubernetes import client, config, watch
from kubernetes.client import ApiException
import json

class GetK8sPods(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        ().__init__(chatbot, **kwargs)

    def can_process(self, statement):
        str = 'Get me pods from namespace'
        if all(x in [i.lower() for i in statement.text.split()] for x in ['pods', 'all','namespaces']):
            return True
        if 'Get me pods from namespace'.lower() in statement.text.lower():
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement

        k8s_config = config.load_kube_config('config')
        k8s_core_v1 = client.CoreV1Api()
        ret, output = '', []

        try:
            if all(x in [i.lower() for i in input_statement.text.split()] for x in ['pods', 'all','namespaces']):
                ret = k8s_core_v1.list_pod_for_all_namespaces(watch=False)
            elif 'Get me pods from namespace'.lower() in input_statement.text.lower():
                ns_name = input_statement.text.split(' ')[-1]
                ret = k8s_core_v1.list_namespaced_pod(ns_name)

            for i in ret.items:
                output.append("{}\t{}\t{}\t{}".format(i.status.pod_ip, i.metadata.namespace, i.metadata.name, i.status.phase))
        except ApiException as e:
            err = json.loads(e.body)
            output.append(err['message'])

        if len(output) > 0:
            confidence = 1
        else:
            confidence = 0

        total_output = ' \n'.join([elem for elem in output])
        response_statement = Statement(text=total_output)
        response_statement.confidence = confidence
        return response_statement