import pandas as pd
import matplotlib.pyplot as plt
import utils

cb_values = [1]
static_traffic_ratio = [1.2]
configuration_layer = [1, 2, 3, 'all']
capacity_online_boutique = 230

challenging_services = ["frontend", "recommendationservice", "productcatalogservice"]

df = pd.read_csv('../logs/cb-experiment.log')



heights = [1, 3, 1, 3, 1, 3, 1, 3]
fig, axs = plt.subplots(nrows=8, ncols=3, sharex=True, figsize=(8, 8), gridspec_kw={'height_ratios': heights})

i = 0
j = 0
for layer in configuration_layer:
    for service in challenging_services:
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
                      (df['configured_layers'] == str(layer)) & (df['attempt'] == 1)]

        data_col = utils.get_status_codes_from_prometheus(service, data['start'], data['end'])
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
                        failed['data'][failed['timestamp'].index(cur_val)] = failed['data'][failed['timestamp'].index(cur_val)] + float(val[1])
                    else:
                        failed["data"].append(float(val[1]))
                        failed["timestamp"].append(float(val[0]) - float(item['values'][0][0]))
        success['timestamp'] = [ii for ii in success['timestamp'] if ii <= 240]
        success['data'] = success['data'][:len(success['timestamp'])]
        circuit_broken['timestamp'] = [ii for ii in circuit_broken['timestamp'] if ii <= 240]
        circuit_broken['data'] = circuit_broken['data'][:len(circuit_broken['timestamp'])]
        failed['timestamp'] = [ii for ii in failed['timestamp'] if ii <= 240]
        failed['data'] = failed['data'][:len(failed['timestamp'])]

        axs[i, j].set_xlim([0, 240])
        axs[2*i, j].plot(success['timestamp'], success['data'], color="green", label="Successful")
        axs[2*i, j].plot(circuit_broken['timestamp'], circuit_broken['data'], color="orange", label="Circuit Broken")
        axs[2*i, j].plot(failed['timestamp'], failed['data'], color="red", label="Failed")

        axs[2*i+1, j].plot(success['timestamp'], success['data'], color="green", label="Successful")
        axs[2*i+1, j].plot(circuit_broken['timestamp'], circuit_broken['data'], color="orange", label="Circuit Broken")
        axs[2*i+1, j].plot(failed['timestamp'], failed['data'], color="red", label="Failed")

        axs[2 * i, j].set_ylim(1200, 1700)
        axs[2 * i, j].set_yticks([1400])# outliers only
        axs[2 * i + 1, j].set_ylim(0, 300)  # most of the data
        axs[2 * i, j].spines.bottom.set_visible(False)
        axs[2 * i + 1, j].spines.top.set_visible(False)
        axs[2 * i, j].xaxis.tick_top()
        axs[2 * i, j].tick_params(labeltop=False)  # don't put tick labels at the top
        axs[2 * i + 1, j].xaxis.tick_bottom()
        d = .5  # proportion of vertical to horizontal extent of the slanted line
        kwargs = dict(marker=[(-1, -d), (1, d)], markersize=12,
                      linestyle="none", color='k', mec='k', mew=1, clip_on=False)
        axs[2 * i, j].plot([0, 1], [0, 0], transform=axs[2 * i, j].transAxes, **kwargs)
        axs[2 * i + 1, j].plot([0, 1], [1, 1], transform=axs[2 * i + 1, j].transAxes, **kwargs)

        if j in [1, 2]:
            axs[2 * i, j].get_yaxis().set_visible(False)
            axs[2 * i + 1, j].get_yaxis().set_visible(False)
        if layer == "all":
            axs[2 * i + 1, j].set_xlabel("Time (sec)")
            if service == "productcatalogservice":
                axs[2 * i + 1, j].legend(loc ="lower center")
        if i == 0:
            axs[2 * i+1, j].set_ylabel("CB configured\non 1st tier \n (req/sec)")
            axs[2 * i+1, j].yaxis.set_label_coords(-0.3, 0.8)
        elif i == 1:
            axs[2 * i+1, j].set_ylabel("CB configured\non 2nd tier \n (req/sec)")
            axs[2 * i+1, j].yaxis.set_label_coords(-0.3, 0.8)
        elif i== 2:
            axs[2 * i+1, j].set_ylabel("CB configured\non 3rd tier \n (req/sec)")
            axs[2 * i+1, j].yaxis.set_label_coords(-0.3, 0.8)
        else:
            axs[2 * i+1, j].set_ylabel("CB configured\non all tiers \n (req/sec)")
            axs[2 * i + 1, j].yaxis.set_label_coords(-0.3, 0.8)
        if i == 0:
            if j == 0:

                axs[2 * i, j].set_title("First tier")
            if j == 1:
                axs[2 * i, j].set_title("Second tier")
            if j == 2:
                axs[2 * i, j].set_title("Third tier")
plt.xticks([0, 60, 120, 180, 240])
plt.tight_layout()

#plt.show()
plt.savefig("./output/fig-4-a.pdf",format="pdf", bbox_inches='tight', pad_inches = 0)




