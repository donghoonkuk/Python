import os, glob, sys, subprocess
from pathlib import Path
#from natsort import natsorted
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yaml
import re
#from mpl_toolkits.axes_grid1 import host_subplot
#from pyhtml import *

def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])


pwd = os.getcwd()
root = Path(pwd)
model_analysis = root / 'model_analysis'
log_analysis = model_analysis / 'log_analysis'
pngs = log_analysis / 'pngs'

#if log_analysis.exists():
#    import shutil
#    shutil.rmtree(log_analysis, ignore_errors=True)
#else:
#    log_analysis.mkdir(exist_ok=True)
#    pngs.mkdir(exist_ok=True)
model_analysis.mkdir(exist_ok=True)
log_analysis.mkdir(exist_ok=True)
pngs.mkdir(exist_ok=True)



log = root / 'log'
#logs = [x for x in log.iterdir() if x.is_dir()]
master_logs = glob.glob('log/*.log')
recent_master_log = root / max(master_logs, key=os.path.getctime)

result = root / 'result'					# result directory itself
result_yaml_file = result / 'result.yaml'
result_yaml = yaml.load(result_yaml_file.open(), Loader=yaml.FullLoader)
#results = [x for x in result.iterdir() if x.is_dir()]
list_of_parameters = list(result_yaml['Result'][0]['Parameters']['Resist'].keys())
list_of_parameters.remove('OpticalThreshold')
list_of_parameters.remove('Threshold')
dic_of_parameters = {}


# Model validation test
out = subprocess.Popen(['wc', '-l', './result/result.yaml'],
	stdout = subprocess.PIPE,
	stderr = subprocess.STDOUT,
	universal_newlines=True).communicate()[0]
result_yaml_wc = out.split()[0]

if 3 < int(result_yaml_wc):
	print("The result.yaml is valid \n")
else:
	print("The result.yaml is invalid \n")


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


master_file = open(recent_master_log, 'r')
master_line = master_file.readlines()

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


server_list = servernames.split(",")
master_server = server_list[0]
slave_server = []
slaveworker_file_list = []

configuration = yaml.load((root / conf_yaml_file).open(), Loader=yaml.FullLoader)


for l,m in enumerate(server_list[1:]):
    slave_full_name = "slave-" + str(l+1) + "-" + m
    x = log.joinpath(slave_full_name)
    slave_server.append(x)				# slave_server became PosixPath list object

for i,j in enumerate(slave_server):
    slaveworker_file_list.append(sorted(j.rglob("slaveworker*.log")))
slaveworker_file_list = flatten(slaveworker_file_list)

#### MP/DP mode recog end #######




####### RegEx START ###############################
IPOPT_loop = re.compile(r"""
 ^LinearSolver:\s*Returned\(seed:(\d*)     # IPOPT Seed Number
 ,\s*iterations:(\d*)                      # IPOPT Iter Number
 ,\s*cost:(\d*\.?\d*)\)                    # IPOPT cost
""", re.VERBOSE)



IPOPT_selected_seed = re.compile(r"""
 ^LinearSolver:\s*Seed\s(\d*)\sis\spicked      # group(1), Check the consistency from the IPOPT_loop data
""", re.VERBOSE)

############################################################
# cost catch for NLOPT + IPOPT
#IPOPT_selected_cost = re.compile(r"""
# ^LinearEngine:\s*[l|L]inear\s*solver\s*cost\s*=\s*(\d*\.?\d*)      # group(1), Check the consistency from the IPOPT_loop data
#""", re.VERBOSE)

############################################################
# cost catch for optimizer plus operator 
IPOPT_selected_cost = re.compile(r"""
 ^[l|L]inear\s*solver\s*cost\s*=\s*(\d*\.?\d*)      # group(1), Check the consistency from the IPOPT_loop data
""", re.VERBOSE)



FindNext_Resist = re.compile(r"""
 ^CooptEngine:{0,2}[f|F]\w+:\s+[d|D]\w+\[(\d*)\]          # CooptEngine Iter Number
 ,\s[r|R][e][s][i][s][t]:(\w+)                            # Name of NL_parameter
 #,\s[r|R][e][s][i][s][t]:([a-z]+)                        # Name of NL_parameter when Optical parameter is listed on. ( /user/cbm/SALT_Research/001_Surface_Kernel_Issues/Case_Collecting/2022_SALTDEV_1216_Abnormal_RI_contour_debug_ticket/ORIGINAL_model_pskang )
 :\w+:\s\w+\s(-?\d*\.?\d*)                                # NL_parameter From
 \s\w+\s(-?\d*\.?\d*)                                     # NL_parameter To
""", re.VERBOSE)


#d 
FindNext_ThrowBack = re.compile(r"""
 ^WARNING:\s*CooptEngine:{0,2}[f|F]\w+:\s.*\[(\d*)\]      # group(1) ThrowBack CooptEngine Iter Number. loglevel 10 only
""", re.VERBOSE)




Task = re.compile(r"""
 ^Task\s*(\d*)                            # group(1) Task number
 \s*([S|E|D]\w*)                          # group(2) Start|End|Duration
 :\s*((\d*-\d*-\d*)|(\d*\.?\d*))          # group(3,4) are the date for Start|End OR group(3,5) are Duration for the duration
 \s*((\d*:\d*:\d*)|(\w*))                 # group (6,7) are the time for Start|End OR group(6,8) are the character s for unit
 """, re.VERBOSE)

####### RegEx END ###############################



####### log file loading start ##################
log_file_list = []

if (mpdp_mode == 's'):
    print('MPDP mode is single. \n')
    log_file_list.append(log / master_server / 'single.log')
    f = open(log_file_list[0], 'r')

elif (mpdp_mode == 'm'):
    print('MPDP mode is single and multi-threading. \n')
    if ((log / master_server / 'single.log').exists()):             # s=1, n=1
        log_file_list.append(log / master_server / 'single.log')
    else:                                                           #s=1, n is multi
        #slaveworker_file_list = server_list
        #slave_server = server_list
        x = log.joinpath(server_list[0])
        slave_server.append(x)				# slave_server became PosixPath list object
        slaveworker_file_list.append(sorted(x.rglob("slaveworker*.log")))
        slaveworker_file_list = flatten(slaveworker_file_list)

        merged_logs = open("./model_analysis/log_analysis/log_merged.txt", 'w')
        for i in slaveworker_file_list:
            f = open(i, 'r')
            line = f.readlines()
            for j in line:
                merged_logs.write(j)
        merged_logs.close()
        f = open('./model_analysis/log_analysis/log_merged.txt', 'r')



elif (mpdp_mode == 'M'):
    print('MPDP mode is DP. \n')
    merged_logs = open("./model_analysis/log_analysis/log_merged.txt", 'w')
    for i in slaveworker_file_list:
        f = open(i, 'r')
        line = f.readlines()
        for j in line:
            merged_logs.write(j)
    merged_logs.close()
    f = open('./model_analysis/log_analysis/log_merged.txt', 'r')
        #slaveworkers = i.glob('slaveworker*.log')
        #print(slaveworkers)
else:
    pass





print("Loading the slavewoker logs ......\n")




log_data = open("./model_analysis/log_analysis/log_data.csv", 'w')


line = f.readlines()

# initialization
index = 0
line_number = 1
task_id = 0
CooptEngine_iter_number = 0
selected_cost = 0.0
#Seed_ID = 0



##### DataFrame()
column_name = ["line_num", "task_id", "task_status", "task_stamping_date", "task_stamping_time", "seed_id", "IPOPT_iter_num", "cost", "selected_seed", "selected_cost","CooptEngine_iter_num", "parameter", "init", "fin", "lower_bound", "upper_bound", "throwback_point"]
log_data.write('line_num,task_id,task_status,task_stamping_date,task_stamping_time,seed_id,IPOPT_iter_num,cost,selected_seed,selected_cost,CooptEngine_iter_num,parameter,init,fin,lower_bound,upper_bound,throwback_point\n')


#column_name = column_name + parameters


#df_slaveworker = pd.DataFrame(columns = column_name)




print("Parsing the slaveworker log ....... \n")

for index,logging in enumerate(line):
    Task_info_data = Task.match(logging)
    IPOPT_data = IPOPT_loop.match(logging)
    Selected_seed = IPOPT_selected_seed.match(logging)
    Selected_cost = IPOPT_selected_cost.match(logging)
    Find_Next_Resist = FindNext_Resist.match(logging)
    Find_ThrowBack_data = FindNext_ThrowBack.match(logging)

        #Task info search:
    if (Task_info_data is not None):

        line_number = index + 1                           # int
        task_id =  Task_info_data.group(1)                # str
        Task_status = Task_info_data.group(2)             # str
        Task_stamping_date = Task_info_data.group(3)      # str
        Task_stamping_time = Task_info_data.group(6)      # str

#        data = {'line_num': line_number, 'task_id': task_id, 'task_status': Task_status, 'task_stamping_date': Task_stamping_date, 'task_stamping_time': Task_stamping_time}
#        df_slaveworker = df_slaveworker.append(data, ignore_index=True)
        #log_data.write(str(line_number) +" Task id: "+ task_id +" Task status: "+ Task_status +" Date "+ Task_stamping_date +" Time "+ Task_stamping_time + "\n")
        #log_data.write('{"line_num": ' + str(line_number) + ', "task_id": ' + task_id + ', "task_status": "'+ Task_status + '", "task_stamping_date": "' + Task_stamping_date + '", "task_stamping_time": "' + Task_stamping_time + '"}\n')
        #log_data.write(str(line_number) + ',' + task_id + ',' + Task_status + ',' + Task_stamping_date + ',' + Task_stamping_time + ',NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN' + '\n')
        log_data.write(str(line_number) + ',' + task_id + ',' + Task_status + ',' + Task_stamping_date + ',' + Task_stamping_time + ',,,,,,,,,,' + '\n')
 #+" Task id: "+ task_id +" Task status: "+ Task_status +" Date "+ Task_stamping_date +" Time "+ Task_stamping_time + "\n")



    elif ((IPOPT_data is not None) or (Selected_seed is not None) or (Selected_cost is not None)):
        if (IPOPT_data is not None):
            line_number = index + 1
            Seed_ID = IPOPT_data.group(1)
            IPOPT_Iter_number = IPOPT_data.group(2)
            cost = IPOPT_data.group(3)

#            data = {'line_num': line_number, 'task_id': task_id, 'seed_id': Seed_ID, 'IPOPT_iter_num': IPOPT_Iter_number, 'cost': cost}
#            df_slaveworker = df_slaveworker.append(data, ignore_index=True)
            #log_data.write('{"line_num": ' + str(line_number) + ', "task_id": ' + task_id + ', "seed_id": ' + Seed_ID + ', "IPOPT_iter_num": ' + IPOPT_Iter_number + ', "cost": ' + cost + '}\n')
            #log_data.write(str(line_number) + ',' + task_id + ',NaN,NaN,NaN,' + Seed_ID + ',' + IPOPT_Iter_number + ',' + cost + ',NaN,NaN,NaN,NaN,NaN,NaN,NaN' + '\n')
            log_data.write(str(line_number) + ',' + task_id + ',,,,' + Seed_ID + ',' + IPOPT_Iter_number + ',' + cost + ',,,,,,,' + '\n')

        elif (Selected_seed is not None):
            line_number = index + 1
            selected_seed = Selected_seed.group(1)

#            data = {'line_num': line_number, 'selected_seed': selected_seed}
#            df_slaveworker = df_slaveworker.append(data, ignore_index=True)
            #log_data.write(str(line_number) + ',' + task_id + ',NaN,NaN,NaN,NaN,NaN,NaN,' + selected_seed + ',NaN,NaN,NaN,NaN,NaN,NaN' + '\n')
            log_data.write(str(line_number) + ',' + task_id + ',,,,,,,' + selected_seed + ',,,,,,' + '\n')

        elif (Selected_cost is not None):
            line_number = index + 1
            selected_cost = Selected_cost.group(1)

#            data = {'line_num': line_number, 'selected_cost': selected_cost}
#            df_slaveworker = df_slaveworker.append(data, ignore_index=True)
            #log_data.write(str(line_number) + ',' + task_id + ',NaN,NaN,NaN,NaN,NaN,NaN,NaN,'+ selected_cost + ',NaN,NaN,NaN,NaN,NaN' + '\n')
            log_data.write(str(line_number) + ',' + task_id + ',,,,,,,,'+ selected_cost + ',,,,,' + '\n')
        else:
            pass

    elif ((Find_Next_Resist is not None) or (Find_ThrowBack_data is not None)):
        if (Find_Next_Resist is not None):
            line_number = index + 1
            Coopt_Iter_number = Find_Next_Resist.group(1)
            parameter = Find_Next_Resist.group(2)
            init = Find_Next_Resist.group(3)
            fin = Find_Next_Resist.group(4)
            lower_bound = configuration['Configuration']['Resist']['Parameters'][parameter]['min']
            upper_bound = configuration['Configuration']['Resist']['Parameters'][parameter]['max']

#            data = {'line_num': line_number, 'CooptEngine_iter_num': Coopt_Iter_number}, '': NL_parameter, '': }
#            df_slaveworker = df_slaveworker.append(data, ignore_index=True)
            #log_data.write(str(line_number) + task_id + ', "CooptEngine_iter_num": ' + Coopt_Iter_number + ', "parameter": ' + parameter + ', "lower": ' + lower + ', "upper": ' + upper + "}\n")
            log_data.write(str(line_number) + ',' + task_id + ',,,,,,,,' + str(selected_cost) + ',' + Coopt_Iter_number + ',' + parameter + ',' + init + ',' + fin + ',' + str(lower_bound) + ',' + str(upper_bound) + '\n')
            #print(f'Progress: {line_number/log_lines:.2f}.')

        elif (Find_ThrowBack_data is not None):
            line_number = index + 1
            ThrowBack_point = Find_ThrowBack_data.group(1)

#            data = {'line_num': line_number, 'throwback_point': ThrowBack_point}
#            df_slaveworker = df_slaveworker.append(data, ignore_index=True)
            #log_data.write(str(line_number) +"ThrowBack Iter num: "+ ThrowBack_point +" "+ "\n")
            log_data.write(str(line_number) + ',' + task_id + ',,,,,,,,,,,,' + ThrowBack_point + '\n')
            #print(f'Progress: {line_number/log_lines:.2f}.')
        else:
            pass

    pass


print("Parsing is Done ! \n\n")

print("Data writing ...... \n")
log_data.close()
print("Data writing is Done ! \n")


# Pandas
print("DB dumping ......\n")
df = pd.read_csv('./model_analysis/log_analysis/log_data.csv')
print("DB dumping is Done! \n")

task_min = df['task_id'].min()
task_max = df['task_id'].max()
task_list = list(range(task_min, task_max + 1, 1))
best_task = df.loc[df['selected_cost'].idxmin()]['task_id']

print('Total tasks: ' + str(task_max + 1) + ' tasks \n')


## df_task dictionary generation
df_task_split = {}
name_of_parameter = ''
linear_solver_cost_list = []

for i in task_list:
    key = "df_task_" + str(i)
    df_task = df[df['task_id'] == task_list[i]]
    df_task_split.update({key: df_task})

    xlim_min = 0
    xlim_max = int(df_task_split[key]['CooptEngine_iter_num'].max())

    linear_solver_cost_list = df_task_split[key]['selected_cost'].dropna()

    print(key + ' DataFraming is under processing......\n')

    for j in range(len(list_of_parameters)):
        name_of_parameter = list_of_parameters[j]
        #print(name_of_parameter)
        df_task_parameter_filtered = df_task[df_task['parameter'] == list_of_parameters[j]]
        #print(df_task_parameter_filtered)
        #df_task_parameter.filtered = key

        x1 = df_task_parameter_filtered['CooptEngine_iter_num']
        #x2 = list(range(xlim_min, int(xlim_max + 1), 1))
        y_init = df_task_parameter_filtered['init']
        y_fin = df_task_parameter_filtered['fin']
        y_lower_bound = df_task_parameter_filtered['lower_bound']
        y_upper_bound = df_task_parameter_filtered['upper_bound']
        cost = df_task_parameter_filtered['selected_cost']



        fig = plt.figure(figsize=(6.4,4))
        ax1 = fig.subplots()

        ax1.plot(x1, y_init, x1, y_fin, marker='.', label=('init','fin'))
        ax1.fill_between(x1, y_lower_bound, y_upper_bound, alpha=0.2)
        ax1.grid(True)
        ax1.legend(['init', 'fin'])
        ax1.set_xlim(xlim_min, xlim_max*1.01)
        ax1.set_xlabel('CooptEngine_iter_number')
        ax1.set_title(str(name_of_parameter) +' '+ '(task_' + str(i) + ', ' + str(j+1) + '/' + str(len(list_of_parameters)) + ')')

        ax2 = ax1.twinx()
        ax2.plot(x1, cost, marker='+', color='gray', linewidth='0.7')
        ax2.set_ylabel('linear solver cost', color='gray')
#        ax2.set_ylim([1, 8])
        ax2.tick_params(axis='y', labelcolor='gray')

        plt.tight_layout()

        png_filename = str('./model_analysis/log_analysis/pngs/' + 'task_' + str(i) + '_' + str(j+1) + '_' + name_of_parameter + '.png')
        fig.savefig(png_filename)   #, dpi=600)

        plt.close()

best_task = df.loc[df['selected_cost'].idxmin()]['task_id']

figures = sorted(pngs.glob('*.png'),key=os.path.getmtime)


######## html generator start ########
html_head = '''
<html lang="en">
 <head>
  <title>SALT Calibration Review</title>
 </head>
 <body>
 Best Task :
 '''

text_1 = '''<img src=\"'''
text_3 = '''\" style=\"border:1px solid black\" height=\"300\" width=\"480\"><br/>'''
text = ''

for i in figures:
    text_2 = str(i)
    text_con = text_1 + text_2 + text_3 + '\n'
    text = text + text_con


html_tail = '''
 </body>
</html>
'''


html_file = open("./model_analysis/log_analysis/log_analysis_report.html", 'w')
full_content = html_head + str(best_task) + '<br/>' + text + html_tail
html_file.write(full_content)
html_file.close()

######## html generator end ########


print('=========================\n')
print('Best task: ' + str(best_task) + '\n')
print('=========================\n')

