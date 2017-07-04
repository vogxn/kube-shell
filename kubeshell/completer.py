from __future__ import absolute_import, unicode_literals, print_function
from subprocess import check_output
from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder import fuzzyfinder
import logging
import shlex
import json
import os
import os.path

from kubeshell.client import KubernetesClient
from kubeshell.parser import Parser

class KubectlCompleter(Completer):

    def __init__(self):
        self.inline_help = True
        self.namespace = ""
        self.kube_client = KubernetesClient()
        self.logger = logging.getLogger(__name__)

        try:
            DATA_DIR = os.path.dirname(os.path.realpath(__file__))
            DATA_PATH = os.path.join(DATA_DIR, 'data/cli.json')
            with open(DATA_PATH) as json_file:
                self.kubectl_dict = json.load(json_file)
            self.parser = Parser(DATA_PATH)
        except Exception as ex:
            self.logger.error("got an exception" + ex.message)

    def set_inline_help(self, val):
        self.inline_help = val

    def set_namespace(self, namespace):
        self.namespace = namespace

    def get_completions(self, document, complete_event, smart_completion=None):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        cmdline = document.text_before_cursor.strip()
        tokens = shlex.split(cmdline)
        _, suggestions = self.parser.parse_tokens(tokens)
        filtered_suggestions = fuzzyfinder(word_before_cursor, suggestions)
        for suggestion in filtered_suggestions:
            yield Completion(suggestion, -len(word_before_cursor), display=suggestion)

    def get_resources(self, resource, namespace="all"):
        resources = []
        try:
            config.load_kube_config()
        except  Exception as e:
            # TODO: log errors to log file
            return resources

        v1 = client.CoreV1Api()
        v1Beta1 = client.AppsV1beta1Api()
        extensionsV1Beta1 = client.ExtensionsV1beta1Api()
        autoscalingV1Api = client.AutoscalingV1Api()
        rbacAPi = client.RbacAuthorizationV1beta1Api()
        batchV1Api = client.BatchV1Api()
        batchV2Api = client.BatchV2alpha1Api()

        ret = None
        namespaced_resource = True

        if resource == "pod":
            ret = v1.list_pod_for_all_namespaces(watch=False)
        elif resource == "service":
            ret = v1.list_service_for_all_namespaces(watch=False)
        elif resource == "deployment":
            ret = v1Beta1.list_deployment_for_all_namespaces(watch=False)
        elif resource == "statefulset":
            ret = v1Beta1.list_stateful_set_for_all_namespaces(watch=False)
        elif resource == "node":
            namespaced_resource = False
            ret = v1.list_node(watch=False)
        elif resource == "namespace":
            namespaced_resource = False
            ret = v1.list_namespace(watch=False)
        elif resource == "daemonset":
            ret = extensionsV1Beta1.list_daemon_set_for_all_namespaces(watch=False)
        elif resource == "networkpolicy":
            ret = extensionsV1Beta1.list_network_policy_for_all_namespaces(watch=False)
        elif resource == "thirdpartyresource":
            namespaced_resource = False
            ret = extensionsV1Beta1.list_third_party_resource(watch=False)
        elif resource == "replicationcontroller":
            ret = v1.list_replication_controller_for_all_namespaces(watch=False)
        elif resource == "replicaset":
            ret = extensionsV1Beta1.list_replica_set_for_all_namespaces(watch=False)
        elif resource == "ingress":
            ret = extensionsV1Beta1.list_ingress_for_all_namespaces(watch=False)
        elif resource == "endpoints":
            ret = v1.list_endpoints_for_all_namespaces(watch=False)
        elif resource == "configmap":
            ret = v1.list_config_map_for_all_namespaces(watch=False)
        elif resource == "event":
            ret = v1.list_event_for_all_namespaces(watch=False)
        elif resource == "limitrange":
            ret = v1.list_limit_range_for_all_namespaces(watch=False)
        elif resource == "configmap":
            ret = v1.list_config_map_for_all_namespaces(watch=False)
        elif resource == "persistentvolume":
            namespaced_resource = False
            ret = v1.list_persistent_volume(watch=False)
        elif resource == "secret":
            ret = v1.list_secret_for_all_namespaces(watch=False)
        elif resource == "resourcequota":
            ret = v1.list_resource_quota_for_all_namespaces(watch=False)
        elif resource == "componentstatus":
            namespaced_resource = False
            ret = v1.list_component_status(watch=False)
        elif resource == "podtemplate":
            ret = v1.list_pod_template_for_all_namespaces(watch=False)
        elif resource == "serviceaccount":
            ret = v1.list_service_account_for_all_namespaces(watch=False)
        elif resource == "horizontalpodautoscaler":
            ret = autoscalingV1Api.list_horizontal_pod_autoscaler_for_all_namespaces(watch=False)
        elif resource == "clusterrole":
            namespaced_resource = False
            ret = rbacAPi.list_cluster_role(watch=False)
        elif resource == "clusterrolebinding":
            namespaced_resource = False
            ret = rbacAPi.list_cluster_role_binding(watch=False)
        elif resource == "job":
            ret = batchV1Api.list_job_for_all_namespaces(watch=False)
        elif resource == "cronjob":
            ret = batchV2Api.list_cron_job_for_all_namespaces(watch=False)
        elif resource == "scheduledjob":
            ret = batchV2Api.list_scheduled_job_for_all_namespaces(watch=False)

        if ret:
            for i in ret.items:
                if namespace == "all" or not namespaced_resource:
                    resources.append((i.metadata.name, i.metadata.namespace))
                elif namespace == i.metadata.namespace:
                    resources.append((i.metadata.name, i.metadata.namespace))
            return resources
        return None

