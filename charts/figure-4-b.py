import utils
import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv('../logs/cb-experiment.log')


fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(7, 4),dpi=300)

configuration_layer = [1, 2, 3, 'all']
capacity_online_boutique = 230

challenging_services = ["frontend", "recommendationservice", "productcatalogservice"]


i = 0
j = 0
for layer in configuration_layer:
    for service in ['frontend']:
        if layer == 1 and service == "frontend":
            i = 0
            j = 0
        elif layer == 1 and service == "recommendationservice":
            i = 0
            j = 1
        elif layer == 1 and service == "productcatalogservice":
            i = 0
            j = 2
        elif layer == 2 and service == "frontend":
            i = 1
            j = 0
        elif layer == 2 and service == "recommendationservice":
            i = 1
            j = 1
        elif layer == 2 and service == "productcatalogservice":
            i = 1
            j = 2
        elif layer == 3 and service == "frontend":
            i = 2
            j = 0
        elif layer == 3 and service == "recommendationservice":
            i = 2
            j = 1
        elif layer == 3 and service == "productcatalogservice":
            i = 2
            j = 2
        elif layer == "all" and service == "frontend":
            i = 3
            j = 0
        elif layer == "all" and service == "recommendationservice":
            i = 3
            j = 1
        elif layer == "all" and service == "productcatalogservice":
            i = 3
            j = 2
        data = df.loc[(df['circuit_breaker'] == 20) & (df['traffic_ratio'] == 1.2) &
                      (df['configured_layers'] == str(layer)) & (df['attempt'] == 0)]

        prom_data = {}
        for percentile in [x / 100 for x in range(0, 100, 1)]:
            prom_data[str(percentile)] = []
            prom_data[str(percentile)] = utils.get_response_time_from_prometheus(service, int(data.iloc[0]['start']), int(data.iloc[0]['end']), percentile)
        response_time = {
            "data": [],
            "timestamp": [],
            "bins":[]
        }
        for item in prom_data:
            response_time['timestamp'].append(float(item))
            ival_list = []
            for ival in prom_data[str(item)][0]['values']:
                ival_list.append(float(ival[1]))
            response_time['data'].append(sum(ival_list)/len(ival_list))

        if layer == 1:
            out = "1st tier"
        elif layer == 2:
            out = "2nd tier"
        elif layer == 3:
            out = "3rd tier"
        if layer == "all":
            axs.plot(response_time['data'],response_time['timestamp'], label="All tiers", alpha=0.5)
        else:
            axs.plot(response_time['data'],response_time['timestamp'], label=out)
        axs.set_yticks([0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1], minor=False)
        axs.set_yticks([0.05,0.15,0.25,0.35,0.45,0.55,0.65,0.75,0.85,0.95], minor=True)

        axs.legend(loc="lower right", title="Circuit breaker\nenforced on:")
        axs.xaxis.grid(True, which='minor')
        axs.xaxis.grid(True, which='major')
        axs.yaxis.grid(True, which='major')
        axs.yaxis.grid(True, which='minor')
        axs.set_ylabel("Probability")
        axs.set_xlabel("Response Time (sec)")

plt.tight_layout()
plt.savefig("./output/figure-4-b.pdf",format='pdf', bbox_inches='tight', pad_inches = 0.1)



