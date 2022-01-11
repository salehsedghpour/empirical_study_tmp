import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import utils
import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv('./logs/retry-experiments.log')


fig, axs = plt.subplots(nrows=1, ncols=4, figsize=(10, 3),dpi=300)

configuration_layer = [1, 2, 3, 'all']
capacity_online_boutique = 230
static_traffic_ratio = [0.8, 1, 1.2]


challenging_services = ["frontend", "recommendationservice", "productcatalogservice"]

cb_values = [1, 20, 1024]

i = 0
j = 0
retry_attempts = [1, 2, 10]


for layer_cb in [1, 2, 3, 'all']:
    for layer_retry in [1, 2, 3, 'all']:
        if layer_retry == 1 and layer_cb == 1:
            i = 0
            j = 0
        elif layer_retry == 1 and layer_cb == 2:
            i = 0
            j = 1
        elif layer_retry == 1 and layer_cb == 3:
            i = 0
            j = 2
        elif layer_retry == 1 and layer_cb == 'all':
            i = 0
            j = 3
        elif layer_retry == 2 and layer_cb == 1:
            i = 1
            j = 0
        elif layer_retry == 2 and layer_cb == 2:
            i = 1
            j = 1
        elif layer_retry == 2 and layer_cb == 3:
            i = 1
            j = 2
        elif layer_retry == 2 and layer_cb == 'all':
            i = 1
            j = 3
        elif layer_retry == 3 and layer_cb == 1:
            i = 2
            j = 0
        elif layer_retry == 3 and layer_cb == 2:
            i = 2
            j = 1
        elif layer_retry == 3 and layer_cb == 3:
            i = 2
            j = 2
        elif layer_retry == 3 and layer_cb == 'all':
            i = 2
            j = 3
        elif layer_retry == 'all' and layer_cb == 1:
            i = 3
            j = 0
        elif layer_retry == 'all' and layer_cb == 2:
            i = 3
            j = 1
        elif layer_retry == 'all' and layer_cb == 3:
            i = 3
            j = 2
        elif layer_retry == 'all' and layer_cb == 'all':
            i = 3
            j = 3
        data = df.loc[(df['configured_layers'] == str([layer_cb, layer_retry])) ]

        prom_data = {}

        for percentile in [x / 100 for x in range(0, 100, 1)]:
            prom_data[str(percentile)] = []
            prom_data[str(percentile)] = utils.get_response_time_from_prometheus("frontend", int(data.iloc[0]['start']),
                                                                           int(data.iloc[0]['end']), percentile)
        response_time = {
            "data": [],
            "timestamp": [],
            "bins": []
        }
        for item in prom_data:
            response_time['timestamp'].append(float(item))
            ival_list = []
            for ival in prom_data[str(item)][0]['values']:
                ival_list.append(float(ival[1]))
            response_time['data'].append(sum(ival_list) / len(ival_list))

        if layer_retry == 1:
            out = "1st tier"
        elif layer_retry == 2:
            out = "2nd tier"
        elif layer_retry == 3:
            out = "3rd tier"
        elif layer_retry == 'all':
            out = "all tiers"
        if layer_cb == 1:
            cb_out = "1st tier"
        elif layer_cb == 2:
            cb_out = "2nd tier"
        elif layer_cb == 3:
            cb_out = "3rd tier"
        elif layer_cb == 'all':
            cb_out = "all tiers"
        axs[j].set_title("CB configured on\n"+cb_out)
        axs[j].plot(response_time['data'],response_time['timestamp'], label=out, alpha=0.5)
        axs[j].set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], minor=False)
        axs[j].set_yticks([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], minor=True)

        if j == 3:
            axs[j].legend(loc="lower right", title="Retry mechanism\nconfigured on:")

        axs[j].xaxis.grid(True, which='minor')
        axs[j].xaxis.grid(True, which='major')
        axs[j].yaxis.grid(True, which='major')
        axs[j].yaxis.grid(True, which='minor')
        axs[j].set_ylabel("Probability")
        axs[j].set_xlabel("Response Time (sec)")

plt.tight_layout()
# plt.show()
plt.savefig("./charts/output/figure-12-b.pdf",format='pdf', bbox_inches='tight', pad_inches = 0.1)



