import pandas as pd
import time
import yaml
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cdist


# Create result directory
Path('./FOS_result').mkdir(parents=True, exist_ok=True)

# 0. load mine_input
with open('./mine_input.yaml') as f:
    mine_input = yaml.load(f, Loader=yaml.FullLoader)

if (mine_input['fovOptMode'] == 0):
    fovOptMode = 0 
    print('FOV Mode : Single')
else:
    fovOptMode = 1
    print('FOV Mode : Multi')




# 1. SONR
#  |-- 1.A. Load input data
samplingCsv = mine_input['samplingCsv']
print('Loading samplingCsv...')
SONR_csv_df = pd.read_csv(samplingCsv)

#  |-- 1.B. N_sonr_data, N_sonr_cluster, 
N_sonr_data = SONR_csv_df.shape[0]
print(f'# of SONR CSV data: {N_sonr_data:,}')

#  |-- 1.C. N_sonr_singlet_cluster
 ## Generate cluster_id column
key_list = [col for col in SONR_csv_df.columns if col.startswith('key')]
print(f'key_list: {key_list}')
#print('Cluster ID generating...')
SONR_csv_df['cluster_id'] = SONR_csv_df[key_list].astype(str).agg(''.join, axis=1).radd('a')

 ## Identify unique cluster_ids and single element clusters
#print('Calculating cluster_id counts...')
unique_cluster_id_counts = SONR_csv_df['cluster_id'].value_counts()
SONR_N_of_cluster = len(unique_cluster_id_counts)
SONR_N_of_singlet_df = unique_cluster_id_counts[unique_cluster_id_counts == 1]
SONR_N_of_singlet = len(SONR_N_of_singlet_df)
SONR_singlet_ratio = round(SONR_N_of_singlet / SONR_N_of_cluster * 100, 1)

#print(f'# of Cluster from SONR: {SONR_N_of_cluster:,} e.a.')
#print(f'# of Single Element Cluster from SONR: {SONR_N_of_singlet} ({SONR_singlet_ratio:.1f}%) e.a.')

# Add population column based on cluster_id counts
#print('Adding population column...')
SONR_csv_df['cluster_population'] = SONR_csv_df['cluster_id'].map(unique_cluster_id_counts)



# 2. FOS 
#  |-- 2.A. Load fos output gauge
 ## Load FOS gauge data and merge cluster, cluster_2
print('Loading FOS_gauge data...')
fos_gauge_df = pd.read_csv('./output_gauges.txt', sep='\t')
original_gauge_col_list = fos_gauge_df.columns.tolist()
excludes = ['cluster', 'cluster_2']
gauge_col_list = [item for item in original_gauge_col_list if item not in excludes]

if (fovOptMode == 1): #multi
    # coincidency: 1 for cluster==cluster_2 for same FOV_id. 0 for otherwise
    fos_gauge_df['coincidency'] = fos_gauge_df.apply(lambda row: 1 if row['cluster'] == row['cluster_2'] else 0, axis=1)
    cluster_1 = fos_gauge_df[['cluster']].copy()
    cluster_2 = fos_gauge_df[['cluster_2']].copy()
    cluster_2.columns = ['cluster']

    df_remaining_cols = fos_gauge_df.drop(columns=['cluster', 'cluster_2']).copy()
    df_remaining_cols_repeated = pd.concat([df_remaining_cols, df_remaining_cols], ignore_index=True)

    df_combined_cluster = pd.concat([cluster_1, cluster_2], ignore_index=True)
    fos_gauge_df = pd.concat([df_combined_cluster, df_remaining_cols_repeated], axis=1)
    col_list = gauge_col_list + ['cluster']
    fos_gauge_df = fos_gauge_df[col_list]
    N_of_gauge = len(fos_gauge_df) / 2
    #fos_gauge_df = df_final
else: #single
    N_of_gauge = len(fos_gauge_df)
    pass

# check cluster_id from gauge and make 'to_gauge'
#print('Updating to_gauge column...')
SONR_csv_df['to_gauge'] = SONR_csv_df['cluster_id'].isin(fos_gauge_df['cluster']).astype(int)


#  |-- 2.B. N_fos_gauge, N_fos_cluster
FOS_N_of_cluster = len(fos_gauge_df['cluster'].unique())
N_of_cluster_SONR2FOS = len(SONR_csv_df[SONR_csv_df['to_gauge'] == 1]['cluster_id'].unique())
if (FOS_N_of_cluster != N_of_cluster_SONR2FOS):
    print('===========================================================')
    print('WARNING')
    print('===========================================================')
    print('FOS_N_of_cluster is NOT EQUAL to the N_of_cluster_SONR2FOS')
    print(f'FOS_N_of_cluster: {FOS_N_of_cluster}')
    print(f'N_of_cluster_SONR2FOS: {N_of_cluster_SONR2FOS}')
    print('===========================================================')

else:
    transfered_cluster_percentage_SONR2FOS = round((N_of_cluster_SONR2FOS / SONR_N_of_cluster) * 100, 1)

    # Calculate the number and percentage of cluster_ids reflected in fos_gauge_df
    fos_cluster_df = fos_gauge_df['cluster'].value_counts()
    fos_gauge_df['cluster_population'] = fos_gauge_df['cluster'].map(fos_cluster_df)

#  |-- 2.C. FOS_N_of_singlet_cluster
    FOS_singlet = fos_gauge_df[fos_gauge_df['cluster_population'] == 1]
    FOS_N_of_singlet = len(FOS_singlet)
    lost_singlet_df = SONR_csv_df[(SONR_csv_df['cluster_population'] == 1) & (SONR_csv_df['to_gauge'] == 0)]
    N_of_lost_singlet = len(lost_singlet_df)

#  |-- 2.D. singlet_transferability: N_fos_singlet_cluster/N_sonr_singlet_cluster * 100
    if (N_of_lost_singlet != 0):
        print('===========================================================')
        print('===========================================================')
        print(f'N of lost singlet cluster: {N_of_lost_singlet}')
        print('Take review ./FOS_result/lost_single.csv')
        print('===========================================================')
        print('===========================================================')
        col_backup = lost_singlet_df.columns.tolist()
        lost_singlet_df.loc[:, 'gauge'] = lost_singlet_df['cluster_id']
        lost_singlet_df['g_type'] = 'ep'
        lost_singlet_df.loc[:, 'startx'] = lost_singlet_df['X']
        lost_singlet_df.loc[:, 'starty'] = lost_singlet_df['Y']
        lost_singlet_df.loc[:, 'endx'] = lost_singlet_df['X']
        lost_singlet_df.loc[:, 'endy'] = lost_singlet_df['Y']
        new_col = ['gauge', 'g_type', 'startx', 'starty', 'endx', 'endy'] + col_backup
        lost_singlet_df[new_col]

        lost_singlet_df.to_csv('./FOS_result/lost_singlet.csv', sep=' ', index=False)
        singlet_tansfer_percentage = round(N_of_lost_singlet / SONR_N_of_singlet * 100, 2)
    else:
        print('All singlet clusters are transfered from SONR to FOS output_gauge')
        singlet_tansfer_percentage = 100



'''
# Appendix I. gauge sorting with DBSCAN mag and fosSpace
radius = 1000 #1um, in later this must coincide with the 
dbscan = DBSCAN(eps=radius, min_samples=1).fit(fos_gauge_df[['startx', 'starty']])
fos_gauge_df['cluster_DBSCAN'] = dbscan.labels_

## Def. sorting funciton
def sort_within_cluster(cluster_df):
    if len(cluster_df) == 1:
        return cluster_df
    start_point = cluster_df.iloc[0]
    sorted_cluster = [start_point]
    remaining_df = cluster_df.drop(index=start_point.name)
    while not remaining_df.empty:
        distances = cdist([sorted_cluster[-1][['startx', 'starty']]], remaining_df[['startx', 'starty']]).flatten()
        closest_index = distances.argmin()
        closest_row = remaining_df.iloc[closest_index]
        sorted_cluster.append(closest_row)
        remaining_df = remaining_df.drop(index=closest_row.name)
    return pd.DataFrame(sorted_cluster)


 

# Sorting gauge inside of R
sorted_clusters = [] 
for cluster_id in fos_gauge_df['cluster_DBSCAN'].unique():
    cluster_df = fos_gauge_df[fos_gauge_df['cluster_DBSCAN'] == cluster_id]
    sorted_cluster_df = sort_within_cluster(cluster_df)
    sorted_clusters.append(sorted_cluster_df)

    
sorted_fos_gauge_df = pd.concat(sorted_clusters).reset_index(drop=True)
if (fovOptMode == 0): #single model
    n_of_FOV = len(fos_gauge_df)
else:
    n_of_FOV = len(sorted_fos_gauge_df['FOV_id'].unique())

print(f'n_of_FOV: {n_of_FOV}')
sorted_fos_gauge_df.to_csv('./output_gauge_sorted.txt', sep=' ', index=False)
'''






# Plot and save histogram of cluster_id
print('Plotting histogram...')
plt.figure(figsize=(10, 6))
unique_cluster_id_counts.hist(bins=50)
plt.title('Histogram of Cluster ID Counts')
plt.xlabel('Number of Entries per Cluster ID')
plt.ylabel('Frequency')
plt.grid(True)
plt.savefig('./FOS_result/cluster_id_histogram.png')
plt.close()
print('Histogram saved.')



# Save the key variables and values to YAML
summary = {
    'SONR_data': {
        'N_SONR_data':N_sonr_data,
        #'key_list': key_list,
        'SONR_N_of_cluster': SONR_N_of_cluster,
        'SONR_N_of_singlet': SONR_N_of_singlet,
        'SONR_singlet_percentage': SONR_singlet_ratio
        },
    'FOS_Data': {
        'N_of_gauge': N_of_gauge,
        'FOS_N_of_cluster': FOS_N_of_cluster,
        'cluster_transfer_percentage': transfered_cluster_percentage_SONR2FOS ,
        'Singlet cluster': {
            'FOS_N_of_singlet': FOS_N_of_singlet,
            'N_of_lost_singlet': N_of_lost_singlet,
            'Singlet_transfer_percentage from SONR': singlet_tansfer_percentage 
        }
    #'Elapsed_time': elapsed_time
    }
}

# End timer and print elapsed time
#end_time = time.time()
#elapsed_time = end_time - start_time
#print(f'Elapsed time: {elapsed_time} seconds')


with open('./FOS_result/summary.yaml', 'w') as outfile:
    yaml.dump(summary, outfile, default_flow_style=False, sort_keys=False)




# Save the updated SONR_csv_df to CSV
#print('DataFrame dumping ...')
#SONR_csv_df.to_csv('./FOS_result/SONR_csv_with_gauge.csv', sep=' ', index=False)
#fos_gauge_df.to_csv('./FOS_result/fos_gauge.csv', sep=' ', index=False)

