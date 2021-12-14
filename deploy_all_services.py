"""Deploy all services (online boutique) with to the cluster"""
from kubernetes import client, config
import utils, yaml, logging, time


config.load_kube_config()
deployment_api = client.AppsV1Api()
core_api = client.CoreV1Api()
logging.basicConfig(format='%(asctime)s - [%(levelname)s]  %(message)s', datefmt='%d/%m/%Y %I:%M:%S', level=logging.INFO)


layer_1_services = ["frontend"]
layer_2_services = ["adservice", "checkoutservice", "recommendationservice"]
layer_3_services = ["cartservice", "shippingservice", "emailservice", "paymentservice", "currencyservice",
                    "productcatalogservice"]
layer_4_services = ["redis-cart"]
all_services = layer_1_services + layer_2_services + layer_3_services + layer_4_services

configuration = {
    "svc_cpu": "2000m",
    "svc_memory": "2000Mi",
    "deployment_wait_time": 180
}


for service in all_services:
    with open('./yaml-files/Deployment/' + service + '.yaml') as f:
        dep = yaml.safe_load(f)
        utils.create_deployment(deployment_api, dep, cpu=configuration['svc_cpu'],
                                memory=configuration['svc_memory'])
        deployment_api.delete_deployment
    f.close()
    with open('./yaml-files/Service/' + service + '.yaml') as f:
        dep = yaml.safe_load(f)
        utils.create_service(core_api, dep)
    f.close()

logging.info("Wait {wait_time} seconds for all services to be up and running.".format(wait_time=configuration['deployment_wait_time']))
time.sleep(configuration['deployment_wait_time'])

