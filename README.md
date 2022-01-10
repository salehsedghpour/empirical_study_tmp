# Reproduce traffic management policies experiments
[![DOI](https://zenodo.org/badge/438598541.svg)](https://zenodo.org/badge/latestdoi/438598541)

This repository contains scripts that help run the traffic management policies experiments from our ICPE '22 paper.

## Overview
1. Set up the requirements (Docker, Kubernetes, Istio and etc.) see section [prepare the required setup](#prepare-the-required-setup)
2. Deploy services ([section](#deploy-services))
3. Perform the experiment sizing ([section](#perform-the-experiment-sizing))
4. Pick an experiment to run, and edit the initial setups. ([section](#run-the-experiments))
5. Draw the charts. ([section](#draw-the-charts))
6. Clean up. ([section](#clean-up))



## Local dependencies

These are local dependencies to run the experiment script and parse the outputs into a report with a graph.
- [Python 3.8.0](https://www.python.org/)
  - See [requirements.txt](requirements.txt)
- [Docker 19.03.15](https://www.docker.com/)
- [Kubernetes 1.19.14](https://kubernetes.io/)
- [Istio 1.11.2](https://istio.io/)


## Prepare the required setup

All of our experiments require at least 5 machines with at least 4 cores of CPU. See the [required versions](#local-dependencies) in each step.

1. The first step is to set up at least 5 different machines (Any distribution of linux could work, we used Ubuntu 20.04).
2. Now we need to install a container engine (We used docker) on all of our machines, You can simply follow the instruction 
in the [docker official documentation](https://docs.docker.com/engine/install/)
3. As we might need to run docker with non-root users, we should follow the [post-installation steps for linux](https://docs.docker.com/engine/install/linux-postinstall/). 
4. After installing docker, we need to install Kubernetes, we used the [official documentation for 
   installation](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/) of production 
   environment using `kubeadm`.
5. Then we need to [create the cluster with `kubeadm`](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/) using the official documentation.
We used `kubeadm init --apiserver-advertise-address <address-of-master-node> --pod-network-cidr  10.244.0.0/16`
6. Then we need to install Kubernetes networking model, we used [Calico](https://projectcalico.docs.tigera.io/getting-started/kubernetes/self-managed-onprem/onpremises). Or simply just follow: 
`curl https://docs.projectcalico.org/manifests/calico.yaml -O
` and then`kubectl apply -f calico.yaml
`
7. Then we should be able to confirm that all nodes are up and ready (state), by just executing `kubectl get nodes`.
8. Now it is time to install Istio  with `default` profile  from the [official documentation](https://istio.io/latest/docs/setup/getting-started/).
9. During the whole experiments, we need `prometheus` as a monitoring tool.  As Istio has prometheus deployment in it's addons, 
   we just need to configure it for our use cases. We'd suggest following the instructions in [Confgiuring Prometheus](#install-and-configure-prometheus) section.
   

## Install and configure Prometheus
By default, Istio provide Prometheus as an add-on which could be found in `<istio-1.11.2>/samples/addons/prometheus.yaml`.
As we are going to save the data in case of pod failure, we should mount the pod storage to the node storage as follows:
1. We first should specify on which node we are going to run Prometheus and save it's data, then create the following directories:
    ```
    ssh <name-of-specified-node-in-cluster>
    sudo mkdir -p /mnt/data/prometheus
    # to ensure the permission requirements,
    chmod 755 /mnt
    chmod 755 /mnt/data
    chmod 755 /mnt/data/prometheus
    ```
2. Then we should create persistent volume and persistent volume claim for kubernetes using the volumes inside [`yaml-files/volumes`](yaml-files/volumes) directory.
    ```
        kubectl apply -f yaml-files/volumes/
    ```
    
Before installing it, we should configure it in on of the following ways:
- You can simply use our pre-configured Prometheus in [`yaml-files/prometheus`](yaml-files/prometheus/pre-configured-prometheus.yaml):
    ```
        # Copy the yaml file into the `<istio-1.11.2>/samples/addons/' directory:
        cp yaml-files/prometheus/pre-configured-prometheus.yaml <istio-1.11.2>/samples/addons/
  
        kubectl apply -f <istio-1.11.2>/samples/addons/pre-configured-prometheus.yaml
    ```
If you want to configure it yourself, just follow:
- As we are going to monitor the service mesh every 5 seconds, we should change the scrape interval to 5 seconds:
    - In line 37 and 38 of yaml file change the values of `scrape_interval` and `scrape_timeout` to 5 seconds as follows:
      ```
        scrape_interval: 5s
        scrape_timeout: 5s
      ```
    - As we are going to save the data in case of pod failure:
        - So one simple idea is to assign the prometheus pods to a node by adding the nodeName in line 420:
            ```
                spec:
                    nodeName: <name-of-specified-node-in-cluster>
                    serviceAccountName: prometheus
            ```
        - We should also configure a mount volume for it in line 470 and 485: 
            ```
              volumeMounts:
                - name: config-volume
                  mountPath: /etc/config
                - name: prometheus-volume
                  mountPath: /data
                  subPath: ""
            ```
        
          and 
        
            ```
              volumes:
                - name: config-volume
                  configMap:
                    name: prometheus
                - name: prometheus-volume
                  persistentVolumeClaim:
                     claimName: prom-pvc
    
            ```
        - If you intend to keep the data for more than 15 days, you may also need to increase the retention time in line 440:
            ```
              # it will keep the data for 6 month
              args:
                - --storage.tsdb.retention.time=180d
                - --config.file=/etc/config/prometheus.yml
                - --storage.tsdb.path=/data
                - --web.console.libraries=/etc/prometheus/console_libraries
                - --web.console.templates=/etc/prometheus/consoles
            ```
## Deploy Services
To run all scripts in the repository, you need to install all required packages:
```
pip3 install -r requirements.txt
```
Before we get started, we should deploy all services by simply running the following:
```
python deploy_all_services.py
```


## Perform the experiment sizing

Before jumping to main experiments, we should just estimate the capacity of our infrastructure based for the services.
First of all we need to deploy all services by simply following the instruction in [previous section](#deploy-services).
To run the experiment sizing:
```
cd experiments
python experiments/0-experiment-sizing.py
```
When the execution is done, it prints the capacity, keep it for further experiments.


## Run the experiments
In this paper, we have two series of experiments; one for [different circuit breaking patterns](#run-the-circuit-breaking-experiments)
and the other one for [different retry mechanisms](#run-the-retry-mechanism-experiments). 

**NOTE** For drawing the charts in the paper, you need to run the experiments first.

### Run the circuit breaking experiments
To run the exact circuit breaking experiments as paper, you need to first update capacity parameter in configuration the 
[experiment file](experiments/1-circuit-breaking-experiments.py) and then:
```
cd experiments
python 1-circuit-breaking-experiments.py
```
If you wish to perform experiments for different traffic scenarios, different circuit breaking, different durations,
different repetition of each experiment and etc., just update the configuration part of the [experiment file](experiments/1-circuit-breaking-experiments.py).

### Run the retry mechanism experiments
To run the exact retry mechanism experiments as paper, you need to first update capacity parameter in configuration the 
[experiment file](experiments/2-retry-mechanism-experiments.py) and then:
```
cd experiments
python 2-retry-mechanism-experiments.py
```
If you wish to perform experiments for different traffic scenarios, different circuit breaking, different durations,
different retry mechanism, different repetition of each experiment and etc., just update the configuration part of the 
[experiment file](experiments/2-retry-mechanism-experiments.py).


## Draw the charts
To draw the charts, you need to first run the experiments as discussed in [previous section](#run-the-experiments).
Before jumpling to drawin, you should edit address of **Prometheus** in the [`config.py`](config.py) file. 
Run the following to get IP of **Prometheus** instance:
```
~ kubectl get svc -n istio-system
NAME                   TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                                      AGE
istio-ingressgateway   LoadBalancer   10.102.191.32    <pending>     15021:32605/TCP,80:30690/TCP,443:31947/TCP   93d
istiod                 ClusterIP      10.111.219.110   <none>        15010/TCP,15012/TCP,443/TCP,15014/TCP        93d
jaeger-collector       ClusterIP      10.100.29.41     <none>        14268/TCP,14250/TCP,9411/TCP                 82d
prometheus             ClusterIP      10.104.156.162   <none>        9090/TCP                                     93d
tracing                ClusterIP      10.103.63.142    <none>        80/TCP,16685/TCP                             82d
zipkin                 ClusterIP      10.107.209.224   <none>        9411/TCP                                     82d
```
In the above example, you can see that the instance has the `10.104.156.162` address and is working on port `9090`.
We have splitted the drawing section to the figures in the paper, it means that each charts in the paper has its own
implementation here in [charts directory](charts). For instance, if you intend to draw the Figure 4-a in the paper,
just run:
```
cd charts
python figure-4-a.py
```


## Clean up
After doing all experiments, if you intend to clean up your infrastructure, just run the clean up script.

```
python clean_up.py
```


          
          
        
