import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import pandas as pd
import matplotlib.pyplot as plt
import json

cb_values = [1]
static_traffic_ratio = [0.8, 1, 1.2]
configuration_layer = [1, 2, 3, 'all']
capacity_online_boutique = 230

challenging_services = ["frontend"]

df = pd.read_csv('./logs/cb-experiment.log')


i = 0

fig, axs = plt.subplots(nrows=1, ncols=3, sharex=True, figsize=(8,4))
for traffic in static_traffic_ratio:
    if traffic == 0.8:
        i = 0
    elif traffic == 1:
        i = 1
    elif traffic == 1.2:
        i = 2
    data = df.loc[(df['circuit_breaker'] == 20) & (df['traffic_ratio'] == traffic) &
                  (df['configured_layers'] == str(1)) & (df['attempt'] == 0)]
    data_col = json.loads(data.iloc[0]['status_frontend'].replace("'", '"'))
    success = {
        "data": [],
        "timestamp": []
    }
    failed = {
        "data": [],
        "timestamp": []
    }
    circuit_broken = {
        "data": [],
        "timestamp": []
    }
    for item in data_col:
        if item['metric']['response_code'] == "200" and item['metric']['response_flags'] == "-":
            for val in item['values']:
                success["data"].append(float(val[1]))
                success["timestamp"].append(float(val[0]) - item['values'][0][0])
        elif item['metric']['response_flags'] == "UO":
            for val in item['values']:
                circuit_broken["data"].append(float(val[1]))
                circuit_broken["timestamp"].append(float(val[0]) - item['values'][0][0])
        elif item['metric']['response_code'] != "200" and item['metric']['response_flags'] != "UO":
            for val in item['values']:
                cur_val = (float(val[0]) - float(item['values'][0][0]))
                if cur_val in failed["timestamp"]:
                    failed['data'][failed['timestamp'].index(cur_val)] = failed['data'][failed['timestamp'].index(
                        cur_val)] + float(val[1])
                else:
                    failed["data"].append(float(val[1]))
                    failed["timestamp"].append(float(val[0]) - float(item['values'][0][0]))
    success['timestamp'] = [ii for ii in success['timestamp'] if ii <= 240]
    success['data'] = success['data'][:len(success['timestamp'])]
    circuit_broken['timestamp'] = [ii for ii in circuit_broken['timestamp'] if ii <= 240]
    circuit_broken['data'] = circuit_broken['data'][:len(circuit_broken['timestamp'])]
    failed['timestamp'] = [ii for ii in failed['timestamp'] if ii <= 240]
    failed['data'] = failed['data'][:len(failed['timestamp'])]
    axs[i].plot(success['timestamp'], success['data'], color="green", label="Successful")
    axs[i].plot(circuit_broken['timestamp'], circuit_broken['data'], color="orange", label="Circuit Broken")
    axs[i].plot(failed['timestamp'], failed['data'], color="red", label="Failed")
    axs[i].set_ylim([0, 250])
    axs[i].set_xlim([0, 240])
    axs[i].set_xlabel("Time (sec)")

    if traffic == 0.8:
        axs[i].set_ylabel("Throughput\n(req/sec)")
        axs[i].set_title("Incoming traffic 0.8\ntimes of capacity")
    if traffic == 1:
        axs[i].set_title("Incoming traffic 1\ntimes of capacity")
    if traffic == 1.2:
        axs[i].set_title("Incoming traffic 1.2\ntimes of capacity")
        axs[i].legend()
plt.yticks([0, 50,100,150,200, 250])
plt.xticks([0, 60, 120, 180, 240])

plt.tight_layout()
#plt.show()
plt.savefig("./charts/output/figure-5-a.pdf",format='pdf', bbox_inches='tight', pad_inches = 0)
