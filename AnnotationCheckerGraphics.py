from ast import Delete
from asyncore import read
from cProfile import label
from cgitb import text
import csv
from distutils import command
from email.mime import image
from glob import glob
from tkinter.font import NORMAL
from turtle import bgcolor, right, width
from typing_extensions import IntVar
from unittest.mock import patch
import matplotlib
from matplotlib.pyplot import fill, title
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Rectangle
import matplotlib.image as mpimg

import matplotlib.animation as animation
from matplotlib.backend_bases import MouseButton
from matplotlib import style

from shapely import geometry
import cv2,pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut

from pathlib import Path

import json
import os

import numpy as np
import pandas as pd

from tkinter import TOP, PhotoImage, Variable, filedialog
import tkinter as tk
from tkinter import ttk

from PIL import ImageTk, Image

LARGE_FONT =('Verdana',12)
NORM_FONT = ('Verdana',8)
SMALL_FONT = ('Verdana',6)
style.use('ggplot')
annotation = {}
final_annotation = []
ecg_statement = {}
interval = {}
annotation_objects = []
mouse_enable = True
egecolor = ['blue','cyan','green','purple']
color_count = 0
indx="0"
filename = 'error'
class_names=["Mass","Calcification", "Architectureal Distortion", "Asymmetry", "Ductal Dialtion", "Skin Tichening", "Nipple Retraction", "Lymphnode"]
birads_level_names=["BI-RADS 2", "BI-RADS 3","BI-RADS 4", "BI-RADS 5"]
try:
    sett_file = open(".settings") 
    #f2 = open(json_path_2)
    setting_dict=json.load(sett_file)
    sett_file.close()
except:
    sett_file=open(".settings",'w')
    setting_dict={"data_directory_1": "/Volumes/MLData/Paulis_Annotation/mammo__1W","data_directory_2":"/Volumes/0973111473/Paulis_annotation2/Mammo__1Betty","joined_data":"/Users/sam/Desktop/new extraction/mammo1.csv","first_doctor":"Dr. Wubalem", "second_doctor":"Dr. Betelhem", "output_dir":""}
    json.dump(setting_dict, sett_file, indent = 6)
    sett_file.close()

data_directory_1 = setting_dict["data_directory_1"]
data_directory_2 = setting_dict["data_directory_2"]
joined_data=setting_dict["joined_data"]
first_doctor=setting_dict["first_doctor"]
second_doctor=setting_dict["second_doctor"]
output_dir=setting_dict["output_dir"]
#print(output_dir)
ann2 = pd.DataFrame()

final_annotations=[]
anns_1=[]
anns_2=[]
index=0
df_csv = pd.DataFrame(columns=["indx", "id", "patient_id","file_name","annotations", "needs_recheck"])
df_csv_ann = pd.DataFrame(columns=["indx", "id", "patient_id","file_name","class","BIRADS", "poly", "ann_by"])


class AnnotationChecker(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self,'Annotation Checker')

        #change the icon
#        photo = tk.PhotoImage(file='logo.png')
#        tk.Tk.wm_iconphoto(self,False,photo)

        #getting screen width and height of display
        width= tk.Tk.winfo_screenwidth(self)
        height= tk.Tk.winfo_screenheight(self)
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Change Settings", command=self.ChangeSettings)
        menubar.add_cascade(label="File", menu=filemenu)

        #filemenu.add_command(label="Open Right", command=lambda: selecting_file2(app2))
        self.config(menu=menubar)
        #setting tkinter window size
        tk.Tk.wm_geometry(self,"%dx%d" % (width, height))
        # print(width,height)
        self.height=height
        self.width=width
        self.container = tk.Frame(self)
        self.container.pack()
        
        self.frame1 = StartPage(self)
        self.frame1.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)

        self.frame2 = TextPage(self)
        self.frame2.pack(side=tk.RIGHT,fill=tk.BOTH,expand=False, pady=20)
    def select_csv_file(self):
        file = filedialog.askopenfilename(filetypes=(("csv files",["*.csv"]),("CSV files","*.csv")),title="Select joined Data")
        return file
    def select_directory(self,path):
        
        
        data_dir= filedialog.askdirectory(title="Select Path")
        path.set(data_dir)
        #path.config(text=data_dir)
    def select_joined_path(self,path):
        data_dir= filedialog.askopenfilename(title="Select csv",filetypes=[("CSV file",".csv")])
        path.config(text=data_dir)
    
    def save_settings(self,text_entry_1,text_entry_2,label_text1,label_text2,csv_path, output_dir_var, settingWindow):
        global data_directory_1, data_directory_2, joined_data, first_doctor,second_doctor,output_dir
        data_directory_1 = label_text1.get()
        data_directory_2 = label_text2.get()
        joined_data=csv_path.get()
        first_doctor=text_entry_1.get()
        second_doctor=text_entry_2.get()
        output_dir=output_dir_var.get()
        #print(data_directory_1,data_directory_2,joined_data,first_doctor,second_doctor)
        settingWindow.destroy()
        self.refresh()
        sett_file=open(".settings",'w')
        setting_dict={"data_directory_1":data_directory_1,"data_directory_2":data_directory_2,"joined_data":joined_data,"first_doctor":first_doctor, "second_doctor":second_doctor, "output_dir":output_dir}
        json.dump(setting_dict, sett_file, indent = 6)
        sett_file.close()

    def refresh(self):
        self.destroy()
        self.__init__()
    def ChangeSettings(self):
    # Toplevel object which will
        # be treated as a new window
        settingWindow = tk.Toplevel(self)
    
        # sets the title of the
        # Toplevel widget
        settingWindow.title("Change Settings")
    
        # sets the geometry of toplevel
        #settingWindow.geometry("400x600")
        
        label1 = ttk.Label(settingWindow,text='First Doctors Name')
        label1.grid(column=0,row=0,padx=10,sticky=tk.NW)
        label_text1 = tk.StringVar(settingWindow)
        
        text_entry_1 = ttk.Entry(settingWindow,textvariable=label_text1, background="white")
        label_text1.set(first_doctor)
        #print(f"First Doctor({first_doctor})({label_text1.get()})")
        text_entry_1.grid(column=1,row=0,padx=10,sticky=tk.NW)
       
        text_entry_1.configure(background="white")

        path_var_1=tk.StringVar()
        path_var_1.set(data_directory_1)

        path1 = ttk.Label(settingWindow,textvariable=path_var_1)
        path1.grid(column=1,row=1,padx=10,sticky=tk.NW)
        button1 = tk.Button(settingWindow,text="Change first doctor's Path",command=lambda: self.select_directory(path_var_1), width=28)
        button1.grid(column=0,row=1,padx=10,sticky=tk.NW)
        #button1.configure(background='#12ADB3')

       
       
        label2 = ttk.Label(settingWindow,text='Second Doctors Name', width=28)
        label2.grid(column=0,row=3,padx=10,sticky=tk.NW)
       

        label_text2 = tk.StringVar(settingWindow)
        label_text2.set(second_doctor)
        text_entry_2 = ttk.Entry(settingWindow,textvariable=label_text2)
        text_entry_2.grid(column=1,row=3,padx=10,sticky=tk.NW)
        text_entry_2.configure(background="white")

        path_var_2=tk.StringVar()
        path_var_2.set(data_directory_2)
        path2 = ttk.Label(settingWindow,textvariable=path_var_2)
        path2.grid(column=1,row=4,padx=10,sticky=tk.NW)
        button2 = tk.Button(settingWindow,text="Change Second doctor's Path",command=lambda: self.select_directory(path_var_2),width=28)
        button2.grid(column=0,row=4,padx=10,sticky=tk.NW)

        #joinde csv path
        csv_path_var=tk.StringVar()
        csv_path_var.set(joined_data)
        csv_path = ttk.Label(settingWindow,textvariable=csv_path_var, width=40, background="white")
        csv_path.grid(column=1,row=5,padx=10,sticky=tk.NW)
        button_csv = tk.Button(settingWindow,text="Change joined CSV path",command=lambda: self.select_joined_path(csv_path_var), width=28)
        button_csv.grid(column=0,row=5,padx=10,sticky=tk.NW)

#output dir
        output_dir_var=tk.StringVar()
        output_dir_var.set(output_dir)
        path3 = ttk.Label(settingWindow,textvariable=output_dir_var)
        path3.grid(column=1,row=6,padx=10,sticky=tk.NW)
        button3 = tk.Button(settingWindow,text="Change Output Folder",command=lambda: self.select_directory(output_dir_var),width=28)
        button3.grid(column=0,row=6,padx=10,sticky=tk.NW)


        #button2.configure(background='#12ADB3')
        button4 = tk.Button(settingWindow,text="Save Changes",command=lambda: self.save_settings(label_text1,label_text2,path_var_1,path_var_2,csv_path_var, output_dir_var, settingWindow), width=28)
        button4.grid(column=1,row=7,padx=10,sticky=tk.NE)
        
    def show_frame(self,cont):
        frame = self.frames[cont]
        frame.tkraise()
    def reload_frame2(self):
        self.frame2.destroy()
        self.frame2 = TextPage(self)
        self.frame2.pack(side=tk.RIGHT,fill=tk.BOTH,expand=False, pady=20)

    def reload_frame1(self):
        global index
        #print("global index",index)
        self.frame1.destroy()
        self.frame1 = StartPage(self)
        self.frame1.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        self.frame1.next_figure(self)

class TextPage(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        
        frame = tk.Frame(self)

        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        global anns_2,anns_1, first_doctor, second_doctor
        
        self.first_selected = []
        self.second_selected = []
        row_count=0
        label_first_doctor = ttk.Label(scrollable_frame,text=f'Select from {first_doctor} Annotation',font=LARGE_FONT)
        label_first_doctor.grid(column=0,row=row_count,padx=10,sticky=tk.NW)
        var1=tk.IntVar()
        var1.set(0)
        selectButton = tk.Checkbutton(scrollable_frame, text="All", command=self.select_all_first, variable=var1)
        selectButton.grid(column=1,row=row_count,padx=1,sticky=tk.NW)

        #print("first label @",row_count)
        for i,anns in enumerate(anns_1):

            #print(anns)
           
            #print("("+anns[3]+")"+anns[6]+" "+anns[5])
            if anns[0]<8:
               
                var = tk.IntVar()
                self.first_selected.append([i,var])
                row_count+=1
                ttk.Checkbutton(scrollable_frame, text="("+str(anns[3])+")"+anns[4]+" "+anns[5],variable=var).grid(column=0,row=row_count,sticky=tk.NSEW)
                #print("check box added at", row_count,"("+str(anns[3])+")"+anns[4]+" "+anns[5])
                
        
        row_count+=1
        label_second_doctor = ttk.Label(scrollable_frame,text=f'Select from {second_doctor} Annotation',font=LARGE_FONT)
        label_second_doctor.grid(column=0,row=row_count,padx=10,sticky=tk.NW)
        var2=tk.IntVar()
        var2.set(0)
        selectButton = tk.Checkbutton(scrollable_frame, text="All", command=self.select_all_second, variable=var2)
        selectButton.grid(column=1,row=row_count,padx=1,sticky=tk.NW)

        #print("second label @",row_count)
        for i,anns in enumerate(anns_2):
            
            #print("("+anns[3]+")"+anns[6]+" "+anns[5])
            if anns[0]<8:
                row_count+=1
                var = tk.IntVar()
                self.second_selected.append([i,var])
                ttk.Checkbutton(scrollable_frame, text="("+str(anns[3])+")"+anns[4]+" "+anns[5],variable=var).grid(column=0,row=row_count,sticky=tk.NSEW)
                
     
        row_count+=2
        
        
        self.needs_checking=tk.IntVar()
        ttk.Checkbutton(scrollable_frame, text="Needs Checking",variable=self.needs_checking).grid(column=0,row=row_count,sticky=tk.NSEW)
             
        row_count+=1
        button4 = ttk.Button(scrollable_frame, text='Save',command=lambda: self.save_annotation(parent))
        button4.grid(column=0,row=row_count,pady=5,padx=10,sticky=tk.NW)

        frame.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True, pady=20)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def select_all_first(self): # Corrected
        for item in self.first_selected:
            n,v = item
            if v.get():
                v.set(0)
            else:
                v.set(1)
        
    def select_all_second(self): # Corrected
        for item in self.second_selected:
            n,v = item
            if v.get():
                v.set(0)
            else:
                v.set(1)
    def save_annotation(self,parent):
        #print(self.first_selected, self.second_selected, self.needs_checking.get())
        ##print(selected_ann_from_1,selected_ann_from_2)
        #needs_recheck=input("does these annotation need a checkup")
        global indx, index,folder_name,index
        curr_ann=[]
        df_csv_ann=pd.DataFrame(columns=["indx", "id", "patient_id","file_name","class","BIRADS", "poly", "ann_by"])
        df_csv = pd.DataFrame(columns=["indx", "id", "patient_id","file_name","annotations", "needs_recheck"])

        #print(anns_1,anns_1[0][2])
        if len(anns_1)>0:     
            for c in self.first_selected:
                if(c[1].get()>0):
                    curr_ann.append({"class":anns_1[c[0]][0],"BIRADS":anns_1[c[0]][1], "poly":anns_1[c[0]][2].tolist(),"ann_by":first_doctor})
                    df_csv_ann=df_csv_ann.append([{"indx":indx,"id":index,"patient_id":folder_name,"file_name":file_name,"class":anns_1[c[0]][0],"BIRADS":anns_1[c[0]][1], "poly":anns_1[c[0]][2].tolist(),"ann_by":first_doctor}], ignore_index=True)
        #print(curr_ann, df_csv_ann)
        if len(anns_2)>0:     
            for c in self.second_selected:
                if(c[1].get()>0):
                    curr_ann.append({"class":anns_2[c[0]][0],"BIRADS":anns_2[c[0]][1], "poly":anns_2[c[0]][2].tolist(),"ann_by":second_doctor})
                    df_csv_ann=df_csv_ann.append([{"indx":indx,"id":index,"patient_id":folder_name,"file_name":file_name,"class":anns_2[c[0]][0],"BIRADS":anns_2[c[0]][1], "poly":anns_2[c[0]][2].tolist(),"ann_by":second_doctor}], ignore_index=True)
        #print(curr_ann)
        #if len(anns_2)>0:   
            #for i in selected_ann_from_2:
            #    if(i>-1):
            #        curr_ann.append({"class":anns_2[i][0],"BIRADS":anns_2[i][1], "poly":anns_2[i][2].tolist(), "ann_by":second_doctor})
            #        df_csv_ann=df_csv_ann.append([{"indx":indx,"id":index,"patient_id":folder_name,"file_name":file_name,"class":anns_2[i][0],"BIRADS":anns_2[i][1], "poly":anns_2[i][2].tolist(), "ann_by":second_doctor}],ignore_index=True)
        final_annotation={indx:{"id": index,"patient_id":folder_name,"file_name":file_name,"annotations":curr_ann, "needs_recheck":self.needs_checking.get()}}
        df_csv=df_csv.append([{"indx":indx,"id":index,"patient_id":folder_name,"file_name":file_name,"annotations":curr_ann, "needs_recheck":self.needs_checking.get()}], ignore_index=True)
        if(index==0):
            df_csv.to_csv(os.path.join(output_dir,"checked_data.csv"), mode="w", index=False, header=True)
            df_csv_ann.to_csv(os.path.join(output_dir,"checked_data_each_ann.csv"), mode="w", index=False, header=True)
            out_file = open(os.path.join(output_dir,"checked_data.json"), "w")
            
            json.dump(final_annotation, out_file, indent = 6)
            out_file.close()
        else:
            df_csv.to_csv(os.path.join(output_dir,"checked_data.csv"), mode="a", index=False, header=False)
            df_csv_ann.to_csv(os.path.join(output_dir,"checked_data_each_ann.csv"), mode="a", index=False, header=False)
            self.write_json(os.path.join(output_dir,final_annotation), filename="checked_data.json")
        index+=1
        ##StartPage.load_annotation(index)
        AnnotationChecker.reload_frame1(parent)
   

    def donothing(self):
        return 0   
   
    
    def write_json(self,new_data, filename='data.json'):
        with open(filename) as f:
            data = json.load(f)

        data.update(new_data)

        with open(filename, 'w') as f:
            json.dump(data, f)
            
            #StartPage.load_annotation(index)
    
class StartPage(tk.Frame):

    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        frame1 = tk.Frame(self)#,background='#12ADB3')
        frame1.pack(side=tk.TOP,fill=tk.X)
        global joined_data, ann2, first_doctor,second_doctor
        
        ann2=pd.read_csv(joined_data)
        label1 = ttk.Label(frame1,text='Starting Index')
        label1.pack(side=tk.LEFT)
       
        
       
        self.label_text = tk.StringVar(frame1)
        self.label_text.set(index)

        label3 = ttk.Entry(frame1,textvariable=self.label_text)
        label3.pack(side=tk.LEFT, padx=5)
        # label2 = ttk.Label(frame1,text='Selected Annotation: '+joined_data)
        # label2.pack(side=tk.LEFT)
        button0 = tk.Button(frame1,text='Load',command=lambda: self.next_figure(parent))
        button0.pack(side=tk.LEFT,padx=10)
        button0.configure(background='#12ADB3')
        #button1 = tk.Button(frame1,text='Change',command=lambda: self.load_file(parent))
        # button1.pack(side=tk.LEFT,padx=10)
        # button1.configure(background='#12ADB3')
        
        width= tk.Tk.winfo_screenwidth(self)
        height= tk.Tk.winfo_screenheight(self)
               
        self.fig = Figure(figsize=(int(width*0.015),int(height*0.10)))
        self.fig.subplots_adjust(hspace=0.1, wspace=0.1,left=0.025,right=0.995,bottom=0.05,top=0.95)

        self.axes = []
        self.axes.append(self.fig.add_subplot(1,2,1)) 
        self.axes.append(self.fig.add_subplot(1,2,2)) 
        self.axes[0].grid(False)#visible=True,color="tab:orange")
        self.axes[1].grid(False)#visible=True,color="tab:orange")
        self.axes[0].title.set_text(first_doctor+" Annotation")
        self.axes[1].title.set_text(second_doctor+" Annotation")
        # self.fig.subplots_adjust(hspace=0.015, wspace=0,left=0.025,right=1,bottom=0.02,top=0.995)

        global g_fig,g_canvas
        g_fig = self.fig

        self.canvas = FigureCanvasTkAgg(self.fig,self)
        g_canvas = self.canvas

        NavigationToolbar2Tk.toolitems = [t for t in NavigationToolbar2Tk.toolitems if t[0] not in ('Save','Subplots')]

        self.toolbar = NavigationToolbar2Tk(self.canvas,self)
        self.toolbar.update()

        # b = ttk.Button(self.toolbar,text='next',command=self.next_figure)
        # b.pack(side=tk.LEFT)
 
        self.canvas.get_tk_widget().pack(fill=tk.BOTH,expand=True)
        self.canvas._tkcanvas.pack()
    
    def next_figure(self, parent):
        
        global color_count,ann2,index,joined_data
        index=int(self.label_text.get())
        if(index==0):
            confirmation = tk.messagebox.askquestion('confirm','Are you sure to delete existing data?')
            if confirmation!="yes":
                return "Error"
        
        ann2=pd.read_csv(joined_data)
        im1,im2,ann1,ann2=self.load_annotation(index)
        self.axes[0].imshow(im1)
        self.axes[1].imshow(im2)

        self.canvas.draw()
        AnnotationChecker.reload_frame2(parent)
        annotation.clear()
    def load_next_figure(self, parent):
        
        global color_count,ann2,index,joined_data
        if(index==0):
            confirmation = tk.messagebox.askquestion('confirm','Are you sure to delete existing data?')
            if confirmation!="yes":
                return "Error"
        
        ann2=pd.read_csv(joined_data)
        im1,im2,ann1,ann2=self.load_annotation(index)
        self.axes[0].imshow(im1)
        self.axes[1].imshow(im2)

        self.canvas.draw()
       
        AnnotationChecker.reload_frame2(parent)
        annotation.clear()

    def load_file(self,parent):
        file = filedialog.askopenfilename(filetypes=(("csv files",["*.csv"]),("CSV files","*.csv")))
        #print(file, self.label_text.get())
        
        
        global color_count,ann2,index,joined_data
        joined_data=file
        index=int(self.label_text.get())
        if(index==0):
            confirmation = tk.messagebox.askquestion('confirm','Are you sure to delete existing data?')
            if confirmation!="yes":
                return "Error"
        
        ann2=pd.read_csv(file)
        im1,im2,ann1,ann2=self.load_annotation(index)
        self.axes[0].imshow(im1)
        self.axes[1].imshow(im2)
        
        self.canvas.draw()
        AnnotationChecker.reload_frame2(parent)
        annotation.clear()
    def load_annotation(self, id):
        global ann2, anns_1,anns_2, indx,file_name, folder_name, index
        index=id
        row=ann2.iloc[id]
        indx=row['indx']
        folder_name=indx.split("-")[0]
        file_name=indx.split("-")[1]+"-"+indx.split("-")[2]+"-"+indx.split("-")[3][:-5]
        #print(folder_name,file_name)
        is_normal_1=is_normal_2=False
        density_level_1=density_level_2=-1
        #print("Got Here:!")
        try: 
            impath= os.path.join(data_directory_1, folder_name,file_name)
            #im_save_path=os.path.join(destination_directory,str(im_counter)+"_"+filename[:-4]+".png")
            #print(impath)
            
            json_path_1=os.path.join(data_directory_1,folder_name,file_name+".json")
            json_path_2=os.path.join(data_directory_2,folder_name,file_name+".json")
            
            
        
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
            #print("annotation by ",first_doctor)
            anns_1=self.extract_annotation(json_path_1)
            #print("annotation by ",second_doctor)
            anns_2=self.extract_annotation(json_path_2)
            
            im_1=img.copy()
            im_2=img.copy()
            
            #print("processing file", index, "of ", len(ann2.index))
            if len(anns_1)>0:          
                im_1=self.plot_image(im_1, anns_1,class_names)
            if len(anns_2)>0:
                im_2=self.plot_image(im_2, anns_2,class_names)
            return im_1, im_2, anns_1, anns_2
        except Exception as e:
            print("General error Occured at the end",e)
            return [0,0,0,0];   
    def plot_image(self,image, anns,class_labels):
        """Plots predicted bounding boxes on the image"""
        # Create a Rectangle patch
        
        colors = [(235, 47, 26), (235, 158, 26), (207, 235, 26), (26, 235, 64),  (26, 221, 235), (71, 26, 235), (158, 26, 235), (235, 26, 151)]
        for ann in anns:
            #print("inside fun",len(ann),ann)
            assert len(ann) == 6, "box should contain  class_indx,score,poly,indx,classname,biradsname"
            class_pred = ann[0]
            if(class_pred<8):
            #box = box[2:]
                poly_coords=ann[2]
                cv2.drawContours(image,[poly_coords], 0,colors[int(class_pred)],3)
                #print(name, "anns",class_labels[int(class_pred)], poly_coords[0])
                #bbox = cv2.boundingRect(poly_coords)
                #print(x_c,y_c,x_min,y_min,w,h)
                poly = geometry.Polygon([[p[0], p[1]] for p in poly_coords])
                centroid=poly.representative_point()
                # Add the patch to the Axes
                #image.add_patch(poly)
                #print(centroid.x,centroid.y)
                
                
                cv2.putText(img=image, text=str(ann[3]), org=(int(centroid.x),int(centroid.y)), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=2, color=colors[int(class_pred)],thickness=2)

                
        
        return image

        ###
        #plt.savefig('pltsave.png')
    def extract_annotation(self,json_path):
        anns=[] 
        
        try:
            f1 = open(json_path) 
            #f2 = open(json_path_2)
            annotations=json.load(f1)
            indx_counter=-1
            for annotation in annotations:
                #print(annotation)
                indx_counter+=1
                if(annotation["label"]!=8 and annotation["label_name"]!="Normal"):
                    try:
                        polys = np.asarray(annotation['poly'])
                        anns.append([int(annotation["label"]),annotation["BIRADS_level"],polys, indx_counter,annotation["label_name"],annotation["BIRADS_level_name"]])
                        #print(indx_counter,"label:",annotation["label_name"],"Level:",annotation["BIRADS_level_name"])
                    except Exception as e:
                        print("error occured processing",json_path)
                    #print(df_loc["label"][0])
                if(annotation["label"]==8):
                    anns.append([8,annotation["Density_level"],[], indx_counter, annotation["label_name"],annotation["Density_level_name"]])
                if (annotation["label_name"]=="Normal"):
                    anns.append([9,0,[], indx_counter, "Normal", "Birads-1"])

            f1.close()
            
            if len(anns)==0:  
                print(f"No annotation by {first_doctor}")
                
            return anns
            
            
        except BaseException as err:
                print(f"Unexpected {err=}, {type(err)=}",json_path)
                return anns
    ##declare annotation files

app = AnnotationChecker()
app.mainloop()
