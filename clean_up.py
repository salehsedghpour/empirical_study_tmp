"""Delete deployments, services, virtual services and destination rules in default namespace"""
from kubernetes import client, config
import utils, logging

config.load_kube_config()
deployment_api = client.AppsV1Api()
core_api = client.CoreV1Api()
custom_object_api = client.CustomObjectsApi()
logging.basicConfig(format='%(asctime)s - [%(levelname)s]  %(message)s', datefmt='%d/%m/%Y %I:%M:%S', level=logging.INFO)

deployments = deployment_api.list_namespaced_deployment("default")
services = core_api.list_namespaced_service("default")
destination_rules = custom_object_api.list_namespaced_custom_object(
    namespace = "default",
    group = "networking.istio.io",
    version = "v1alpha3",
    plural = "destinationrules"
)

virtual_services = custom_object_api.list_namespaced_custom_object(
    namespace = "default",
    group = "networking.istio.io",
    version = "v1alpha3",
    plural = "virtualservices"
)

for deployment in deployments.items:
    utils.delete_deployment(deployment_api, deployment.metadata.name)

for service in services.items:
    if service.metadata.name != "kubernetes":
        utils.delete_service(core_api, service.metadata.name)

for destination_rule in destination_rules['items']:
    custom_object_api.delete_namespaced_custom_object(
        namespace="default",
        group="networking.istio.io",
        version="v1alpha3",
        plural="destinationrules",
        name=destination_rule['metadata']['name']
    )
    logging.info("Circuit breaker for service %s is successfully deleted. " % (
    str(destination_rule['metadata']['name'])))

for virtual_service in virtual_services['items']:
    custom_object_api.delete_namespaced_custom_object(
        namespace="default",
        group="networking.istio.io",
        version="v1alpha3",
        plural="virtualservices",
        name=virtual_service['metadata']['name']
    )
    logging.info("Retry mechanism for service %s is successfully deleted. " % (
    str(virtual_service['metadata']['name'])))
