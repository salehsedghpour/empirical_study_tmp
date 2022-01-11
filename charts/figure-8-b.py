import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import utils
import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv('./logs/retry-experiments.log')

fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(7, 4),dpi=300)

configuration_layer = [1, 2, 3, 'all']
capacity_online_boutique = 230
static_traffic_ratio = [0.8, 1, 1.2]

challenging_services = ["frontend", "recommendationservice", "productcatalogservice"]

cb_values = [1, 20, 1024]

i = 0
j = 0
retry_attempts = [1, 2, 10]

for retry_at in retry_attempts:
    for service in challenging_services:
        if retry_at == 1 and service == "frontend":
            i = 0
            j = 0
        elif retry_at == 1 and service == "recommendationservice":
            i = 0
            j = 1
        elif retry_at == 1 and service == "productcatalogservice":
            i = 0
            j = 2
        elif retry_at == 2 and service == "frontend":
            i = 1
            j = 0
        elif retry_at == 2 and service == "recommendationservice":
            i = 1
            j = 1
        elif retry_at == 2 and service == "productcatalogservice":
            i = 1
            j = 2
        elif retry_at == 10 and service == "frontend":
            i = 2
            j = 0
        elif retry_at == 10 and service == "recommendationservice":
            i = 2
            j = 1
        elif retry_at == 10 and service == "productcatalogservice":
            i = 2
            j = 2
    data = df.loc[(df['retry_attempts'] == retry_at)]

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

    axs.plot(response_time['data'],response_time['timestamp'], label=str(retry_at), alpha=0.5)
    axs.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], minor=False)
    axs.set_yticks([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], minor=True)
    axs.legend(loc="lower right", title="Number of retry\nattempts:")

    axs.xaxis.grid(True, which='minor')
    axs.xaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='minor')
    axs.set_ylabel("Probability")
    axs.set_xlabel("Response Time (sec)")

plt.tight_layout()
# plt.show()
plt.savefig("../charts/output/figure-8-b.pdf",format='pdf', bbox_inches='tight', pad_inches = 0.1)



