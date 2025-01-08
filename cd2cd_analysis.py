
import sys, os
from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import copy
import pickle

pwd = Path(os.getcwd())

model_analysis_path = pwd / 'model_analysis'
model_analysis_path.mkdir(exist_ok=True)
cd2cd_path = model_analysis_path / 'cd2cd'
cd2cd_path.mkdir(exist_ok=True)

sys.path.append('/user/cbm/python_package/SALT')
from model.model_analysis import *
ma = model_analysis()

if(((model_analysis_path / 'cal_data.pkl').exists()) and ((model_analysis_path / 'result_data.pkl').exists())):
    with open(model_analysis_path / 'cal_data.pkl', 'rb') as f1:
        cal_data = pickle.load(f1)
    with open(model_analysis_path / 'result_data.pkl', 'rb') as f2:
        result_data = pickle.load(f2)
    del(f1)
    del(f2)
else:
    cal_data = ma.caldirs(pwd)
    result_data = ma.result_yaml_analysis(cal_data)
    with open(model_analysis_path / 'cal_data.pkl', 'wb') as f1:
        pickle.dump(cal_data, f1)
    with open(model_analysis_path / 'result_data.pkl', 'wb') as f2:
        pickle.dump(result_data, f2)
    del(f1)
    del(f2)


df_list = []
result_data["cost_ranking"]=result_data["Resist_linear_cost"].rank(axis=0, method='min', numeric_only=1).astype(int)
#cost_list = result_data["cost_ranking"].tolist()

result_list = list(range(cal_data['tasks']))

if(((cd2cd_path / 'cd2cd.txt').exists()) and ((cd2cd_path / 'mask.txt').exists())):
    print("-----------------------------") 
    print("cd2cd.txt & mask.txt are exist. Loading them.")
    print("-----------------------------") 
    cd2cd_df = pd.read_pickle(cd2cd_path / 'cd2cd.pkl')
    mask_df = pd.read_pickle(cd2cd_path / 'mask.pkl')

    #cd2cd_df = pd.read_csv(cd2cd_path / 'cd2cd.txt', header=0, index_col=0)
    #mask_df = pd.read_csv(cd2cd_path / 'mask.txt', header=0, index_col=0)
    
    ##change the type of index and column from str to int due to scan
    #cd2cd_df.index = cd2cd_df.index.astype(int)
    #cd2cd_df.columns = cd2cd_df.columns.astype(int)
    #mask_df.index = mask_df.index.astype(int)
    #mask_df.columns = mask_df.columns.astype(int)

   
else:        
    print("-----------------------------")
    print("Neither cd2cd.txt nor mask.txt exist.")
    print("gauge files are loading ...")
    print(".")
    print(".")
    print(".")  

    for i,j in enumerate(cal_data['result_yaml']['Result']):
        gauge_file = Path(j['Path']) / 'gauge.txt'
        #df_name = str('df_' + str(i))
        df_name = pd.read_csv(gauge_file, sep=' ')
        #print(str("result" + str(i) + " is loading.."))
        df_name["ID"] = i
        df_list.append(df_name)

    n_of_gauge = int(df_list[0].shape[0])

    df = pd.concat(df_list)

    zeros = np.zeros((cal_data['tasks'],cal_data['tasks']))
    print("-----------------------------")    
    print("cd2cd data framing starts. It takes 8 min for 500 models roughtly")
    print(".")
    print(".")
    print(".")

    

    #result_list = []
    #for i in range(cal_data['tasks']):
    #    name = str('result' + str(i)) #result0, result1
    #    result_list.append(name)


    cd2cd_df = pd.DataFrame(zeros, columns=result_list, index=result_list)
    mask_df = copy.deepcopy(cd2cd_df)

    #CD_diff_df = (df[df["ID"] == 0]["simcd_resist"] - df[df["ID"] == 1]["simcd_resist"]).sum()

    for l in range(cal_data['tasks']):
        for m in range(cal_data['tasks']):
            #print(str(str(l) + " by " + str(m) + "....."))
            #cd2cd_df.iloc[l][str('result' + str(m))] = (df[df["ID"] == l]["simcd_resist"] - df[df["ID"] == m]["simcd_resist"]).sum()
            cd2cd_df.iloc[l][m] = 1/(n_of_gauge-1) *(((df[df["ID"] == l]["simcd_resist"]) - (df[df["ID"] == m]["simcd_resist"]))**2).sum() 

            # masking if there are any CD missing
            if((df[df["ID"]==l]["opt_out"].max()==1) | (df[df["ID"]==m]["opt_out"].max()==1)):
                mask_df.iloc[l][m] = 1
            else:
                mask_df.iloc[l][m] = 0


        if( l == int(int(cal_data['tasks']) * 0.3) ):
            print("30% done")
        elif( l == int(int(cal_data['tasks']) * 0.8) ):
            print("80% done")
        else:
            pass

    cd2cd_df.to_pickle(cd2cd_path / 'cd2cd.pkl')
    mask_df.to_pickle(cd2cd_path / 'mask.pkl')

    #cd2cd_df.to_csv(cd2cd_path / 'cd2cd.txt', header=1, index=1)
    #mask_df.to_csv(cd2cd_path / 'mask.txt', header=1, index=1)
    
    print("cd2cd dataframing is done ")



# 1. Variance s^2 with mask
fig, ax1 = plt.subplots(figsize=(12, 12))

sns.heatmap(data=cd2cd_df, square=1, mask=mask_df.astype('bool'), vmin=0, cbar_kws={"shrink": 0.85}, ax=ax1, cmap = 'RdBu') #cmap = 'Accent') #cmap='Spectral') #, cmap='seismic')
ax1.set_xlabel("results")
ax1.set_ylabel("results")
plt.title("Variance (s^2)")
plt.savefig(cd2cd_path / 'cd2cd.png')
plt.close()

# 2. standard deviation sqrt(s^2) mapping
fig, ax2 = plt.subplots(figsize=(12, 12))

sns.heatmap(data=cd2cd_df.apply(np.sqrt), square=1, mask=mask_df.astype('bool'), vmin=0, cbar_kws={"shrink": 0.85}, cmap = 'RdBu') #cmap = 'Accent') #cmap='Spectral') #, cmap='seismic')
ax2.set_xlabel("results")
ax2.set_ylabel("results")
plt.title("Standard Deviation (s)")
plt.savefig(cd2cd_path / 'cd2cd_sd.png')
plt.close()

# 3. Pearson Correlation
cmap = sns.diverging_palette(230, 20, as_cmap=True)
cd2cd_df_corr = cd2cd_df.corr(method='pearson', min_periods=1)

fig, ax3 = plt.subplots(figsize=(12, 12))
sns.heatmap(cd2cd_df_corr, center = 0, mask=mask_df.astype('bool'), square=1, cbar_kws={"shrink": 0.85}, ax=ax3, vmin=-1, vmax=1, cmap = cmap) #, cmap=cmap, 
ax3.set_xlabel("results")
ax3.set_ylabel("results")
plt.title("Pearson Corr.")
plt.savefig(cd2cd_path / 'cd2cd_pearson_corr.png')
plt.close()



# 4. Clipping
cutting_list = list(np.arange(9,250,10))

for i,j in enumerate(cutting_list):
    cd2cd_df.sort_index(axis=0)
    cd2cd_df_trunc1 = cd2cd_df.truncate(after=j, axis=0)
    cd2cd_df_trunc2 = cd2cd_df_trunc1.truncate(after=j, axis=1)
    mask_df_trunc1 = mask_df.truncate(after=j, axis=0)  
    mask_df_trunc2 = mask_df_trunc1.truncate(after=j, axis=1)

    cd2cd_df_s = cd2cd_df.apply(np.sqrt)
    cd2cd_df_s.sort_index(axis=0) 
    cd2cd_df_s_trunc1 = cd2cd_df_s.truncate(after=j, axis=0)
    cd2cd_df_s_trunc2 = cd2cd_df_s_trunc1.truncate(after=j, axis=1)

    cd2cd_df_corr = cd2cd_df_trunc2.corr(method='pearson', min_periods=1)  

    #fig, ax4 = plt.subplots(figsize=(12, 12))
    #filename_s = str("cd2cd_clipping" + str(j) + "_by_" + str(j) + ".png")
    #sns.heatmap(data=cd2cd_df_trunc2, square=1, mask=mask_df_trunc2.astype('bool'), annot=False, fmt=".1f", cbar_kws={"shrink": 0.85}, ax=ax4) #, cmap = 'seismic') #cmap = 'Accent') #cmap='Spectral') #, cmap='seismic')
    #plt.savefig(cd2cd_path / filename_s)
    
    if(j <= 20):
        annot_flag = True
    else:
        annot_flag = False
    
    fig, ax5 = plt.subplots(figsize=(12, 12))
    filename_sqrt_s = str("cd2cd_clipping_sqrt_s" + str(j) + "_by_" + str(j) + ".png")
    sns.heatmap(data=cd2cd_df_s_trunc2.apply(np.sqrt), square=1, mask=mask_df_trunc2.astype('bool'), annot=annot_flag, fmt=".1f", cbar_kws={"shrink": 0.85}, ax=ax5) #, cmap = 'seismic') #cmap = 'Accent') #cmap='Spectral') #, cmap='seismic')
    ax5.set_xlabel("results")
    ax5.set_ylabel("results")
    plt.title("Standard Deviation")
    plt.savefig(cd2cd_path / filename_sqrt_s)
    plt.close()

    fig, ax6 = plt.subplots(figsize=(12, 12))
    filename_corr = str("cd2cd_clipping_corr_" + str(j) + "_by_" + str(j) + ".png")
    sns.heatmap(cd2cd_df_corr, cmap=cmap, center = 0, square=1, vmin=-1, vmax=1, mask=mask_df_trunc2.astype('bool'), annot=annot_flag, fmt=".1f", cbar_kws={"shrink": 0.85}, ax=ax6)
    ax6.set_xlabel("results")
    ax6.set_ylabel("results")
    plt.title("Pearson Corr.")
    plt.savefig(cd2cd_path / filename_corr)
    
    plt.close()
    
