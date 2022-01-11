import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import pandas as pd
import matplotlib.pyplot as plt
import json

cb_values = [1, 20, 1024]
static_traffic_ratio = [1.2]
configuration_layer = [1, 2, 3, 'all']
capacity_online_boutique = 230

df_cb = pd.read_csv('./logs/cb-experiment.log')


fig, axs = plt.subplots(nrows=1, ncols=3, figsize=(8, 4),dpi=300)
i = 0


for cb in cb_values:
    if cb == 1:
        i = 0
    elif cb == 20:
        i = 1
    elif cb == 1024:
        i = 2
    data_cb = df_cb.loc[(df_cb['circuit_breaker'] == cb) & (df_cb['traffic_ratio'] == 1.2) &
                  (df_cb['configured_layers'] == str(1)) & (df_cb['attempt'] == 1)]
    data_cb_col = json.loads(data_cb.iloc[0]['status_frontend'].replace("'", '"'))
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
    response_time = []
    for item in data_cb_col:
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

    for item in success['data']:
        print(str(item)+",")

    success['timestamp'] = [ii for ii in success['timestamp'] if ii <= 240]
    success['data'] = success['data'][:len(success['timestamp'])]
    circuit_broken['timestamp'] = [ii for ii in circuit_broken['timestamp'] if ii <= 240]
    circuit_broken['data'] = circuit_broken['data'][:len(circuit_broken['timestamp'])]
    failed['timestamp'] = [ii for ii in failed['timestamp'] if ii <= 240]
    failed['data'] = failed['data'][:len(failed['timestamp'])]
    axs[i].plot(success['timestamp'], success['data'], color="green", label="Successful")
    axs[i].plot(circuit_broken['timestamp'], circuit_broken['data'], color="orange", label="Circuit Broken")
    axs[i].plot(failed['timestamp'], failed['data'], color="red", label="Failed")
    axs[i].set_title(str(cb) +" as CB value\n (req/sec)")
    axs[i].set_xticks([0, 60, 120, 180, 240])
    axs[i].set_yticks([0, 75,150,225,300])
    axs[i].set_xlabel("Time (sec)")
    axs[i].set_ylim(0)
    axs[i].set_xlim(0,240)

    if i == 0:
        axs[i].set_ylabel("Throughput\n (req/sec)")
    if i == 2:
        axs[i].legend(loc="lower right")


plt.tight_layout()
#plt.show()
plt.savefig("./charts/output/figure-6-a.pdf",format='pdf', bbox_inches='tight', pad_inches = 0)



