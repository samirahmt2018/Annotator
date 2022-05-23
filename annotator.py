# -*- coding: utf-8 -*-
# Advanced zoom example. Like in Google Maps.
# It zooms only a tile, but not the whole image. So the zoomed tile occupies
# constant memory and not crams it with a huge resized image for the large zooms.
#from __future__ import annotations
import random
import tkinter as tk
from tkinter import Event, Label, PhotoImage, ttk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageDraw
import json  
from functools import partial  
from pydicom.filereader import dcmread
import skimage.io as io
import matplotlib.pyplot as plt
import numpy as np
import Zoom_Advanced
import pandas as pd
import cv2
import os
import pydicom
import sys
import fnmatch
import glob
def key_func(current_frame, key_pressed,params):
    scale, x_shift, y_shift=params
    if(key_pressed=="BackSpace"):
        current_frame.canvas.delete('points')
        current_frame.canvas.delete(current_frame.current_polygon)
        #print(current_frame.current_polygon)
        current_frame.list_of_points.pop()
        list_of_points2=[]
        for pt in current_frame.list_of_points:
            x, y =  pt
            x=x*scale+x_shift
            y=y*scale+y_shift
            list_of_points2.append((x,y))
            #draw dot over position which is clicked
            x1, y1 = (x - 1), (y - 1)
            x2, y2 = (x + 1), (y + 1)
            current_frame.canvas.create_oval(x1, y1, x2, y2, fill=current_frame.label_color, outline=current_frame.label_color, width=0, tags=('points'))
        # add clicked positions to list

        numberofPoint=len(list_of_points2)
        # Draw polygon
        if numberofPoint>2:
            current_frame.current_polygon=current_frame.poly=current_frame.canvas.create_polygon(list_of_points2, fill='', outline=current_frame.label_color, width=2,tags=('polygon'))
            current_frame.canvas.coords(current_frame.poly,)

        elif numberofPoint==2 :
            print('line')
            current_frame.current_polygon=current_frame.canvas.create_line(list_of_points2, tags=('polygon'))
        else:
            print('dot')

    if(key_pressed=="Escape"):
        current_frame.canvas.delete('points')
        current_frame.canvas.delete(current_frame.current_polygon)
        current_frame.list_of_points=[]
    if(key_pressed=="Return"):
        print("Left Return was pressed")
        current_frame.canvas.delete('points')
        labeltype="BIRADS"
        if(current_frame.current_label==8):
            labeltype="Density"
        if(current_frame.current_label==9):
            labeltype="Anatomy"
        current_frame.annotations.append(({'age':current_frame.age,'width':current_frame.width,'height': current_frame.height,'label_name':current_frame.current_label_name,'label':current_frame.current_label,labeltype+'_level':current_frame.birads_level,labeltype+'_level_name':current_frame.birads_level_name,'poly':current_frame.list_of_points}))
        list_of_points2=[]
        for pt in current_frame.list_of_points:
            x, y =  pt
            x=x*scale+x_shift
            y=y*scale+y_shift
            list_of_points2.append((x,y))
        current_frame.canvas.create_polygon(list_of_points2, fill='', outline=current_frame.label_color, width=2,tags=('final_polygon'))
        current_frame.list_of_points=[]
def key(event):
        #print(app.canvas.bbox(app.container))
        #print(app2.canvas.bbox(app2.container))
        #if(app.canvas.bbox)
        print("current frame is",app.list_of_points, "Position", app.frame_position)
        
        if(len(app.list_of_points)>0):
            bbox = app.canvas.bbox(app.container)  # get image area
            bbox1 = (bbox[0] + 1, bbox[1] + 1, bbox[2] - 1, bbox[3] - 1)
            x_shift=bbox1[0]
            y_shift=bbox1[1]
            params=(app.imscale,x_shift, y_shift)
            if(event.keysym=="BackSpace"):
                key_func(app,"BackSpace", params)
            if(event.keysym=="Escape"):
                key_func(app, "Escape", params)
            if(event.keysym=="Return"):
                key_func(app, "Return", params)
        
def selecting_left():
    resetFrame(app)
    filename_l = filedialog.askopenfilename()
    app.init(path=filename_l, position="left")
    

label_color="green"
filename_l=None
filename_r=None

def dicomtopil(current_frame, dataset):
    if ('PixelData' not in dataset):
        raise TypeError("Cannot show image -- DICOM dataset does not have "
                    "pixel data")
    # can only apply LUT if these window info exists
    if ('WindowWidth' not in dataset) or ('WindowCenter' not in dataset):
        bits = dataset.BitsAllocated
        samples = dataset.SamplesPerPixel
        if samples == 1:
            mode = "L"
        elif samples == 3:
            mode = "RGB"
        
        # PIL size = (width, height)
        size = (dataset.Columns, dataset.Rows)

        # Recommended to specify all details
        # by http://www.pythonware.com/library/pil/handbook/image.htm
        im = Image.frombuffer(mode, size, int(dataset.PixelData*255/65535),
                                "raw", mode, 0, 1)
        

    else:
        ew = dataset['WindowWidth']
        ec = dataset['WindowCenter']
        ww = int(ew.value[0] if ew.VM > 1 else ew.value)
        wc = int(ec.value[0] if ec.VM > 1 else ec.value)
        image = get_LUT_value(dataset.pixel_array, ww, wc)
        # Convert mode to L since LUT has only 256 values:
        #   http://www.pythonware.com/library/pil/handbook/image.htm
        im = Image.fromarray(image).convert('L')

    return im
def get_LUT_value(data, window, level):
    """Apply the RGB Look-Up Table for the given
    data and window/level value."""
    if not have_numpy:
        raise ImportError("Numpy is not available."
                        "See http://numpy.scipy.org/"
                        "to download and install")

    return np.piecewise(data,
                        [data <= (level - 0.5 - (window - 1) / 2),
                        data > (level - 0.5 + (window - 1) / 2)],
                        [0, 255, lambda data: ((data - (level - 0.5)) /
                        (window - 1) + 0.5) * (255 - 0)])
def popup_message(msg):
    win = tk.Toplevel()
    win.wm_title("Result")

    l = tk.Label(win, text=msg)
    l.grid(row=0, column=0)

    b = ttk.Button(win, text="Okay", command=win.destroy)
    b.grid(row=1, column=0)
def savejson():
    if(len(app.annotations)>0):
        mask=np.array(np.zeros((app.annotations[0]['height'], app.annotations[0]['width'],3)),np.uint8)
        for i in range(len(app.annotations)):
            #print(list(app.annotations[i]['poly']))
            #print(app.annotations[i])
            #print(label_colors2[app.annotations[i]['label']])
            print("label:", app.annotations[i]['label'])
            if(app.annotations[i]['label']<8):
                poly=np.array(app.annotations[i]['poly'], np.int32)
                cv2.fillPoly(mask, [poly], tuple(label_colors2[app.annotations[i]['label']]))
                im2write=cv2.cvtColor(mask, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(app.path+"GT.png"),im2write)
        #print(str(app.path+"GT.png"))
            else:
                print("anatomy detected")
                poly=np.array(app.annotations[i]['poly'], np.int32)
                cv2.fillPoly(mask, [poly], tuple(label_colors2[app.annotations[i]['label']]))
                im2write=cv2.cvtColor(mask, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(app.path+"_GT_anatomy.png"),im2write)
                im2write2=cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
                _, bw_img=cv2.threshold(im2write2,2,255,cv2.THRESH_BINARY)
                cv2.imwrite(str(app.path+"_GT_anatomy_binary.png"),bw_img)
        
    with open(app.path+'.json', 'w') as f:
        json.dump(app.annotations, f, indent=4)
    popup_message("successfully saved")
    print(app.annotations)
    reset(app)
def loadjson():
    if(app.path!=None):
        print('annotation path:',app.path+'.json')
        f = open(app.path+'.json')
        
        annotations=json.load(f)
        print(annotations)
        app.annotations=annotations
        count=0;
        for annotation in annotations:
            #app.canvas.delete('points')
            #print(annotation["age"])
            #current_frame.annotations.append(({'age':current_frame.age,'width':current_frame.width,'height': current_frame.height,'label_name':current_frame.current_label_name,'label':current_frame.current_label,labeltype+'_level':current_frame.birads_level,labeltype+'_level_name':current_frame.birads_level_name,'poly':current_frame.list_of_points}))
            #break
            count+=1
            list_of_points=annotation["poly"]
            bbox = app.canvas.bbox(app.container)  # get image area
            bbox1 = (bbox[0] + 1, bbox[1] + 1, bbox[2] - 1, bbox[3] - 1)
            bbox2 = (app.canvas.canvasx(0),  # get visible area of the canvas
                    app.canvas.canvasy(0),
                    app.canvas.canvasx(app.canvas.winfo_width()),
                    app.canvas.canvasy(app.canvas.winfo_height()))
            x_shift=bbox1[0]
            y_shift=bbox1[1]
            list_of_points2=[]
            for pt in list_of_points:
                x, y =  pt
                x=x*app.imscale+x_shift
                y=y*app.imscale+y_shift
                list_of_points2.append((x,y))
            
            print(annotation,dash_types)
            if(annotation["label"]==8):
                print(annotation["label"], label_colors)
                app.canvas.create_polygon(list_of_points2, fill='', outline=label_colors[0], width=2,tags=('final_polygon'))
            elif(annotation["label"]==9):
                print(annotation["label"], label_colors)
                app.canvas.create_polygon(list_of_points2, fill='', outline=label_colors[0], width=2,tags=('final_polygon'))
                app.canvas.create_text(x, y, text=annotation["Anatomy_level_name"], fill=label_colors[annotation["label"]], font=('Helvetica 15 bold'))
            else:
                print("test1:",annotation["label"])
                try:
                    app.canvas.create_polygon(list_of_points2, fill='', outline=label_colors[annotation["label"]], width=2,tags=('final_polygon'))
                    app.canvas.create_text(x, y, text=annotation["label_name"]+": BIRADS "+str(annotation["Anatomy_level"]), fill=label_colors[annotation["label"]], font=('Helvetica 15 bold'))
                except:
                    app.canvas.create_polygon(list_of_points2, fill='', outline=label_colors[annotation["label"]], width=2,tags=('final_polygon'))
                    app.canvas.create_text(x, y, text=annotation["label_name"]+" "+str(annotation["birads_level"]), fill=label_colors[annotation["label"]], font=('Helvetica 15 bold'))
  
            app.list_of_points=[]
        print(count, "annotations were loaded")
    # returns JSON object as 
    # a dictionary
    #data = json.load(f)
def exportcsv():
    data_directory = filedialog.askdirectory(title="Select Dataset Directory")
    destination_directory = filedialog.askdirectory(title="Select Destination Directory")
    print(destination_directory,data_directory)
    ann_counter=0
    im_counter=0
    total_anns= len(fnmatch.filter(os.listdir(data_directory), '*.json'))
    df=pd.DataFrame(columns=['patient_id','Filename','ViewPosition','Laterality','size','label','label_name','BIRADS_level', 'BIRADS_level_name', 'poly', 'Density_level', 'Density_level_name'])
    df2=pd.DataFrame(columns=['patient_id','Filename','ViewPosition','Laterality','size',"Mass","Calcification", "ArchitecturalDistortion", "Asymmetry", "DuctalDialtion", "SkinTichening", "NippleRetraction", "Lymphnode","Density"])
    root_path=data_directory.split(os.sep)
    for root, dirs, files in os.walk(data_directory):
        path = root.split(os.sep)
        #print(path)
        
        for filename in files:
            #print(filename,filename.endswith(".json"),path[-1])
            #continue
            
            if filename.endswith(".json"):
                im_counter+=1
                print("processing file", im_counter, "of ", total_anns)
                try:
                    f = open(os.path.join(root, filename)) 
                    impath= os.path.join(root, filename[:-5])
                    ds = pydicom.dcmread(impath, force=True)
                    viewP="UN"
                    imL="UN"
                    try:
                        if ds.ViewPosition is not None:
                            viewP=ds.ViewPosition
                        if ds.ImageLaterality is not None:
                            imL=ds.ImageLaterality
                    except:
                        print("Unexpected error:", sys.exc_info()[0])

                    age=0
                    try:
                        age=ds.PatientAge
                    except:
                        age='-1Y'
                    annotations=json.load(f)
                    df2_loc=pd.DataFrame({'patient_id':path[-1],'age':age,'Filename':filename,'ViewPosition':viewP,'Laterality':imL,'size':[''],"Mass":0,"Calcification":0, "ArchitecturalDistortion":0, "Asymmetry":0, "DuctalDialtion":0, "SkinTichening":0, "NippleRetraction":0, "Lymphnode":0,"Density":0})       
                    #annotations=pd.read_json(os.path.join(root, filename))
                    for annotation in annotations:
                        #print(annotation)
                        #print(np.array2string(np.array(annotation['poly']), precision=2, separator=',',suppress_small=True))
                        ann_counter+=1
                        if(annotation["label"]==8):
                            df_loc=pd.DataFrame({'Laterality':[imL],"ViewPosition":[viewP],'size':[str(annotation['width'])+'X'+str(annotation['height'])],'Filename':filename,'patient_id': path[-1],'view':'UN', 'label':annotation['label'], 'label_name':annotation['label_name'], 'Density_level':annotation['Density_level'], 'Density_level_name':annotation['Density_level_name'],'poly':[np.array2string(np.asarray(annotation['poly']), precision=2, separator=',',suppress_small=True)]})
                            df2_loc["Density"]=annotation['Density_level']
                        
                        else:
                            try:
                                df_loc=pd.DataFrame({'Laterality':[imL],"ViewPosition":[viewP],'size':[str(annotation['width'])+'X'+str(annotation['height'])],'Filename':filename,'patient_id': path[-1],'view':'UN', 'label':annotation['label'], 'label_name':annotation['label_name'], 'BIRADS_level':annotation['BIRADS_level'], 'BIRADS_level_name':annotation['BIRADS_level_name'],'poly':[np.array2string(np.asarray(annotation['poly']), precision=2, separator=',',suppress_small=True)]})
                            except:
                                try:
                                    #print({'Filename':filename,'patient_id': path[-1],'view':'UN', 'label':annotation['label'], 'label_name':annotation['label_name'], 'BIRADS_level':annotation['birads_level'], 'BIRADS_level_name':annotation['birads_level_name'],'poly':[np.array2string(np.asarray(annotation['poly'],), precision=2, separator=',',suppress_small=True)]})
                                    df_loc=pd.DataFrame({'Laterality':[imL],"ViewPosition":[viewP],'size':[str(annotation['width'])+'X'+str(annotation['height'])],'Filename':filename,'patient_id': path[-1],'view':'UN', 'label':annotation['label'], 'label_name':annotation['label_name'], 'BIRADS_level':annotation['birads_level'], 'BIRADS_level_name':annotation['birads_level_name'],'poly':[np.array2string(np.asarray(annotation['poly']), precision=2, separator=',',suppress_small=True)]})
                                except Exception as e:
                                    print("error occured processing", path[-1], filename, "error",e)
                            #print(df_loc["label"][0])
                            if(df_loc["label_name"][0]=="Normal"):
                                print("Normal detected at", path[-1], "and skipped")
                            elif(df_loc["label"][0]==0):
                                df2_loc["Mass"]=df_loc["BIRADS_level"][0]
                            elif(df_loc["label"][0]==1):
                                df2_loc["Calcification"]=df_loc["BIRADS_level"][0]
                            elif(df_loc["label"][0]==2):
                                df2_loc["ArchitecturalDistortion"]=df_loc["BIRADS_level"][0]
                            elif(df_loc["label"][0]==3):
                                df2_loc["Asymmetry"]=df_loc["BIRADS_level"][0]
                            elif(df_loc["label"][0]==4):
                                df2_loc["DuctalDialtion"]=df_loc["BIRADS_level"][0]
                            elif(df_loc["label"][0]==5):
                                df2_loc["SkinTichening"]=df_loc["BIRADS_level"][0]
                            elif(df_loc["label"][0]==6):
                                df2_loc["NippleRetraction"]=df_loc["BIRADS_level"][0]
                            elif(df_loc["label"][0]==7):
                                df2_loc["Lymphnode"]=df_loc["BIRADS_level"][0]
                            
                        df2["size"]= df_loc["size"][0]    
                        df=df.append(df_loc)
                    df2=df2.append(df2_loc)
                except:
                    print("error accessing file",filename)
                
    print(df.head())
    df.to_csv(os.path.join(destination_directory, root_path[-1]+'_extracted_data.csv'))
    df2.to_csv(os.path.join(destination_directory, root_path[-1]+'_extracted_summary_data.csv'))
    popup_message("Extracted "+ str(ann_counter) + " annotations from "+ str(im_counter)+" images and successfully saved to "+os.path.join(destination_directory, 'extrated_data.csv'))
    #resetFrame(app2)


def reset(appL):
        appL.annotations=[]
       
        appL.list_of_points=[]
       
        appL.canvas.delete('points')
       
        appL.canvas.delete('polygon')
        
        appL.canvas.delete('final_polygon')
        
        appL.reset(frame)
        
def resetFrame(app):
        app.annotations=[]
        app.list_of_points=[]
        app.canvas.delete('points')
        app.canvas.delete('polygon')
        app.canvas.delete('final_polygon')
        
def donothing():
    filewin = tk.Toplevel(root)

    button = tk.Button(filewin, text="Do nothing button")
    button.pack()
def resetAll():
    reset(app)
        
def about():
    filewin = tk.Toplevel(root)                  
    widget = Label(filewin, text='Developed at Ethiopian \n Artificial Intelligence Institue \n Contact:info@aic.et', fg='#F49A21', bg='#3760A9')
    widget.pack()
    p1 = PhotoImage(file = 'aii_logo.png')
    # Setting icon of master window
    filewin.iconphoto(False, p1)
    
    
def change_label(lcolor, label,name,dash_type,birads_level,birads_name):
    app.label_color=lcolor
    

    app.dash_type=dash_type
    app.birads_level=birads_level
    app.birads_level_name=birads_name

    

    app.current_label=label
    

    app.current_label_name=name
    
    
path = 'M13.jpg'  # place path to your image here
current_label=0
label_color="green"
active_pane=0
filename_l=None
filename_r=None
labels=[0,1,2,3,4,5,6,7,8]
density_levels_names=["pre-dominantly fatty","Scattered", "Hetrogenously Dense", "Extremely Dense"]
density_levels=[1,2,3,4]
anatomy_type_names=["Lung Region", "Foreign Object", "Text","Other Body Parts"]
anatomy_types=[1,2,3,4]

birads_levels=[2,3,4,5]
label_names=["Mass","Calcification", "Architectureal Distortion", "Asymmetry", "Ductal Dialtion", "Skin Tichening", "Nipple Retraction", "Lymphnode"]
birads_level_names=["BI-RADS 2", "BI-RADS 3","BI-RADS 4", "BI-RADS 5"]
#dash_types=[(5,20),(20,20),(30,10,30),(30,5,15,10),(10,5,110,10),(10,10,10,10)]
dash_types=[(5,20),(5,20),(5,20),(5,20),(5,20),(5,20)]
label_colors=["Red","green","blue", "yellow","light blue","purple","brown","magenta","pink","purple"]
label_colors2=[(255,0,0),(0,255,0),(0,0,255),(0,255,255),(255,255,0),(204,204,255),(128,0,128),(165,42,42),(255,0,255), (128,0,128)]

root = tk.Tk()
root.title("X-ray Annotator")
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
root.bind("<Key>", key)
p1 = PhotoImage(file = 'aii_logo.png')
 
# Setting icon of master window
root.iconphoto(False, p1)
frame = tk.Frame(root,  width=w, height=h, bd=1)
frame.pack(side="left", fill="both", expand=True)
#frame.tkraise()
#frame2.tkraise()
app = Zoom_Advanced.Zoom_Advanced(frame)

menubar = tk.Menu(root)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open", command=selecting_left)
#filemenu.add_command(label="Open Right", command=lambda: selecting_file2(app2))

filemenu.add_command(label="Reset", command=resetAll)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)

menubar.add_cascade(label="File", menu=filemenu)
labelmenu = tk.Menu(menubar, tearoff=0)
label_color="green"
active_pane=0
labelmenu.add_command(label="Normal", background="gray", command=partial(change_label,"gray",0,"Normal",(15,1),1,"BI-RADS-1"))
   


anatomical_annotation=tk.Menu(menubar, tearoff=0)
for i in range(len(anatomy_types)):
    anatomical_annotation.add_command(label=anatomy_type_names[i], command=partial(change_label,label_colors[i],9,"anatomy",dash_types[i],anatomy_types[i],anatomy_type_names[i]))


menubar.add_cascade(label="Lung Anatomy", menu=anatomical_annotation)
annotationmenu=tk.Menu(menubar, tearoff=0)
annotationmenu.add_command(label="Save Annotations", command=savejson)
annotationmenu.add_command(label="Load Annotations", command=loadjson)
annotationmenu.add_command(label="Compare Annotations", command=loadjson)
annotationmenu.add_command(label="Export Annotations to CSV", command=exportcsv)
menubar.add_cascade(label="Annotation", menu=annotationmenu)

helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About...", command=about)
menubar.add_cascade(label="Help", menu=helpmenu)

root.config(menu=menubar)
#menubar.pack()
#print(app2.list_of_points)

root.mainloop()