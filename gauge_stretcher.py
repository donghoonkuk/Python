import os, glob, sys, subprocess
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import re
import pickle
import shutil
from pathlib import Path
sys.path.append('/user/cbm/python_package/SALT/package')

#To prevent the ON/OFF is interpreated to true/false in yaml load
sys.path.append('/user/dw1409kang/Python/myModule/SALT/Yaml') 
from Loader import load_yaml_raw 



pwd = os.getcwd()
root = Path(pwd)
log = root / 'log'
master_logs = glob.glob('log/*.log')
recent_master_log = root / max(master_logs, key=os.path.getctime)
result = root / 'result'
result_yaml_file = result / 'result.yaml'
result_yaml = load_yaml_raw(result_yaml_file)
model_analysis = root / 'model_analysis'
seeding = model_analysis / 'seeding'
gauge_stretcher = model_analysis / 'gauge_stretcher'

model_analysis.mkdir(exist_ok=True)
gauge_stretcher.mkdir(exist_ok=True)

master_file = open(recent_master_log, 'r')
master_line = master_file.readlines()
#### loglevel, MP/DP mode and configuration.yaml recog start #######
loglevel_regexp = re.compile(r"""
 ^option:\s*loglevel\s*value:\s*(\d*)       # group(1): loglevel
 """, re.VERBOSE)

MPDP_regexp = re.compile(r"""
 -m\s(\w)                                   # group(1): MPDP mode. s: single, m: single and multithread, M: DP model
 """, re.VERBOSE)

server_list_regexp = re.compile(r"""
 -s\s([a-zA-Z0-9_,]*)                       # group(1): assigned master and slaves
 """, re.VERBOSE)

conf_yaml_regexp = re.compile(r"""
 -c\s*(\w*.yaml)                            # group(1): conf.yaml
 """, re.VERBOSE)


for index, logging in enumerate(master_line):
    MPDP = MPDP_regexp.search(logging)
    serverlist = server_list_regexp.search(logging)
    loglevel = loglevel_regexp.match(logging)
    conf_yaml = conf_yaml_regexp.search(logging)

    if (MPDP is not None):
        mpdp_mode = MPDP.group(1) 		# group(1): MPDP mode. s: single, m: single and multithread, M: DP model
    else:
        pass

    if (conf_yaml is not None):
        conf_yaml_file = conf_yaml.group(1)

    if (serverlist is not None):
        servernames = serverlist.group(1)
    else:
        pass

    if (loglevel is not None):
        loglevel = int(loglevel.group(1))
    else:
        pass


# Configuration load and trimming 
configuration = load_yaml_raw(root / conf_yaml_file)
configuration['Configuration']['Model'] = str(root / 'input_model') 
configuration['Configuration']['Resist']['Dispatch']['Random'] = 1
configuration['Configuration']['Mask']['Thread'] = 1
configuration['Configuration']['Mask']['Clip_Thread'] = 1
configuration['Configuration']['Optics']['Thread'] = 1
configuration['Configuration']['Resist']['Thread'] = 1
configuration['Configuration']['Tcc']['Thread'] = 1
configuration['Configuration']['Mask']['GPU'] = 'OFF'
configuration['Configuration']['Tcc']['GPU'] = 'OFF'
configuration['Configuration']['Optics']['GPU'] = 'OFF'
configuration['Configuration']['Resist']['GPU'] = 'OFF'


cal_gauge = configuration['Configuration']['Gaugefile']
cal_gauge_df = pd.read_csv(cal_gauge, delim_whitespace=True, keep_default_na=False)


cal_gauge_df = cal_gauge_df.astype({'startx': 'float64'})
cal_gauge_df = cal_gauge_df.astype({'starty': 'float64'})
cal_gauge_df = cal_gauge_df.astype({'endx': 'float64'})
cal_gauge_df = cal_gauge_df.astype({'endy': 'float64'})
cal_gauge_df = cal_gauge_df.astype({'wafercd': 'float64'})



#cal_gauge_df["center_x"] = cal_gauge_df["startx"] + (cal_gauge_df["startx"] + cal_gauge_df["endx"])/2
#cal_gauge_df["center_y"] = cal_gauge_df["starty"] + (cal_gauge_df["starty"] + cal_gauge_df["endy"])/2
cal_gauge_df["center_x"] = cal_gauge_df[['startx', 'endx']].mean(axis=1)
cal_gauge_df["center_y"] = cal_gauge_df[['starty', 'endy']].mean(axis=1)

cal_gauge_df = cal_gauge_df.astype({'center_x': 'float64'})
cal_gauge_df = cal_gauge_df.astype({'center_y': 'float64'})


# add HV
cal_gauge_df['HV'] = ''
cal_gauge_df['HV'] = np.where(cal_gauge_df['starty']==cal_gauge_df['endy'],'H',np.where(cal_gauge_df['startx']==cal_gauge_df['endx'],'V','Diag'))



# 1. original guage
# 2. symmetric wafer_cd 10-200 % manipulated gauge 
# 2-1. left only
# 2.2. right only
stretching_ratio = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 4.0, 6.0, 8.0, 10.0, 20.0]
shifting = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 4.0, 6.0, 8.0]

#mkdir(gauge_stretcher,exist_ok=True)



for i,j in enumerate(stretching_ratio):

    sub_dir = gauge_stretcher/str('wfcd_' + str(j))
    sub_dir.mkdir(exist_ok=True)
    print('wfcd_', j, ' is created')

    sub_conf = sub_dir / 'conf_gauge_stretch.yaml'
    sub_gauge = sub_dir / str('gauge_wfcd_' + str(j) + '.txt')
    configuration['Configuration']['Gaugefile'] = str(sub_gauge)

    sub_conf.touch(exist_ok=True)
    with open(sub_conf, 'w') as f:
        yaml.dump(configuration, f)

    gauge_df = cal_gauge_df.copy(deep=True)

#    cal_gauge_df_copy.mask(cal_gauge_df_copy['HV']==H, cal_gauge_df_copy['startx']=cal_gauge_df_copy['wafercd']*j*0.5, inplace=True)
    gauge_df.loc[gauge_df["HV"]=="H","startx"] = gauge_df["center_x"] - gauge_df["wafercd"]*0.5*j
    gauge_df.loc[gauge_df["HV"]=="H","endx"] = gauge_df["center_x"] + gauge_df["wafercd"]*0.5*j
    gauge_df.loc[gauge_df["HV"]=="V","starty"] = gauge_df["center_y"] - gauge_df["wafercd"]*0.5*j
    gauge_df.loc[gauge_df["HV"]=="V","endy"] = gauge_df["center_y"] + gauge_df["wafercd"]*0.5*j


    #cal_gauge copy and dump
#    sub_gauge = sub_dir / str('gauge_wfcd_' + str(j) + '.txt') 

    gauge_df.to_csv(sub_gauge, index=0 , sep=' ') 

    shutil.copy('/user/cbm/python_package/SALT/package/run_scripts/run_for_gauge_stretcher.sh', sub_dir / 'run.sh')




for i,j in enumerate(shifting):
    sub_dir = gauge_stretcher/str('center_shifting_' + str(j))
    sub_dir.mkdir(exist_ok=True)
    print('center_shifting_', j, ' is created')

    sub_conf = sub_dir / 'conf_gauge_shifting.yaml'
    sub_gauge = sub_dir / str('gauge_shifting_' + str(j) + '.txt')
    configuration['Configuration']['Gaugefile'] = str(sub_gauge)

    sub_conf.touch(exist_ok=True)
    with open(sub_conf, 'w') as f:
        yaml.dump(configuration, f)

    gauge_df = cal_gauge_df.copy(deep=True)

#    cal_gauge_df_copy.mask(cal_gauge_df_copy['HV']==H, cal_gauge_df_copy['startx']=cal_gauge_df_copy['wafercd']*j*0.5, inplace=True)
    gauge_df.loc[gauge_df["HV"]=="H","startx"] = gauge_df["startx"] - j 
    gauge_df.loc[gauge_df["HV"]=="H","endx"] = gauge_df["endx"] -j 
    gauge_df.loc[gauge_df["HV"]=="V","starty"] = gauge_df["starty"] - j 
    gauge_df.loc[gauge_df["HV"]=="V","endy"] = gauge_df["endy"] -j 

    gauge_df.to_csv(sub_gauge, index=0 , sep=' ') 

    shutil.copy('/user/cbm/python_package/SALT/package/run_scripts/run_for_gauge_shift.sh', sub_dir / 'run.sh')




#make RUN.sh
with open(gauge_stretcher / 'RUN.sh', 'w') as f:
    f.write("#!/bin/bash\n")
    for a,b in enumerate(gauge_stretcher.iterdir()):
       if b.is_dir():
           f.write("cd ")
           f.write(str(b))
           f.write("\n")
           f.write("./run.sh\n")
           #f.write("cd ../\n")
       else:
           pass
os.chmod('./model_analysis/gauge_stretcher/RUN.sh', 0o755)

#cal_gauge_df_copy.loc[0, 'wafercd']
