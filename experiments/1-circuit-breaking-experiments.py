'''Different circuit breaking will applied on different layers with different values'''

from kubernetes import client, config
import utils, yaml, logging, time, csv

config.load_kube_config()
deployment_api = client.AppsV1Api()
customobject_api = client.CustomObjectsApi()
logging.basicConfig(format='%(asctime)s - [%(levelname)s]  %(message)s', datefmt='%d/%m/%Y %I:%M:%S', level=logging.INFO)

configuration = {
    # Services deployment configuration
    "svc_cpu": "2000m",
    "svc_memory": "2000Mi",
    "configure_wait_time": 30,
    "deployment_wait_time": 30,
    # experiment configurations
    "cb_values": [1, 20, 1024],
    "static_traffic_ratio": [0.8, 1,1.2],
    #
    #   The recorded capacity should be rewritten here.
    #
    "capacities": {
        # Update me
        "online_boutique": 230
    },
    "experiment_time_margin": {
        "start": 30,
        "end": 30
    },
    "experiment_duration": 360000,
    "single_experiment_duration": 300,
    "log_dir": "../logs/",
    "repeat_factor": 5,
}


def online_boutique():
    '''
    experiments for online boutique micro-service demo
    :return:
    '''
    layer_1_services = ["frontend"]
    layer_2_services = ["adservice", "checkoutservice", "recommendationservice"]
    layer_3_services = ["cartservice", "shippingservice", "emailservice", "paymentservice", "currencyservice",
                        "productcatalogservice"]
    layer_4_services = ["redis-cart"]
    all_services = layer_1_services + layer_2_services + layer_3_services + layer_4_services
    loadgenerator_service = ["loadgenerator"]

    # Touch the log file
    file_name = "cb-experiment.log"
    with open(configuration['log_dir']+file_name, 'a') as csv_file:
        fieldnames = ['cpu', 'memory', 'configured_layers', 'traffic_ratio', 'circuit_breaker', 'start', 'end', 'attempt']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        csv_file.close()

    # Deploy the load generator
    for traffic_ratio in configuration['static_traffic_ratio']:
        for service in loadgenerator_service:
            with open('../yaml-files/Deployment/' + service + '.yaml') as f:
                dep = yaml.safe_load(f)
                concurrency_value = int(traffic_ratio * configuration['capacities']['online_boutique'])
                experiment_duration = configuration['experiment_duration']
                traffic_scenario = "setConcurrency {concurrency}; sleep {duration};".format(concurrency=concurrency_value,
                                                                                            duration=experiment_duration)
                dep['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
                utils.create_deployment(deployment_api, dep, cpu=configuration['svc_cpu'],
                                        memory=configuration['svc_memory'])
        logging.info("Wait {wait_time} seconds for loadgenerator to be deployed.".format(
            wait_time=configuration['deployment_wait_time']))
        time.sleep(configuration['deployment_wait_time'])
        logging.info("Loadgenerator is deployed successfully with {cpu} CPU and {memory}"
                     " memory".format(cpu=configuration['svc_cpu'], memory=configuration['svc_memory']))

        # Now the configuration begins:
        for cb_value in configuration['cb_values']:
            # experimenting first layer
            logging.info("Starting the experiments for first layer")
            for service in layer_1_services:
                utils.create_circuit_breaker(customobject_api, service, cb_value)
            logging.info("Wait {wait_time} seconds for configuring cb.".format(wait_time=configuration['configure_wait_time']))
            time.sleep(configuration['configure_wait_time'])

            # Repeat of each single experiment
            logging.info("Performing the experiments")
            for i in range(configuration['repeat_factor']):
                start = str(int(time.time() * 1000) - configuration['experiment_time_margin']['start'])
                time.sleep(configuration['single_experiment_duration'])
                end = str(int(time.time() * 1000) + configuration['experiment_time_margin']['end'])

                # write to the csv
                with open(configuration['log_dir'] + file_name, 'a') as csv_file:
                    writer = csv.writer(csv_file, delimiter=",")
                    writer.writerow([
                        configuration['svc_cpu'],
                        configuration['svc_memory'],
                        1,
                        traffic_ratio,
                        cb_value,
                        start,
                        end,
                        i
                    ])
                    csv_file.close()
                logging.info('''The following experiment  is done:
                                                    Attempt number: {attempt}
                                                    Circuit breaker: {cb}
                                                    Configured Layers: 1
                                                    Traffic ratio: {ratio}
                                                    Start TS: {start}
                                                    End TS: {end}
                '''.format(attempt=i, cb=cb_value, ratio=traffic_ratio,start=start, end=end))
            for service in layer_1_services:
                utils.delete_circuit_breaker(customobject_api, service)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for removing cb.".format(
                wait_time=configuration['configure_wait_time']))
            logging.info("The experiments for first layer ended")
            # end first layer experimentation

            # experimenting second layer
            logging.info("Starting the experiments for second layer")
            for service in layer_2_services:
                utils.create_circuit_breaker(customobject_api, service, cb_value)
            logging.info("Wait {wait_time} seconds for configuring cb.".format(
                wait_time=configuration['configure_wait_time']))
            time.sleep(configuration['configure_wait_time'])

            # Repeat of each single experiment
            logging.info("Performing the experiments")
            for i in range(configuration['repeat_factor']):
                start = str(int(time.time() * 1000) - configuration['experiment_time_margin']['start'])
                time.sleep(configuration['single_experiment_duration'])
                end = str(int(time.time() * 1000) + configuration['experiment_time_margin']['end'])
                # write to the csv
                with open(configuration['log_dir'] + file_name, 'a') as csv_file:
                    writer = csv.writer(csv_file, delimiter=",")
                    writer.writerow([
                        configuration['svc_cpu'],
                        configuration['svc_memory'],
                        2,
                        traffic_ratio,
                        cb_value,
                        start,
                        end,
                        i
                    ])
                    csv_file.close()
                logging.info('''The following experiment  is done:
                                                                Attempt number: {attempt}
                                                                Circuit breaker: {cb}
                                                                Configured Layers: 2
                                                                Traffic ratio: {ratio}
                                                                Start TS: {start}
                                                                End TS: {end}
                            '''.format(attempt=i, cb=cb_value, ratio=traffic_ratio, start=start, end=end))

            for service in layer_2_services:
                utils.delete_circuit_breaker(customobject_api, service)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for removing cb.".format(
                wait_time=configuration['configure_wait_time']))
            logging.info("The experiments for second layer ended")
            # end second layer experimentation

            # experimenting third layer
            logging.info("Starting the experiments for third layer")
            for service in layer_3_services:
                utils.create_circuit_breaker(customobject_api, service, cb_value)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for configuring cb.".format(
                    wait_time=configuration['configure_wait_time']))
            # Repeat of each single experiment
            logging.info("Performing the experiments")
            for i in range(configuration['repeat_factor']):
                start = str(int(time.time() * 1000) - configuration['experiment_time_margin']['start'])
                time.sleep(configuration['single_experiment_duration'])
                end = str(int(time.time() * 1000) + configuration['experiment_time_margin']['end'])
                # write to the csv
                with open(configuration['log_dir'] + file_name, 'a') as csv_file:
                    writer = csv.writer(csv_file, delimiter=",")
                    writer.writerow([
                        configuration['svc_cpu'],
                        configuration['svc_memory'],
                        3,
                        traffic_ratio,
                        cb_value,
                        start,
                        end,
                        i,
                    ])
                    csv_file.close()
                logging.info('''The following experiment  is done:
                                                                Attempt number: {attempt}
                                                                Circuit breaker: {cb}
                                                                Configured Layers: 3
                                                                Traffic ratio: {ratio}
                                                                Start TS: {start}
                                                                End TS: {end}
                            '''.format(attempt=i, cb=cb_value, ratio=traffic_ratio, start=start, end=end))

            for service in layer_3_services:
                utils.delete_circuit_breaker(customobject_api, service)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for removing cb.".format(
                wait_time=configuration['configure_wait_time']))
            logging.info("The experiments for first layer ended")
            # end third layer experimentation

            # experimenting all layer
            logging.info("Starting the experiments for all layers")
            for service in all_services:
                utils.create_circuit_breaker(customobject_api, service, cb_value)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for configuring cb.".format(
                    wait_time=configuration['configure_wait_time']))
            # Repeat of each single experiment
            logging.info("Performing the experiments")
            for i in range(configuration['repeat_factor']):
                start = str(int(time.time() * 1000) - configuration['experiment_time_margin']['start'])
                time.sleep(configuration['single_experiment_duration'])
                end = str(int(time.time() * 1000) + configuration['experiment_time_margin']['end'])

                # write to the csv
                with open(configuration['log_dir'] + file_name, 'a') as csv_file:
                    writer = csv.writer(csv_file, delimiter=",")
                    writer.writerow([
                        configuration['svc_cpu'],
                        configuration['svc_memory'],
                        'all',
                        traffic_ratio,
                        cb_value,
                        start,
                        end,
                        i
                    ])
                    csv_file.close()
                logging.info('''The following experiment  is done:
                                                                            Attempt number: {attempt}
                                                                            Circuit breaker: {cb}
                                                                            Configured Layers: all
                                                                            Traffic ratio: {ratio}
                                                                            Start TS: {start}
                                                                            End TS: {end}
                                        '''.format(attempt=i, cb=cb_value, ratio=traffic_ratio, start=start, end=end))

            for service in all_services:
                utils.delete_circuit_breaker(customobject_api, service)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for removing cb.".format(
                wait_time=configuration['configure_wait_time']))
            logging.info("The experiments for all layers ended")
            # end all layer experimentation

    # Delete loadgenerator
    for service in loadgenerator_service:
        logging.info("Deleting all load generator services ...")
        utils.delete_deployment(deployment_api, service)





online_boutique()