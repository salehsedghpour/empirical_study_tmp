import logging,yaml
from kubernetes.client.rest import ApiException


logging.basicConfig(format='%(asctime)s - [%(levelname)s]  %(message)s', datefmt='%d/%m/%Y %I:%M:%S', level=logging.INFO)


def create_deployment(api_instance, deployment, cpu=None, memory=None):
    """
    :param api_instance:
    :param deployment:
    :return:
    """
    try:
        if cpu:
            deployment['spec']['template']['spec']['containers'][0]['resources']['limits']['cpu'] = cpu
            deployment['spec']['template']['spec']['containers'][0]['resources']['requests']['cpu'] = cpu
        if memory:
            deployment['spec']['template']['spec']['containers'][0]['resources']['limits']['memory'] = memory
            deployment['spec']['template']['spec']['containers'][0]['resources']['requests']['memory'] = memory
        resp = api_instance.create_namespaced_deployment(body=deployment, namespace="default")

        logging.info("Deployment %s is successfully created. " % str(deployment['metadata']['name']))
        return True
    except ApiException as e:
        logging.warning("Deployment creation of %s did not completed %s"  % (str(deployment['metadata']['name']), str(e)))
        return False


def patch_deployment(api_instance, deployment_name, deployment):
    try:
        resp = api_instance.patch_namespaced_deployment(name=deployment_name, body=deployment, namespace="default")

        logging.info("Deployment %s is successfully updated. " % str(deployment['metadata']['name']))
        return True
    except ApiException as e:
        logging.warning("Deployment update of %s did not completed %s"  % (str(deployment['metadata']['name']), str(e)))
        return False


def delete_deployment(api_instance, deployment_name):
    """
    :param api_instance:
    :param deployment_name:
    :return:
    """
    try:
        resp = api_instance.delete_namespaced_deployment(name=deployment_name, namespace="default")

        logging.info("Deployment %s is successfully deleted. " % str(deployment_name))
        return True
    except ApiException as e:
        logging.warning("Deployment deletion of %s did not completed %s"  % (deployment_name, str(e)))
        return False


def create_service(api_instance, service):
    """
    :param api_instance:
    :param service:
    :return:
    """
    try:
        resp = api_instance.create_namespaced_service(body=service, namespace="default")
        logging.info("Service %s is successfully created. " % str(service['metadata']['name']))
        return True
    except ApiException as e:
        logging.warning("Service creation of %s did not completed %s"  % (str(service['metadata']['name']), str(e)))
        return False


def delete_service(api_instance, service_name):
    """
    :param api_instance:
    :param service_name:
    :return:
    """
    try:
        resp = api_instance.delete_namespaced_service(name=service_name, namespace="default")
        logging.info("Service %s is successfully deleted. " % str(service_name))
        return True
    except ApiException as e:
        logging.warning("Service deletion of %s did not completed %s"  % (str(service_name), str(e)))
        return False


def create_circuit_breaker(api_instance, service_name, max_requests):
    """
    :param api_instance:
    :param service_name:
    :param max_requests:
    :return:
    """
    try:
        cb = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "DestinationRule",
            "metadata": {"name": service_name+"-cb"},
            "spec": {
                "host": service_name,
                "trafficPolicy":{
                    "connectionPool":{
                        "http": {"http2MaxRequests": max_requests,
                                 #"maxRetries":20
                                 }
                    }
                }
            }
        }
        api_instance.create_namespaced_custom_object(
            namespace="default",
            body=cb,
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules"
        )
        logging.info("Circuit breaker for service %s with value of %s is successfully created. " % (str(service_name), str(max_requests)))
        return True
    except ApiException as e:
        logging.warning("Circuit breaker creation for service %s is not completed. %s" % (str(service_name), str(e)))
        return False


def delete_circuit_breaker(api_instance, service_name):
    """
    :param api_instance:
    :param service_name:
    :return:
    """
    try:
        api_instance.delete_namespaced_custom_object(
            namespace="default",
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules",
            name=service_name+"-cb"
        )
        logging.info("Circuit breaker for service %s is successfully deleted. " % str(service_name))
        return True
    except ApiException as e:
        logging.warning(
            "Circuit breaker deletion for service %s is not completed. %s" % (str(service_name), str(e)))
        return False


def create_retry(api_instance, service_name, attempts, timeout):
    """
    :param api_instance:
    :param service_name:
    :param attempts:
    :param timeout:
    :return:
    """
    try:
        retry = {
          "apiVersion": "networking.istio.io/v1alpha3",
          "kind": "VirtualService",
          "metadata": {
            "name": service_name +"-retry"
          },
          "spec": {
            "hosts": [
              service_name+".default.svc.cluster.local"
            ],
            "http": [
              {
                "route": [
                  {
                    "destination": {
                      "host": service_name+".default.svc.cluster.local",
                    },
                      # "headers": {
                      #     "response": {
                      #         "set": {
                      #             "x-envoy-retry-grpc-on": "unavailable,resource-exhausted,internal,deadline-exceeded,cancelled",
                      #             #"x-envoy-max-retries" : "100"
                      #         }
                      #     }
                      # }


                  }
                ],
                # "timeout":"5s",
                "retries": {
                  "attempts": attempts,
                  "perTryTimeout": timeout,
                   # "retryOn": "retriable-status-codes, retriable-headers, cancelled,deadline-exceeded,internal, "
                   #            "resource-exhausted, unavailable "
                  #"retryOn": "5xx,reset,gateway-error,connect-failure,retriable-4xx,refused-stream, cancelled,"
                  #           ""
                  #"retryOn": "retriable-status-codes, 503"
                   # "retryOn": "unavailable,resource-exhausted,internal,cancelled,deadline-exceeded,retriable-status-codes"
                    "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                },
              }
            ]
          }
        }

        api_instance.create_namespaced_custom_object(
            namespace="default",
            body=retry,
            group="networking.istio.io",
            version="v1alpha3",
            plural="virtualservices"
        )
        logging.info("Retry mechanism for service %s with value of %s is successfully created. " % (str(service_name), str(attempts)))
        return True
    except ApiException as e:
        logging.warning("Retry mechanism creation for service %s is not completed. %s" % (str(service_name), str(e)))
        return False


def delete_retry(api_instance, service_name):
    """
    :param api_instance:
    :param service_name:
    :return:
    """
    try:
        api_instance.delete_namespaced_custom_object(
            namespace="default",
            group="networking.istio.io",
            version="v1alpha3",
            plural="virtualservices",
            name=service_name+"-retry"
        )
        logging.info("Retry mechanism for service %s is successfully deleted. " % str(service_name))
        return True
    except ApiException as e:
        logging.warning(
            "Retry mechanims deletion for service %s is not completed. %s" % (str(service_name), str(e)))
        return False


def patch_retry(api_instance, service_name, attempts, timeout):
    """
    :param api_instance:
    :param service_name:
    :param attempts:
    :param timeout:
    :return:
    """
    try:
        retry = {
          "apiVersion": "networking.istio.io/v1alpha3",
          "kind": "VirtualService",
          "metadata": {
            "name": service_name +"-retry"
          },
          "spec": {
            "hosts": [
              service_name+".default.svc.cluster.local"
            ],
            "http": [
              {
                "route": [
                  {
                    "destination": {
                      "host": service_name+".default.svc.cluster.local",
                    }
                  }
                ],
                "retries": {
                  "attempts": attempts,
                  "perTryTimeout": timeout
                }
              }
            ]
          }
        }

        api_instance.patch_namespaced_custom_object(
            name=service_name +"-retry",
            namespace="default",
            body=retry,
            group="networking.istio.io",
            version="v1alpha3",
            plural="virtualservices"
        )
        logging.info("Retry mechanism for service %s with value of %s is successfully updated. " % (str(service_name), str(attempts)))
        return True
    except ApiException as e:
        logging.warning("Retry mechanism update for service %s is not completed. %s" % (str(service_name), str(e)))
        return False


def patch_circuit_breaker(api_instance, service_name, max_requests):
    """
    :param api_instance:
    :param service_name:
    :param max_requests:
    :return:
    """
    try:
        cb = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "DestinationRule",
            "metadata": {"name": service_name+"-cb"},
            "spec": {
                "host": service_name,
                "trafficPolicy":{
                    "connectionPool":{
                        "http": {"http2MaxRequests": max_requests}
                    }
                }
            }
        }
        api_instance.patch_namespaced_custom_object(
            name=service_name+"-cb",
            namespace="default",
            body=cb,
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules"
        )
        logging.info("Circuit breaker for service %s with value of %s is successfully updated. " % (str(service_name), str(max_requests)))
        return True
    except ApiException as e:
        logging.warning("Circuit breaker update for service %s is not completed. %s" % (str(service_name), str(e)))
        return False