import os, glob, sys, subprocess
import pandas as pd
import numpy as np
from pathlib import Path
import re
import copy

#for loading xTal image.txt 
sys.path.append('/user/devsalt/USER/CNR/3.SQA/SCRIPTS')
import mycal

#To prevent the manipulating of ON/OFF into true/false in yaml loading
sys.path.append('/user/dw1409kang/Python/myModule/SALT/Yaml') 
from Loader import load_yaml_raw 


class model_analysis:
#    def __init__(self):
#        self.result

    def caldirs(self, dir):     # returns: dict_keys(['result', 'result_yaml', 'conf_yaml', 'tasks'])
        dirs_dict = {}
        #pwd = os.getcwd() #is transfered
        self.dir = dir 
        root = Path(dir)
        
        # result part
        result = root / 'result' # result directory itself
        result_yaml_file = result / 'result.yaml'
        result_yaml = load_yaml_raw(result_yaml_file)

    
 #       ### Model validation test
 #       out = subprocess.Popen(['wc', '-l', './result/result.yaml'],
 #       	stdout = subprocess.PIPE,
 #       	stderr = subprocess.STDOUT,
 #       	universal_newlines=True).communicate()[0]
 #       result_yaml_wc = out.split()[0]
 #       
 #       if 3 < int(result_yaml_wc):
 #       	print("The result.yaml is valid \n")
 #       else:
 #       	print("The result.yaml is invalid \n")

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

        # log part
        log = root / 'log'
        #master_logs = glob.glob('log/*.log')
        master_logs = list(log.glob('*.log'))
        recent_master_log = root / max(master_logs, key=os.path.getctime)

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

        # conf part
        configuration = load_yaml_raw(root / conf_yaml_file)

        optimization_tables = sorted(log.rglob("optimization*.txt")) #load all optimization_##.txt files under the log directory
        tasks = len(optimization_tables)

        nl_parameter_init_table = {}
        nl_parameter_fin_table = {}
        
        final_model_result_num = 0
        final_model_parameter_table = result_yaml['Result'][final_model_result_num]['Parameters']['Resist']

        #loading optimization table
        for i, optimization_table in enumerate(optimization_tables):
           #print(optimization_table, ' is loaded.')
           df = pd.read_csv(optimization_table, sep='\t', skiprows=1)
           nl_name = df['nl_parameter'].unique()  #parameters
           nl_fins = result_yaml['Result'][i]['Parameters']['Resist']
        
           #loading parameters in each table and add it to the dict.
           for parameter in nl_name[1:]:
               init = float(df.loc[(df['nl_parameter'] == parameter), "NLP_INI"].to_numpy()[0])  #it is returned as str
               #print(parameter, ' init: ', init)
               if ((parameter in nl_parameter_init_table) is not True):
                   #print('no. This is first iter')
                   nl_parameter_init_table[parameter] = [init] #append as a list
                   #print('fin_', parameter, ': ', nl_fins[parameter])
                   nl_parameter_fin_table[parameter] = [nl_fins[parameter]]
               else:
                   nl_parameter_init_table[parameter].append(init)
                   #print('fin: ', parameter, ': ', nl_fins[parameter])
                   nl_parameter_fin_table[parameter].append(nl_fins[parameter])
                   #print('yes. it is in')           
        
        # model part 
        #model_path = result / 'result0' / 'Model_TCC_1_0' 
        #model_gauge = result / 'result0' / 'gauge.txt' 
        #model_yaml_file = model_path / 'model.yaml' 
        #model_yaml = load_yaml_raw(model_yaml_file)

        dirs_dict['result'] = result
        dirs_dict['result_yaml'] = result_yaml
        dirs_dict['conf_yaml'] = configuration
        dirs_dict['tasks'] = tasks
        dirs_dict['conf'] = configuration 
 
        return dirs_dict

#        model_analysis = root / 'model_analysis'
#        log_analysis = model_analysis / 'log_analysis'
#        pngs = log_analysis / 'pngs' 


    def result_yaml_analysis(self, data):
        self.data = data

        ID = []
        Subtask_ID = []
        Resist_linear_cost = []
        #Resist_error_range = []
        #OpticsThreshold = []
        Optics_unweighted_rms = []
        Optics_weighted_rms = []
        #ResistThreshold = []
        Resist_unweighted_rms = []
        Resist_weighted_rms = []
        Best_Focus = []
        Image_Plane = []
        #gauge_path_list = []
        opt_out_list = []
    
        result_dict = {'ID': ID,
                       'Subtask_ID': Subtask_ID,
                       'Resist_linear_cost': Resist_linear_cost,
                       #'Resist_error_range': Resist_error_range,
                       #'OpticsThreshold': OpticsThreshold,
                       'Optics_unweighted_rms': Optics_unweighted_rms,
                       'Optics_weighted_rms': Optics_weighted_rms,
                       #'ResistThreshold': ResistThreshold,
                       'Resist_unweighted_rms': Resist_unweighted_rms,
                       'Resist_weighted_rms': Resist_weighted_rms,
                       'Best_Focus': Best_Focus,
                       'Image_Plane': Image_Plane,
                       #'gauge_path': gauge_path_list,
                       'opt_out': opt_out_list}
    
        for i,j in enumerate(data['result_yaml']['Result']):
            result_df = pd.DataFrame.from_dict(j)

            par_df = pd.DataFrame.from_dict([result_df.loc['Resist']['Parameters']])
            coeff_df = pd.DataFrame.from_dict([result_df.loc['Resist_Coefficients']['Parameters']])
            merge_df_temp = pd.concat([par_df, coeff_df], axis=1)
            if(i==0):
                merge_df = copy.deepcopy(merge_df_temp)
            else:
                merge_df = pd.concat([merge_df, merge_df_temp], axis=0)
   
            ID.append(result_df.loc["Optics"]["ID"])
            Subtask_ID.append(result_df.loc["Optics"]["Subtask_ID"])
            Resist_linear_cost.append(result_df.loc["Optics"]["Resist_linear_cost"])
            #Resist_error_range.append(result_df.loc["Optics"]["Resist_error_range"])
            #OpticsThreshold.append(result_df.loc["Optics"]["OpticsThreshold"])
            Optics_unweighted_rms.append(result_df.loc["Optics"]["Optics_unweighted_rms"])
            Optics_weighted_rms.append(result_df.loc["Optics"]["Optics_weighted_rms"])
            #ResistThreshold.append(result_df.loc["Optics"]["ResistThreshold"])
            Resist_unweighted_rms.append(result_df.loc["Optics"]["Resist_unweighted_rms"])
            Resist_weighted_rms.append(result_df.loc["Optics"]["Resist_weighted_rms"])
            Best_Focus.append(result_df.loc["Optics"]["Parameters"]["Best_Focus"])
            Image_Plane.append(result_df.loc["Optics"]["Parameters"]["Image_Plane"])
            #gauge_path_list.append(result_df.loc["Optics"]["Path"])
            gauge_file = Path(result_df.loc["Optics"]["Path"]) / 'gauge.txt'
            gauge_df = pd.read_csv(gauge_file, sep=' ')
            opt_out_list.append(gauge_df["opt_out"].max())
            
        result_df = pd.DataFrame.from_dict(result_dict)
        result_df = result_df.reset_index()
        merge_df = merge_df.reset_index()
        result_df = pd.concat([result_df, merge_df], axis=1)
        return result_df
