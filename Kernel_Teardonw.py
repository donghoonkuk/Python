import os, glob, sys, subprocess
from pathlib import Path

#for loading xTal image.txt 
sys.path.append('/user/devsalt/USER/CNR/3.SQA/SCRIPTS')
import mycal

#To prevent the manipulating of ON/OFF into true/false in yaml loading
sys.path.append('/user/dw1409kang/Python/myModule/SALT/Yaml') 
from Loader import load_yaml_raw 

#import pandas as pd
import cv2
import copy
import shutil
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import yaml
import re
import math
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import MaxNLocator

np.seterr(divide='ignore', invalid='ignore')

pwd = os.getcwd()
root = Path(pwd)
log = root / 'log'
master_logs = glob.glob('log/*.log')
recent_master_log = root / max(master_logs, key=os.path.getctime)
master_file = open(recent_master_log, 'r')
master_line = master_file.readlines()

result = root / 'result' # result directory itself
result_yaml_file = result / 'result.yaml'
#result_yaml = yaml.load(result_yaml_file.open(), Loader=yaml.FullLoader)
result_yaml = load_yaml_raw(result_yaml_file)

model_path = result / 'result0' / 'Model_TCC_1_0' 
model_gauge = result / 'result0' / 'gauge.txt' 
model_yaml_file = model_path / 'model.yaml' 
#model_yaml = yaml.load(model_yaml_file.open(), Loader=yaml.FullLoader)
model_yaml = load_yaml_raw(model_yaml_file)


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


#configuration = yaml.load((root / conf_yaml_file).open(), Loader=yaml.FullLoader)  #load cal conf.yaml
configuration = load_yaml_raw(root / conf_yaml_file)
#configuration['Configuration']['Model'] = str(model_path) #replace model
configuration['Configuration']['Model'] = './input_model' #replace model
configuration['Configuration']['Gaugefile'] = str(model_gauge) #replace model
configuration['Configuration']['Mask']['Output'] = 'mi' #add mi output
#configuration['Configuration']['Mask']['Dispatch'].clear() 
#configuration['Configuration']['Mask']['Dispatch']['Wholespace'] = 'ON'
configuration['Configuration']['Tcc']['From'] = str(result) #add Tcc loading
configuration['Configuration']['Optics']['Output'] = 'ai' #add mi output
configuration['Configuration']['Resist']['Output'] = 'ri' #add mi output
del configuration['Configuration']['Optimizer'] # drop optimizer
del configuration['Configuration']['Resist']['Parameters'] # drop Parameters
del configuration['Configuration']['Resist']['Constraints'] # drop Parameters
del configuration['Configuration']['Resist']['Use_Kernel'] 
configuration['Configuration']['Resist']['Dispatch'].clear()
configuration['Configuration']['Resist']['Dispatch']['Wholespace'] = 'ON' 


KT =  root / 'Kernel_Teardown'
KE =  root / 'Kernel_Effectiveness'
if KT==1:
    shutil.rmtree(KT)
else: pass
if KE==1:
    shutil.rmtree(KE)
else: pass
KT.mkdir(exist_ok=True)
KE.mkdir(exist_ok=True)


# For loop for Kernel Teardown
for i, k in enumerate(model_yaml['Resist_Set'][0]['Resist']['Coefficients'].keys()): 
    # SEM_srk regular expression
    p_semsrk = re.compile('^SEM_srk\w+') 
    semsrk = p_semsrk.match(k) 
    # for the case of SEM_srk is in the model
    if semsrk: 
        kernel_name = semsrk.group() 
        sub_dir_KT = KT / kernel_name
        sub_dir_KE = KE / kernel_name
        if (sub_dir_KT.exists()) and (sub_dir_KE.exists()):
            pass
        else:
            sub_dir_KT_input_model = sub_dir_KT / "input_model" 
            sub_dir_KE_input_model = sub_dir_KE / "input_model" 
            sub_dir_KT.mkdir(exist_ok=True)
            sub_dir_KE.mkdir(exist_ok=True)
            # Kernel Teardown
            shutil.copytree(model_path, sub_dir_KT_input_model)
            shutil.copytree(model_path, sub_dir_KE_input_model)
            os.remove(sub_dir_KT_input_model / 'model.yaml')
            os.remove(sub_dir_KE_input_model / 'model.yaml')
            model_yaml_tmp = copy.deepcopy(model_yaml)
            model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].clear()
            model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].append(kernel_name)
            with open(sub_dir_KT_input_model / 'model.yaml', 'w') as f:
                yaml.dump(model_yaml_tmp, f)
            with open(sub_dir_KT / 'conf_simulation.yaml', 'w') as f:
                yaml.dump(configuration, f)
            shutil.copy('/user/donghoon.kuk/SALT/SALT_validation_set/run.sh', sub_dir_KT / 'run.sh')
            # Kernel Effectiveness
            model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].clear()
            model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'] = model_yaml['Resist_Set'][0]['Resist']['Use_Kernel']
            model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].remove(kernel_name) 
            with open(sub_dir_KE_input_model / 'model.yaml', 'w') as f:
                yaml.dump(model_yaml_tmp, f)
            with open(sub_dir_KE / 'conf_simulation.yaml', 'w') as f:
                yaml.dump(configuration, f)
            shutil.copy('/user/donghoon.kuk/SALT/SALT_validation_set/run.sh', sub_dir_KE / 'run.sh')
            print(i, k) 
    else: 
        kernel_name = k
        sub_dir_KT = KT / kernel_name
        sub_dir_KE = KE / kernel_name
        sub_dir_KT_input_model = sub_dir_KT / "input_model" 
        sub_dir_KE_input_model = sub_dir_KE / "input_model" 
        sub_dir_KT.mkdir(exist_ok=True)
        sub_dir_KE.mkdir(exist_ok=True)
        shutil.copytree(model_path, sub_dir_KT_input_model)
        shutil.copytree(model_path, sub_dir_KE_input_model)
        os.remove(sub_dir_KT_input_model / 'model.yaml')
        os.remove(sub_dir_KE_input_model / 'model.yaml')
        model_yaml_tmp = copy.deepcopy(model_yaml)
        # Kernel Teardown
        model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].clear()
        model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].append(k)
        with open(sub_dir_KT_input_model / 'model.yaml', 'w') as f:
            yaml.dump(model_yaml_tmp, f)
        with open(sub_dir_KT / 'conf_simulation.yaml', 'w') as f:
            yaml.dump(configuration, f)
        shutil.copy('/user/donghoon.kuk/SALT/SALT_validation_set/run.sh', sub_dir_KT / 'run.sh')
        # Kernel Effectiveness
        model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].clear()
        model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'] = model_yaml['Resist_Set'][0]['Resist']['Use_Kernel']
        model_yaml_tmp['Resist_Set'][0]['Resist']['Use_Kernel'].remove(k)
        with open(sub_dir_KE_input_model / 'model.yaml', 'w') as f:
            yaml.dump(model_yaml_tmp, f)
        with open(sub_dir_KE / 'conf_simulation.yaml', 'w') as f:
            yaml.dump(configuration, f)
        shutil.copy('/user/donghoon.kuk/SALT/SALT_validation_set/run.sh', sub_dir_KE / 'run.sh')

        print(i, k) 


#make RUN.sh
with open(KT / 'RUN.sh', 'w') as f:
    f.write("#!/bin/bash\n")
    for a,b in enumerate(KT.iterdir()):
       if b.is_dir():
           f.write("cd ./")
           f.write(b.stem)
           f.write("\n")
           f.write("./run.sh\n")
           f.write("cd ../\n")
       else:
           pass
os.chmod('./Kernel_Teardown/RUN.sh', 0o755)
shutil.copy('./Kernel_Teardown/RUN.sh', './Kernel_Effectiveness/RUN.sh')



#number_of_task = len(result_yaml.get('Result'))



#for i in result_yaml['Result']: 
#	#print(i['Path']) 
#	model_yaml_file = Path(i['Path'] + "/Model_TCC_1_0/model.yaml")  
#	model_yaml = yaml.load(model_yaml_file.open(), Loader=yaml.FullLoader)

#bumping = result_yaml['Result'][0]['Parameters']['Resist']['bumping']
#p2 = result_yaml['Result'][0]['Parameters']['Resist']['surf_pow2']



#pngs =  root / 'pngs'
#pngs.mkdir(exist_ok=True)

###############################################################################################
###############################################################################################
###############################################################################################
###############################################################################################
###############################################################################################
###############################################################################################
###############################################################################################
###############################################################################################
#####mi_txt_list = list((root / 'mi').glob('*.txt'))
#####mi_txt_list.sort()
#####ai_txt_list = list((root / 'ai').glob('*.txt'))
#####ai_txt_list.sort()
#####ri_txt_list = list((root / 'ri').glob('*.txt'))
#####ri_txt_list.sort()
#####
#####
#####
#####for i,j in enumerate(ai_txt_list):
#####    #ai_img = cv2.imread(str(j), 0) #load gray scale
#####    #ri_img = cv2.imread(str(ri_pgm_list[i]), 0)
#####
#####    # x = ai_img[0], y = ai_img[1], z = ai_img[2]
#####    mi_img = mycal.readXtalImage(mi_txt_list[i])[2]
#####    ai_img = mycal.readXtalImage(ai_txt_list[i])[2]
#####    ri_img = mycal.readXtalImage(ri_txt_list[i])[2]
#####
#####    #if (abs(ai_img_vmin) <= ai_img_vmax):
#####    #    ai_img_vmin = -ai_img_vmax
#####    #else:
#####    #    ai_img_vmax = -ai_img_vmin
#####
#####    window_x = 80 #80 #50 #in pxl
#####    window_y = 80 #80 #50 
#####    shift_x = 0 #2 
#####    shift_y = 0 
#####    center_x = ai_img.shape[1]/2 - shift_x
#####    center_y = ai_img.shape[0]/2 - shift_y
#####
#####    x_1 = int(center_x - window_x/2)
#####    y_1 = int(center_y - window_y/2)
#####    x_2 = int(center_x + window_x/2)
#####    y_2 = int(center_y + window_y/2)
#####
###### Full image
######    mi_img_clip = mi_img 
######    ai_img_clip = ai_img 
######    ri_img_clip = ri_img 
#####
###### Clipping image
#####    mi_img_clip = mi_img[y_1:y_2,x_1:x_2]
#####    ai_img_clip = ai_img[y_1:y_2,x_1:x_2]
#####    ri_img_clip = ri_img[y_1:y_2,x_1:x_2]
#####
#####    #ri_img_vmin = math.floor(np.nanmin(ri_img))
#####    #ri_img_vmax = round(np.nanmax(ri_img))
#####    ai_img_vmin = np.nanmin(ai_img_clip)
#####    ai_img_vmax = np.nanmax(ai_img_clip)
#####    ri_img_vmin = np.nanmin(ri_img_clip)
#####    ri_img_vmax = np.nanmax(ri_img_clip)
#####
#####
#####
#####    if (abs(ai_img_vmin) <= ai_img_vmax):
#####        ai_img_vmin = -ai_img_vmax
#####    else:
#####        ai_img_vmax = -ai_img_vmin
#####
#####
#####    if (abs(ri_img_vmin) <= ri_img_vmax):
#####        ri_img_vmin = -ri_img_vmax
#####    else:
#####        ri_img_vmax = -ri_img_vmin
#####
###### slicing
######    h1 = 8    #vertical positon
#####    h2 = 30    #vertical positon
######    h3 = 34    #vertical positon
#####    h1_probe_line_length = 42 
#####    h1_x1 = int((ri_img_clip.shape[1]/2) - (h1_probe_line_length/2))
#####    h1_x2 = int((ri_img_clip.shape[1]/2) + (h1_probe_line_length/2))
#####    
#####    x = np.linspace(h1_x1, h1_x2, h1_x2-h1_x1+1, endpoint=True)
######    slicing_ai_h1 = ai_img_clip[h1][h1_x1:h1_x2+1]
#####    slicing_ai_h2 = ai_img_clip[h2][h1_x1:h1_x2+1]
#####    slicing_ri_h2 = ri_img_clip[h2][h1_x1:h1_x2+1]
######    slicing_ai_h3 = ai_img_clip[h3][h1_x1:h1_x2+1]
#####
#####    
#####    plt.figure(figsize=(10,10)) # 3.5))
#####
#####    png_filename_1 = str('./pngs/4by4_' + str(i) + '.png')
#####    png_filename_2 = str('./pngs/cont_' + str(i) + '.png')
#####    mi_filename = str('./mi/' + mi_txt_list[i].stem + '.png')
#####    ai_filename = str('./ai/' + ai_txt_list[i].stem + '.png')
#####    ri_filename = str('./ri/' + ri_txt_list[i].stem + '.png')
#####
#####    mi_img_clip_filename = str('./mi/' + mi_txt_list[i].stem + '.csv')
#####    ai_img_clip_filename = str('./ai/' + ai_txt_list[i].stem + '.csv')
#####    ri_img_clip_filename = str('./ri/' + ri_txt_list[i].stem + '.csv')
#####    
#####    np.savetxt(mi_img_clip_filename,mi_img_clip,delimiter=",")
#####    np.savetxt(ai_img_clip_filename,ai_img_clip,delimiter=",")
#####    np.savetxt(ri_img_clip_filename,ri_img_clip,delimiter=",")
#####
#####    x_cut = 0
#####    y_cut = 0 
#####
#####    #cv2.imwrite(ai_filename, ai_img)
#####    #cv2.imwrite(ri_filename, ri_img)
#####
#####
#####
#####    plt.subplot(2,2,1)
#####    plt.imshow(ai_img_clip, norm=mpl.colors.Normalize(vmin=0, vmax=ai_img_vmax), cmap='viridis')  #cmap='rainbow')  #cmap='gray')
#####    plt.title('AI'), plt.colorbar()
#####
##### 
######    plt.subplot(2,2,2)
######    plt.contour(ai_img_clip)#, levels=1)
######    plt.imshow(ai_img_clip, norm=mpl.colors.Normalize(vmin=ai_img_vmin, vmax=ai_img_vmax), alpha=0.3, cmap='gray')
######    plt.title('AI contour'), plt.colorbar()
#####
#####    plt.subplot(2,2,2)
#####    plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), cmap='seismic') #cmap='rainbow') 
#####    plt.title('Ai with coeff'), plt.colorbar()
#####
#####
#####    plt.subplot(2,2,3),
#####    plt.imshow(ai_img_clip, cmap='gray') 
#####    plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), alpha=0.5, cmap='seismic')
#####    #plt.contour(ai_img_clip) 
#####    plt.title('AI coefff'), plt.colorbar()
#####    
#####    plt.subplot(2,2,4)
#####    #plt.plot(x, slicing_ai_h1, x, slicing_ai_h2, x, slicing_ai_h3)
#####    plt.plot(x, slicing_ai_h2, marker='.', label='AI')
#####    plt.plot(x, slicing_ri_h2, marker='.', label='AI with coeff')
#####    plt.legend(loc=1)
#####    
######    plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), cmap='seismic')
######    plt.title('RI'), plt.colorbar()
#####    #plt.title('Surface Kernel (p1=' + str(p1) + ', p2=' + str(p2) + ')'), plt.colorbar()
#####
#####
#####    #plt.show()
#####    plt.savefig(png_filename_1, dpi=600)
#####    plt.close()
#####
#####    #plt.figure()
#####    #plt.contour(ai_img_clip)#, levels=1) 
#####    #plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), alpha=0.5, cmap='seismic')
#####    #plt.savefig(png_filename_2, dpi=600)
#####    #plt.close()
#####
#####    #plt.figure()
#####    #plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), cmap='seismic')
#####
#####    #plt.imsave(png_filename, ri_img_clip, vmin=ri_img_vmin, vmax=ri_img_vmax, cmap='seismic')
#####    #plt.close()
#####
