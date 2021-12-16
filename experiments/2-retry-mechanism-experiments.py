'''Different retry mechanism will applied on different layers with different values'''

from kubernetes import client, config
import utils, yaml, logging, time, datetime, csv

config.load_kube_config()
deployment_api = client.AppsV1Api()
customobject_api = client.CustomObjectsApi()
logging.basicConfig(format='%(asctime)s - [%(levelname)s]  %(message)s', datefmt='%d/%m/%Y %I:%M:%S', level=logging.INFO)

configuration = {
    # Services deployment configuration
    "svc_cpu": "2000m",
    "svc_memory": "2000Mi",
    "deployment_wait_time": 30,
    "configure_wait_time": 30,
    # experiment configurations
    "cb_values": [1, 20, 1024],
    "retry_attempts": [1, 2, 10],
    "retry_timeouts": ["25ms", "5s", "20s"],
    "static_traffic_ratio": [0.8, 1,1.2],
    "dynamic_traffic_ratio": 0.8,
    "dynamic_traffic_spike_ration": [0.2, 0.4, 0.5],
    "dynamic_traffic_spike_duration": 5,
    "dynamic_traffic_duration": 60,
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
    def deploy_loadgenerator(traffic_scenario):
        for service in loadgenerator_service:
            with open('../yaml-files/Deployment/' + service + '.yaml') as f:
                dep = yaml.safe_load(f)
                dep['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
                utils.create_deployment(deployment_api, dep, cpu=configuration['svc_cpu'],
                                        memory=configuration['svc_memory'])
        logging.info("Wait {wait_time} seconds for loadgenerator to be deployed.".format(
            wait_time=configuration['deployment_wait_time']))
        time.sleep(configuration['deployment_wait_time'])
        logging.info("Loadgenerator is deployed successfully with {cpu} CPU and {memory}"
                     " memory".format(cpu=configuration['svc_cpu'], memory=configuration['svc_memory']))

    layer_1_services = ["frontend"]
    layer_2_services = ["adservice", "checkoutservice", "recommendationservice"]
    layer_3_services = ["cartservice", "shippingservice", "emailservice", "paymentservice", "currencyservice",
                        "productcatalogservice"]
    layer_4_services = ["redis-cart"]
    loadgenerator_service = ["loadgenerator"]
    all_services = layer_1_services + layer_2_services + layer_3_services + layer_4_services

    # Touch the log file
    file_name = "retry-experiments.log"
    with open(configuration['log_dir'] + file_name, 'a') as csv_file:
        fieldnames = ['cpu', 'memory', 'configured_layers', 'traffic_ratio','spike_ratio', 'circuit_breaker',
                      'retry_attempts','retry_timeout', 'start', 'end', 'attempt']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        csv_file.close()

    def retry_storm():
        # experiments for value of retry
        # deploy the load generator
        traffic_ratio = 1
        concurrency_value = int(traffic_ratio * configuration['capacities']['online_boutique'])
        experiment_duration = configuration['experiment_duration']
        traffic_scenario = "setConcurrency {concurrency}; sleep {duration};".format(concurrency=concurrency_value,
                                                                                    duration=experiment_duration)
        deploy_loadgenerator(traffic_scenario)
        for cb in configuration["cb_values"]:
            # configuration on all layers
            logging.info("Starting the experiments for all layers")
            for service in layer_3_services:
                utils.create_retry(customobject_api, service, 2, "1ms")
                utils.create_circuit_breaker(customobject_api, service, cb)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for configuring retry.".format(
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
                        configuration['svc_cpu'], # cpu
                        configuration['svc_memory'], # memory
                        'all', # configured_layers
                        traffic_ratio,  #traffic_ratio
                        0, # spike_ratio
                        cb, # circuit_breaker
                        2, # retry_attempts
                        '',# retry_timeouts
                        start, # start
                        end, # end
                        i, # attempt
                    ])
                    csv_file.close()
                logging.info('''The following experiment  is done:
                                                                                            Attempt number: {attempt}
                                                                                            Circuit breaker: {cb}
                                                                                            Configured Layers: all
                                                                                            Traffic ratio: {ratio}
                                                                                            Start TS: {start}
                                                                                            End TS: {end}
                                                                                            Spike ratio: {spike}
                                                                                            Retry attempts: {retry}
                                                                                            Retry timeouts: {timeout} 
                                                        '''.format(attempt=i, cb=cb, ratio=traffic_ratio, start=start,
                                                                   end=end, spike=0, retry=2, timeout=''))

            for service in layer_3_services:
                utils.delete_retry(customobject_api, service)
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

    def retry_attempts():
        #experiments for value of retry
        #deploy the load generator
        traffic_ratio = 1
        concurrency_value = int(traffic_ratio * configuration['capacities']['online_boutique'])
        experiment_duration = configuration['experiment_duration']
        traffic_scenario = "setConcurrency {concurrency}; sleep {duration};".format(concurrency=concurrency_value,
                                                                                        duration=experiment_duration)
        deploy_loadgenerator(traffic_scenario)
        for retry in configuration["retry_attempts"]:
            # configuration on just productcatalogservices
            for service in layer_3_services:
                cb = 1
                utils.create_circuit_breaker(customobject_api, service, cb)
                utils.create_retry(customobject_api, service, retry, "1ms")

            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for configuring retry and cb.".format(
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
                        configuration['svc_cpu'], # cpu
                        configuration['svc_memory'], # memory
                        'all', # configured_layers
                        traffic_ratio,  #traffic_ratio
                        0, # spike_ratio
                        cb, # circuit_breaker
                        retry, # retry_attempts
                        '',# retry_timeouts
                        start, # start
                        end, # end
                        i, # attempt

                    ])
                    csv_file.close()
                logging.info('''The following experiment  is done:
                                                                                            Attempt number: {attempt}
                                                                                            Circuit breaker: {cb}
                                                                                            Configured Layers: all
                                                                                            Traffic ratio: {ratio}
                                                                                            Start TS: {start}
                                                                                            End TS: {end}
                                                                                            Spike ratio: {spike}
                                                                                            Retry attempts: {retry}
                                                                                            Retry timeouts: {timeout} 
                                                        '''.format(attempt=i, cb=cb, ratio=traffic_ratio, start=start,
                                                                   end=end, spike=0, retry=retry, timeout=''))

            for service in layer_3_services:
                utils.delete_retry(customobject_api, service)
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

    def retry_timeouts():
        # experiments for value of retry
        # deploy the load generator
        traffic_ratio = 1
        concurrency_value = int(traffic_ratio * configuration['capacities']['online_boutique'])
        experiment_duration = configuration['experiment_duration']
        traffic_scenario = "setConcurrency {concurrency}; sleep {duration};".format(concurrency=concurrency_value,
                                                                                    duration=experiment_duration)
        deploy_loadgenerator(traffic_scenario)
        for timeout in configuration["retry_timeouts"]:
            # configuration on all layers
            logging.info("Starting the experiments for all layers")
            retry = 10
            for service in layer_3_services:
                utils.create_retry(customobject_api, service, retry, timeout)
                utils.create_circuit_breaker(customobject_api, service, 20)
            time.sleep(configuration['configure_wait_time'])
            logging.info("Wait {wait_time} seconds for configuring retry and cb.".format(
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
                        configuration['svc_cpu'], # cpu
                        configuration['svc_memory'], # memory
                        'all', # configured_layers
                        traffic_ratio,  #traffic_ratio
                        0, # spike_ratio
                        30, # circuit_breaker
                        retry, # retry_attempts
                        timeout,# retry_timeouts
                        start, # start
                        end, # end
                        i, # attempt

                    ])
                    csv_file.close()
                logging.info('''The following experiment  is done:
                                                                                            Attempt number: {attempt}
                                                                                            Circuit breaker: {cb}
                                                                                            Configured Layers: all
                                                                                            Traffic ratio: {ratio}
                                                                                            Start TS: {start}
                                                                                            End TS: {end}
                                                                                            Spike ratio: {spike}
                                                                                            Retry attempts: {retry}
                                                                                            Retry timeouts: {timeout} 
                                                        '''.format(attempt=i, cb=1, ratio=traffic_ratio, start=start,
                                                                   end=end, spike=0, retry=retry, timeout=timeout))
            for service in layer_3_services:
                utils.delete_retry(customobject_api, service)
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

    def retry_timeouts_spikes():
        # experiments for value of retry
        for spike in configuration['dynamic_traffic_spike_ration']:
            # deploy the load generator
            traffic_ratio = configuration['dynamic_traffic_ratio']
            spike_value = int(configuration['capacities']['online_boutique']* (1+spike))
            concurrency_value = int(traffic_ratio * configuration['capacities']['online_boutique'])
            experiment_duration = configuration['experiment_duration']
            traffic_scenario = "for i in {{1..10000}}; do setConcurrency {concurrency_l}; sleep {duration_l}; setConcurrency {concurrency_s}; sleep {duration_s}; done".format(concurrency_l=concurrency_value,
                                                                                                    duration_l=configuration['dynamic_traffic_duration'],
                                                                                                    concurrency_s=spike_value,
                                                                                                    duration_s=configuration['dynamic_traffic_spike_duration'])

            deploy_loadgenerator(traffic_scenario)
            for timeout in configuration["retry_timeouts"]:
                # configuration on all layers
                logging.info("Starting the experiments for all layers")
                retry = 10
                for service in layer_3_services:
                    utils.create_retry(customobject_api, service, retry, timeout)
                    utils.create_circuit_breaker(customobject_api, service, 20)
                time.sleep(configuration['configure_wait_time'])
                logging.info("Wait {wait_time} seconds for configuring retry and cb.".format(
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
                            configuration['svc_cpu'], # cpu
                            configuration['svc_memory'], # memory
                            'all', # configured_layers
                            traffic_ratio,  #traffic_ratio
                            spike, # spike_ratio
                            20, # circuit_breaker
                            retry, # retry_attempts
                            timeout,# retry_timeouts
                            start, # start
                            end, # end
                            i, # attempt
                        ])
                        csv_file.close()
                    logging.info('''The following experiment  is done:
                                                                                                Attempt number: {attempt}
                                                                                                Circuit breaker: {cb}
                                                                                                Configured Layers: all
                                                                                                Traffic ratio: {ratio}
                                                                                                Start TS: {start}
                                                                                                End TS: {end}
                                                                                                Spike ratio: {spike}
                                                                                                Retry attempts: {retry}
                                                                                                Retry timeouts: {timeout} 
                                                            '''.format(attempt=i, cb=1, ratio=traffic_ratio, start=start,
                                                                       end=end, spike=0, retry=retry, timeout=timeout))

                for service in layer_3_services:
                    utils.delete_retry(customobject_api, service)
                    utils.delete_circuit_breaker(customobject_api, service)
                time.sleep(configuration['configure_wait_time'])
                logging.info("Wait {wait_time} seconds for removing cb.".format(
                    wait_time=configuration['configure_wait_time']))
                logging.info("The experiments for all layers ended")
                # end all layer experimentation
            for service in loadgenerator_service:
                logging.info("Deleting all load generator services ...")
                utils.delete_deployment(deployment_api, service)
    def different_locations():
        # experiments for value of retry
        # deploy the load generator
        traffic_ratio = 1
        concurrency_value = int(traffic_ratio * configuration['capacities']['online_boutique'])
        experiment_duration = configuration['experiment_duration']
        traffic_scenario = "setConcurrency {concurrency}; sleep {duration};".format(concurrency=concurrency_value,
                                                                                    duration=experiment_duration)
        deploy_loadgenerator(traffic_scenario)
        cb= 20
        retry_attempt = 2
        retry_timeout = "5s"
        for layer_cb in [1,2,3,'all']:
            for layer_retry in [1,2,3,'all']:
                if layer_cb == 1:
                    layer_cb_list = layer_1_services
                elif layer_cb == 2:
                    layer_cb_list = layer_2_services
                elif layer_cb == 3:
                    layer_cb_list = layer_3_services
                elif layer_cb == "all":
                    layer_cb_list = all_services
                if layer_retry == 1:
                    layer_retry_list = layer_1_services
                elif layer_retry == 2:
                    layer_retry_list = layer_2_services
                elif layer_retry == 3:
                    layer_retry_list = layer_3_services
                elif layer_retry == "all":
                    layer_retry_list = all_services
                for cb_service in layer_cb_list:
                    utils.create_circuit_breaker(customobject_api, cb_service, cb)
                for retry_service in layer_retry_list:
                    utils.create_retry(customobject_api, retry_service, retry_attempt, retry_timeout)
                logging.info("Wait {wait_time} seconds for configuring cb.".format(
                    wait_time=configuration['configure_wait_time']))
                time.sleep(configuration['configure_wait_time'])
                logging.info("Performing the experiments")
                for i in range(configuration['repeat_factor']):
                    start = str(int(time.time() * 1000) - configuration['experiment_time_margin']['start'])
                    time.sleep(configuration['single_experiment_duration'])
                    end = str(int(time.time() * 1000) + configuration['experiment_time_margin']['end'])

                    # write to the csv
                    with open(configuration['log_dir'] + file_name, 'a') as csv_file:
                        writer = csv.writer(csv_file, delimiter=",")
                        configuration['svc_cpu'],  # cpu
                        configuration['svc_memory'],  # memory
                        'all',  # configured_layers
                        traffic_ratio,  # traffic_ratio
                        spike,  # spike_ratio
                        20,  # circuit_breaker
                        retry,  # retry_attempts
                        timeout,  # retry_timeouts
                        start,  # start
                        end,  # end
                        i,  # attempt
                        writer.writerow([
                            configuration['svc_cpu'],
                            configuration['svc_memory'],
                            str([layer_cb,layer_retry]),
                            traffic_ratio,
                            0,  # spike_ratio
                            cb,
                            0,  # retry_attempts
                            0,  # retry_timeouts
                            start,
                            end,
                            i,

                        ])
                        csv_file.close()
                    logging.info('''The following experiment  is done:
                                                        Attempt number: {attempt}
                                                        Circuit breaker: {cb}
                                                        Configured Layers: 1
                                                        Traffic ratio: {ratio}
                                                        Start TS: {start}
                                                        End TS: {end}
                    '''.format(attempt=i, cb=cb, ratio=traffic_ratio, start=start, end=end))
                    for service in layer_cb_list:
                        utils.delete_circuit_breaker(customobject_api, service)
                    for service in layer_retry_list:
                        utils.delete_retry(customobject_api,service)
                    time.sleep(configuration['configure_wait_time'])
                    logging.info("Wait {wait_time} seconds for removing cb.".format(
                        wait_time=configuration['configure_wait_time']))
                    logging.info("The experiments for first layer ended")
        for service in loadgenerator_service:
            logging.info("Deleting all load generator services ...")
            utils.delete_deployment(deployment_api, service)

    retry_storm()
    retry_attempts()
    retry_timeouts()
    retry_timeouts_spikes()
    different_locations()

online_boutique()



