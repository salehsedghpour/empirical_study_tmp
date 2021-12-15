"""
The experiment sizing is just a measurement of the capacity of system
The capacity is defined by the average throughput when the average 95th percentile response times reaches to 100ms
"""
from kubernetes import client, config
import utils, yaml, logging, time, re
from kubernetes.stream import stream


config.load_kube_config()
deployment_api = client.AppsV1Api()
logging.basicConfig(format='%(asctime)s - [%(levelname)s]  %(message)s', datefmt='%d/%m/%Y %I:%M:%S', level=logging.INFO)

with open('../yaml-files/Deployment/loadgenerator.yaml') as f:
    dep = yaml.safe_load(f)
    traffic_scenario = """
    for j in {100..500..10};
              do
                 setConcurrency $j;
                 sleep 15;
              done
    """
    dep['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
utils.create_deployment(deployment_api, dep, cpu="2000m", memory="2000Mi")

f.close()
logging.info("Wait {wait_time} seconds for experiment sizing to be done.".format(wait_time="650"))

time.sleep(650)

pod_name = ""
api_instance = client.CoreV1Api()

pods = api_instance.list_namespaced_pod("default").items
for pod in pods:
    if pod.metadata.labels['service.istio.io/canonical-name'] == "loadgenerator":
        pod_name = pod.metadata.name
exec_command = [
    '/bin/sh',
    '-c',
    'echo This message goes to stdout; cat httpmon.log'
]
api_response = stream(api_instance.connect_get_namespaced_pod_exec,
                      pod_name,
                      'default',
                      container='main',
                      command=exec_command,
                      stderr=True,
                      stdin=False,
                      stdout=True,
                      tty=False,
                      _preload_content=True)
response_times = re.findall(r"latency95=(\d+)", api_response)


throughput = re.findall(r"throughput=(\d+)", api_response)



occurance_num = 20
occurance_index = 0
for i in range(len(response_times)):
    if i > occurance_num:
        all_more_than_100 = 0
        for j in range(occurance_num):
            if int(response_times[i-j]) > 100:
                all_more_than_100 = all_more_than_100 + 1
        if all_more_than_100 == occurance_num:
            occurance_index = i
            break

capacity_sum = 0
for i in range(occurance_num-1):
    capacity_sum = capacity_sum + int(throughput[occurance_index-i])

logging.info("The capacity is calculated as follows")
print("Capacity is: ", int(capacity_sum/occurance_num))

utils.delete_deployment(deployment_api, "loadgenerator")

