import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml
import seaborn as sns
import dask.dataframe as dd
import time
from pathlib import Path

start_time = time.time()

Path('./FOS_result').mkdir(parents=True, exist_ok=True)

#1. FOS analysis

with open('./mine_input.yaml') as f: 
    mine_input = yaml.load(f, Loader=yaml.FullLoader) 

# 1.A. SONR_input analysis
samplingCsv = mine_input['samplingCsv']
print(f'')
print(f'Loading samplingCsv...')
SONR_csv_df = pd.read_csv(samplingCsv)
#ddf = dd.from_pandas(SONR_csv_df, npartitions=10)

print(f'# of SONR CSV data: {SONR_csv_df.shape[0]:,}')
key_list = [col for col in SONR_csv_df.columns if col.startswith('key')]
#key_list = [col for col in ddf.columns if col.startswith('key')]
print(f'key_list: {key_list}')

print(f'Keycomb generating ...')
SONR_csv_df['keycomb'] = SONR_csv_df[key_list].apply(lambda row: 'a' + ''.join(row.astype(str)), axis=1)
#ddf['keycomb'] = ddf[key_list].apply(lambda row: 'a' + ''.join(row.astype(str)), axis=1, meta=('x', 'str'))
print(f'Keycomb Done.')

#keycomb identifying
unique_keycomb_key = SONR_csv_df['keycomb'].value_counts().index
unique_keycomb_value = SONR_csv_df['keycomb'].value_counts().values

#single element 
single_element = unique_keycomb_value[unique_keycomb_value == 1]

print(f'# of Cluster: {len(unique_keycomb_key):,} e.a.')
print(f'# of Single Element Cluster: {len(single_element)} ({round(len(single_element)/len(unique_keycomb_key)*100,1)} %) e.a.')


end_time = time.time()
elapsed_time = end_time - start_time
print(f'Elapsed time: {elapsed_time} seconds')

SONR_csv_df.to_csv('./FOS_result/SONR_csv.csv', sep=' ', index=False)
