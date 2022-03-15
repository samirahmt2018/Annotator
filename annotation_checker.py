import fnmatch
from cv2 import equalizeHist
import pandas as pd
import os
import pydicom
import json
import cv2 
import numpy as np
from pydicom.pixel_data_handlers.util import apply_voi_lut
from PIL import Image
import fnmatch
import glob
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import matplotlib.patches as mpatches
import numpy as np

def plot_image(image, boxes_1,boxes_2,class_labels,name_1,name_2,is_normal_1,is_normal_2, density_level_1,density_level_2):
    """Plots predicted bounding boxes on the image"""
    cmap = plt.get_cmap("tab20b")
    colors = [cmap(i) for i in np.linspace(0, 1, len(class_labels)+1)]
    im = np.array(image)
    #print(im.shape)
    height, width,_= im.shape

    # Create figure and axes
    fig, ax = plt.subplots(1,2)
    fig.set_size_inches(14.5, 7, forward=True)

    # Display the image
    ax[0].imshow(im)

    # box[0] is x midpoint, box[2] is width
    # box[1] is y midpoint, box[3] is height
    # Create a Rectangle patch
    my_handles=[]
    present_classes=[]
    for box in boxes_1:
        print("inside fun",len(box),box)
        assert len(box) == 6, "box should contain  class_indx,score,x_c, y_c, w_c, h_c class"
        class_pred = box[0]
        #box = box[2:]
        x_min,y_min,w,h=box[2:6]
        
        #print(x_c,y_c,x_min,y_min,w,h)
        rect = patches.Rectangle(
            (x_min,y_min),
            w,
            h,
            linewidth=1,
            edgecolor=colors[int(class_pred)],
            facecolor="none",
        )
        # Add the patch to the Axes
        ax[0].add_patch(rect)
        
        
        plt.text(
            5*int(class_pred),
            0,
            s=class_labels[int(class_pred)],
            color="white",
            verticalalignment="top",
            bbox={"color": colors[int(class_pred)], "pad": 0},
            animated=True
        )
        if class_pred not in present_classes:
            my_handles.append(mpatches.Patch(color=colors[int(class_pred)], label=class_labels[int(class_pred)]+", BIRADS - "+str(box[1])))
            present_classes.append(class_pred)
    if(density_level_2!= -1):
        my_handles.append(mpatches.Patch(color=colors[len(class_labels)], label="Density Level - "+str(density_level_1)))
    ax[0].legend(handles=my_handles, loc=(1.04,0))
    # Create figure and axes for doctor2
    title_1="Annotation by: "+name_1 + ("Annotated Normal" if  is_normal_2 else "")
    ax[0].set_title(title_1)
    ax[0].set_xticks([])
    ax[0].set_yticks([])

    ###
    ax[1].imshow(im)

    # box[0] is x midpoint, box[2] is width
    # box[1] is y midpoint, box[3] is height
    # Create a Rectangle patch
    my_handles_2=[]
    present_classes_2=[]
    for box in boxes_2:
        print("inside fun",len(box),box)
        assert len(box) == 6, "box should contain  class_indx,score,x_c, y_c, w_c, h_c class"
        class_pred = box[0]
        #box = box[2:]
        x_min,y_min,w,h=box[2:6]
        
        #print(x_c,y_c,x_min,y_min,w,h)
        rect = patches.Rectangle(
            (x_min,y_min),
            w,
            h,
            linewidth=1,
            edgecolor=colors[int(class_pred)],
            facecolor="none",
        )
        # Add the patch to the Axes
        ax[1].add_patch(rect)
        
        
        plt.text(
            5*int(class_pred),
            0,
            s=class_labels[int(class_pred)],
            color="white",
            verticalalignment="top",
            bbox={"color": colors[int(class_pred)], "pad": 0},
            animated=True
        )
        if class_pred not in present_classes_2:
            my_handles_2.append(mpatches.Patch(color=colors[int(class_pred)], label=class_labels[int(class_pred)]+", BIRADS - "+str(box[1])))
            present_classes_2.append(class_pred)
    if(density_level_2!= -1):
        my_handles_2.append(mpatches.Patch(color=colors[len(class_labels)], label="Density Level - "+str(density_level_2)))
    ax[1].legend(handles=my_handles_2, loc=(1.04,0))
    title_2="Annotation by: "+name_2 + ("Annotated Normal" if  is_normal_2 else "")
    print(title_2)
    ax[1].set_title(title_2)
    ax[1].set_xticks([])
    ax[1].set_yticks([])
    #plt.show()
    plt.savefig('pltsave.png')

##declare annotation files

class_names=["Mass","Calcification", "Architectureal Distortion", "Asymmetry", "Ductal Dialtion", "Skin Tichening", "Nipple Retraction", "Lymphnode"]
birads_level_names=["BI-RADS 2", "BI-RADS 3","BI-RADS 4", "BI-RADS 5"]
data_directory_1 = "/Volumes/MLData/Paulis_Annotation/mammo__2Mulu"
data_directory_2 = "/Volumes/0973111473/Paulis_annotation2/2_mammo__2"
no_files_1=len(glob.glob1(data_directory_1,"*.dcm"))
no_files_2= len(glob.glob1(data_directory_2,"*.dcm"))
if no_files_1 != no_files_2:
    print("!!! Warning: The no of files are not equal!!")
data_directory=data_directory_1
if(no_files_2>no_files_1):
    data_directory=data_directory_2
no_annotations_1=len(glob.glob1(data_directory_1,"*.json"))
no_annotations_2= len(glob.glob1(data_directory_2,"*.json"))
first_doctor="Dr. Mulu"
second_doctor="Dr. Wubalem"
print(f"No of annotations: \n\t1: ({no_annotations_1}) \n\t 2:({no_annotations_2}) ")

total_anns = max(no_annotations_1,no_annotations_2)
ann_counter=0
im_counter=0


yolo_annot=""
text_file = open("pauli_annotations.txt", "w")
#n = text_file.write('Welcome to pythonexamples.org')
test=0

for root, dirs, files in os.walk(data_directory_1):
    path = root.split(os.sep)
    #print(path)
    print(root)
   
    for filename in files:
        #print(filename,filename.endswith(".json"),path[-1])
        #continue
        
        if filename.endswith(".dcm"):
            is_normal_1=is_normal_2=False
            density_level_1=density_level_2=-1
            try: 
                print("processing file", im_counter, "of ", total_anns)
                impath= os.path.join(root, filename)
                #im_save_path=os.path.join(destination_directory,str(im_counter)+"_"+filename[:-4]+".png")
                #print(impath)
                final_folder=path[-1]
                json_path_1=os.path.join(data_directory_1,final_folder,filename+".json")
                json_path_2=os.path.join(data_directory_2,final_folder,filename+".json")
               

                ds = pydicom.dcmread(impath, force=True)
                img= ds.pixel_array.astype(float)
                
                if 'WindowWidth' in ds:
                    #print('Dataset has windowing')
                    windowed  = apply_voi_lut(ds.pixel_array, ds)
                    #plt.imshow(windowed, cmap="gray", vmax=windowed.max(), vmin=windowed.min)
                    #plt.show()
                    img=windowed.astype(float)
                    #return "windowed"
                # Convert to uint
                img = (np.maximum(img,0) / img.max()) * 255.0
                img= np.uint8(img)
                img = cv2.merge([img,img,img])
                #img = cv2.COLOR_GRAY2RGB()
                #(ori_h,ori_w)=img.shape
                boxes_1=[]
                
                boxes_2=[]
                try:
                    f1 = open(json_path_1) 
                    #f2 = open(json_path_2)
                    annotations=json.load(f1)
                    
                    for annotation in annotations:
                        #print(annotation)
                        #print(np.array2string(np.array(annotation['poly']), precision=2, separator=',',suppress_small=True))
                        ori_w=annotation["width"]
                        ori_h=annotation["height"]
                        
                        ann_counter+=1
                        #print(annotation["label"],annotation["label_name"])
                        
                        if(annotation["label"]!=8 and annotation["label_name"]!="Normal"):
                            try:
                                print(annotation['poly'])
                                #current_label=annotation["label"] if annotation["label"]<3 else (annotation["label"]-1)
                                
                                x,y,w,h = cv2.boundingRect(np.asarray(annotation['poly']))
                                boxes_1.append([int(annotation["label"]),annotation["BIRADS_level"],x,y,w,h])
                                print("got here",boxes_1)
                            except Exception as e:
                                print("error occured processing", path[-1], filename, "error",e)
                            #print(df_loc["label"][0])
                        if(annotation["label"]==8):
                            density_level_1=annotation["Density_level"]
                        if (annotation["label_name"]=="Normal"):
                            is_normal_1=False

                    f1.close()
                   
                    if len(boxes_1)>0:  
                        #plt.show()
                        print("annotations plotted")
                        test=1
                    else: 
                        print(f"No annotation by {first_doctor}")
                    
                except BaseException as err:
                        print(f"Unexpected {err=}, {type(err)=}")
                        raise
                try:
                    f2 = open(json_path_2)
                    annotations=json.load(f2)
                    
                    for annotation in annotations:
                        #print(annotation)
                        #print(np.array2string(np.array(annotation['poly']), precision=2, separator=',',suppress_small=True))
                        ori_w=annotation["width"]
                        ori_h=annotation["height"]
                        
                        ann_counter+=1
                        #print(annotation["label"],annotation["label_name"])
                        if(annotation["label"]!=8 and annotation["label_name"]!="Normal" and annotation["label"]!=3):
                            try:
                                print(annotation['poly'])
                                #current_label=annotation["label"] if annotation["label"]<3 else (annotation["label"]-1) 
                                x,y,w,h = cv2.boundingRect(np.asarray(annotation['poly']))
                                boxes_2.append([int(annotation["label"]),annotation["BIRADS_level"],x,y,w,h])
                                #print("got here",boxes_1)
                            except Exception as e:
                                print("error occured processing", path[-1], filename, "error",e)
                            #print(df_loc["label"][0])
                        if(annotation["label"]==8):
                            density_level_2=annotation["Density_level"]
                        if (annotation["label_name"]=="Normal"):
                            is_normal_2=False

                    f2.close()
                    #plot_image(img, boxes_2,class_names,second_doctor)
                    if len(boxes_2)>0:  
                        #plt.show()
                        print("annotations plotted")
                        
                    else: 
                        print(f"No annotation by {second_doctor}")
                    
                except BaseException as err:
                        print(f"Unexpected {err=}, {type(err)=}")
                        raise
                plot_image(img, boxes_1,boxes_2,class_names,first_doctor, second_doctor,is_normal_1,is_normal_2,density_level_1,density_level_2)
                input("Press Enter to continue...")
            except Exception as e:
                print("General error Occured at the end",e)      
        
text_file.close()        