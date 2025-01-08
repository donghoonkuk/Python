import os, glob, sys, subprocess
from pathlib import Path

#for loading xTal image.txt 
sys.path.append('/user/devsalt/USER/CNR/3.SQA/SCRIPTS')
import mycal

#To prevent the manipulating of ON/OFF into true/false in yaml loading
sys.path.append('/user/dw1409kang/Python/myModule/SALT/Yaml') 
from Loader import load_yaml_raw 


import pandas as pd
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import yaml
#import re
import math
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import MaxNLocator

np.seterr(divide='ignore', invalid='ignore')

pwd = os.getcwd()
root = Path(pwd)
#log_analysis = root / 'log_analysis'

result = root / 'result'					# result directory itself
#result_yaml_file = result / 'result.yaml'
#result_yaml = yaml.load(result_yaml_file.open(), Loader=yaml.FullLoader)
#result_yaml = load_yaml_raw(result_yaml_file)

#model_path = result / 'result0' / 'Model_TCC_1_0' 
#model_gauge = result / 'result0' / 'gauge.txt' 
#model_yaml_file = model_path / 'model.yaml' 
#model_yaml = yaml.load(model_yaml_file.open(), Loader=yaml.FullLoader)
#model_yaml = load_yaml_raw(model_yaml_file)


#gauge = pd.read_csv('./result/result0/gauge.txt', delim_whitespace=True)

#bumping = result_yaml['Result'][0]['Parameters']['Resist']['bumping']
#p2 = result_yaml['Result'][0]['Parameters']['Resist']['surf_pow2']


pngs =  root / 'pngs'
pngs.mkdir(exist_ok=True)

#Optical_pixel_size = model_yaml['Optics_Set'][0]['Optics']['Pixel_Size']
#Resist_pixel_size = model_yaml['Resist_Set'][0]['Resist']['Pixel_Size']
#Optical_pixel_size = 20 
#Resist_pixel_size = 10 

mi_txt_list = list((root / 'mi').glob('*.txt'))
mi_txt_list.sort()
ai_txt_list = list((root / 'ai').glob('*.txt'))
ai_txt_list.sort()
ri_txt_list = list((root / 'ri').glob('*.txt'))
ri_txt_list.sort()



for i,j in enumerate(ai_txt_list):
    #ai_img = cv2.imread(str(j), 0) #load gray scale
    #ri_img = cv2.imread(str(ri_pgm_list[i]), 0)

    # x = ai_img[0], y = ai_img[1], z = ai_img[2]
#    mi_img = mycal.readXtalImage(mi_txt_list[i])[2]
    ai_img = mycal.readXtalImage(ai_txt_list[i])[2]
#    ri_img = mycal.readXtalImage(ri_txt_list[i])[2]
    
    #save mi/ai/ri to csv

    win_x = 80 #50 #in pxl
    win_y = 80 #50 
    shift_x = 0 #2 
    shift_y = 0 
    center_x = ai_img.shape[1]/2 - shift_x
    center_y = ai_img.shape[0]/2 - shift_y

    x_1 = int(center_x - win_x/2)
    y_1 = int(center_y - win_y/2)
    x_2 = int(center_x + win_x/2)
    y_2 = int(center_y + win_y/2)

    #mi_img_clip = mi_img #Full
    #ai_img_clip = ai_img #Full
    #ri_img_clip = ri_img #Full
#    mi_img_clip = mi_img[y_1:y_2,x_1:x_2]
    ai_img_clip = ai_img[y_1:y_2,x_1:x_2]
    ri_img_clip = ri_img[y_1:y_2,x_1:x_2]

    #ri_img_vmin = math.floor(np.nanmin(ri_img))
    #ri_img_vmax = round(np.nanmax(ri_img))
    ai_img_vmin = np.nanmin(ai_img_clip)
    ai_img_vmax = np.nanmax(ai_img_clip)
    ri_img_vmin = np.nanmin(ri_img_clip)
    ri_img_vmax = np.nanmax(ri_img_clip)



    if (abs(ai_img_vmin) <= ai_img_vmax):
        ai_img_vmin = -ai_img_vmax
    else:
        ai_img_vmax = -ai_img_vmin


    if (abs(ri_img_vmin) <= ri_img_vmax):
        ri_img_vmin = -ri_img_vmax
    else:
        ri_img_vmax = -ri_img_vmin

## slicing in horizontal
##    h1 = 8    #vertical positon
#    h2 = 40    #vertical positon
##    h3 = 34    #vertical positon
#    h1_probe_line_length = 10 #42 
#    h1_x1 = int((ri_img_clip.shape[1]/2) - (h1_probe_line_length/2))
#    h1_x2 = int((ri_img_clip.shape[1]/2) + (h1_probe_line_length/2))
#    
#    x = np.linspace(h1_x1, h1_x2, h1_x2-h1_x1+1, endpoint=True)
#    x_axis_scale = np.linspace(1,ri_img_clip.shape[1],ri_img_clip.shape[1]) * Resist_pixel_size   
#
#    slicing_ai_h2 = ai_img_clip[h2][h1_x1:h1_x2+1]
#    slicing_ri_h2 = ri_img_clip[h2][h1_x1:h1_x2+1]
##    slicing_ai_h3 = ai_img_clip[h3][h1_x1:h1_x2+1]


# slicing in vertical
#    h1 = 8    #vertical positon
    v2 = 40    #vertical positon
#    h3 = 34    #vertical positon
    v1_probe_line_length = 40 #42 
    v1_y1 = int((ri_img_clip.shape[0]/2) - (v1_probe_line_length/2))
    v1_y2 = int((ri_img_clip.shape[0]/2) + (v1_probe_line_length/2))
    
    x = np.linspace(v1_y1, v1_y2, v1_y2-v1_y1+1, endpoint=True)
#    x_axis_scale = np.linspace(1,ri_img_clip.shape[0],ri_img_clip.shape[0]) * Resist_pixel_size   

    slicing_ai_v2 = ai_img_clip[v1_y1:v1_y2+1, v2]
    slicing_ri_v2 = ri_img_clip[v1_y1:v1_y2+1, v2]
#    slicing_ai_h3 = ai_img_clip[h3][h1_x1:h1_x2+1]



    
#    png_filename_1 = str('./pngs/ai_' + str(Path(j).name) + '.png')
#    png_filename_2 = str('./pngs/cont_' + str(Path(j).name) + '.png')
#    mi_filename = str('./mi/' + mi_txt_list[i].stem + '.png')

    ai_filename = str('./pngs/' + ai_txt_list[i].stem + '.png')
    ai_img_filename = str('./pngs/' + ai_txt_list[i].stem + '.csv')

    plt.imshow(ai_img_clip
    plt.savefig(ai_filename, dpi=600)
    plt.close()

    plt.savefig(png_filename_1, dpi=600)
    np.savetxt(ai_img_filename,ai_img,delimiter=",")
#    ri_filename = str('./ri/' + ri_txt_list[i].stem + '.png')

#    mi_img_clip_filename = str('./mi/' + mi_txt_list[i].stem + '.csv')
#    ri_img_clip_filename = str('./ri/' + ri_txt_list[i].stem + '.csv')
    
#    np.savetxt(mi_img_clip_filename,mi_img_clip,delimiter=",")
#    np.savetxt(ri_img_clip_filename,ri_img_clip,delimiter=",")

#    x_cut = 0
#    y_cut = 0 

    #cv2.imwrite(ai_filename, ai_img)
    #cv2.imwrite(ri_filename, ri_img)

    
#    plt.figure(figsize=(10,10)) # 3.5))
#
#    plt.subplot(2,2,1)
#    plt.imshow(ai_img_clip, norm=mpl.colors.Normalize(vmin=0, vmax=ai_img_vmax), cmap='viridis')  #cmap='rainbow')  #cmap='gray')
#    plt.title('AI'), plt.colorbar()
#    plt.set_xticks()
#    ax[0].xaxis.grid(True, which='minor')
#    xaxis.set_major_locator(MultipleLocator(20))
#    xaxis.set_major_formatter('{x:.0f}')

 
#    plt.subplot(2,2,2)
#    plt.contour(ai_img_clip)#, levels=1)
#    plt.imshow(ai_img_clip, norm=mpl.colors.Normalize(vmin=ai_img_vmin, vmax=ai_img_vmax), alpha=0.3, cmap='gray')
#    plt.title('AI contour'), plt.colorbar()

#    plt.subplot(2,2,2)
#    plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), cmap='seismic') #cmap='rainbow') 
#    plt.title('RI'), plt.colorbar()
#
#
#    plt.subplot(2,2,3),
#    plt.imshow(ai_img_clip, cmap='gray') 
#    plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), alpha=0.5, cmap='seismic')
#    #plt.contour(ai_img_clip) 
#    plt.title('RI on AI'), plt.colorbar()
#    
#    plt.subplot(2,2,4)
#    #plt.plot(x, slicing_ai_h1, x, slicing_ai_v2, x, slicing_ai_h3)
#    plt.plot(x, slicing_ai_v2, marker='.', label='AI')
#    plt.plot(x, slicing_ri_v2, marker='.', label='RI')
#    plt.legend(loc=1)
    
#    plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), cmap='seismic')
#    plt.title('RI'), plt.colorbar()
    #plt.title('Surface Kernel (p1=' + str(p1) + ', p2=' + str(p2) + ')'), plt.colorbar()


    #plt.show()
#    plt.savefig(png_filename_1, dpi=600)
#    plt.close()

    #plt.figure()
    #plt.contour(ai_img_clip)#, levels=1) 
    #plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), alpha=0.5, cmap='seismic')
    #plt.savefig(png_filename_2, dpi=600)
    #plt.close()

    #plt.figure()
    #plt.imshow(ri_img_clip, norm=mpl.colors.Normalize(vmin=ri_img_vmin, vmax=ri_img_vmax), cmap='seismic')

    #plt.imsave(png_filename, ri_img_clip, vmin=ri_img_vmin, vmax=ri_img_vmax, cmap='seismic')
    #plt.close()


