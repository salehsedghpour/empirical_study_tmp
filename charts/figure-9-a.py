import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import utils
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd


retry_attempts = [1, 2, 10]
static_traffic_ratio = [0.8, 1, 1.2]
configuration_layer = [1, 2, 3, 'all']
cb_values = [1, 20, 1024]
capacity_online_boutique = 230
challenging_services = ["frontend", "recommendationservice", "productcatalogservice"]
retry_timeouts= ["25ms", "5s", "20s"]

df = pd.read_csv('./logs/retry-experiments.log')

fig, axs = plt.subplots(nrows=3, ncols=3, figsize=(8, 8), sharex=True, sharey=True,dpi=300)
i = 0
j = 0

for retry_to in retry_timeouts:
    for service in challenging_services:
        if retry_to == "25ms" and service == "frontend":
            i = 0
            j = 0
        elif retry_to == "25ms" and service == "recommendationservice":
            i = 0
            j = 1
        elif retry_to == "25ms" and service == "productcatalogservice":
            i = 0
            j = 2
        elif retry_to == "5s" and service == "frontend":
            i = 1
            j = 0
        elif retry_to == "5s" and service == "recommendationservice":
            i = 1
            j = 1
        elif retry_to == "5s" and service == "productcatalogservice":
            i = 1
            j = 2
        elif retry_to == "20s" and service == "frontend":
            i = 2
            j = 0
        elif retry_to == "20s" and service == "recommendationservice":
            i = 2
            j = 1
        elif retry_to == "20s" and service == "productcatalogservice":
            i = 2
            j = 2

        data = df.loc[(df['retry_timeout'] == retry_to)]
        data_status_col = utils.get_status_codes_from_prometheus(service, int(data['start'].values[0]), int(data['end'].values[0]))


        success = {
            "data": [],
            "timestamp": [],
        }
        failed = {
            "data": [],
            "timestamp": []
        }
        circuit_broken = {
            "data": [],
            "timestamp": [],
        }
        for item in data_status_col:
            if item['metric']['response_code'] == "200" and item['metric']['response_flags'] == "-":
                for val in item['values']:
                    success["data"].append(float(val[1]))
                    success["timestamp"].append(float(val[0]) - item['values'][0][0])
            elif item['metric']['response_flags'] == "UO":
                for val in item['values']:
                    circuit_broken["data"].append(float(val[1]))
                    circuit_broken["timestamp"].append(float(val[0]) - item['values'][0][0])
            elif item['metric']['response_flags'] != "UO":
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
        axs[i, j].grid()
        axs[i, j].plot(success['timestamp'], success['data'], color="green", label="Successful")
        axs[i, j].plot(circuit_broken['timestamp'], circuit_broken['data'], color="orange", label="Circuit Broken")
        axs[i, j].plot(failed['timestamp'], failed['data'], color="red", label="Failed")
        axs[i, j].set_xticks([0, 60, 120, 180, 240])
        axs[i, j].set_xlim(0, 240)
        axs[i, j].set_yscale("log")
        axs[i, j].set_yticks([10, 100, 1000])
        axs[i, j].yaxis.set_major_formatter(mpl.ticker.ScalarFormatter())
        if i == 2:
            axs[i, j].set_xlabel("Time (sec)")
        if i == 0:
            if j == 0:
                axs[i, j].set_title("First tier")
            elif j == 1:
                axs[i, j].set_title("Second tier")
            elif j == 2:
                axs[i, j].set_title("Third tier")

        if j == 0:
            if retry_to == "20s":
                to = "10s"
            else:
                to = retry_to
            axs[i, j].set_ylabel(str(to) + " as retry timeouts\n(req/sec)")
        if j==2:
            if i == 2:
                axs[i, j].legend()

plt.xticks([0, 60,120,180,240])

plt.tight_layout()
# plt.show()
plt.savefig("./charts/output/figure-9-a.pdf", format='pdf', bbox_inches='tight', pad_inches = 0)