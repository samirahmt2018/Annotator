from ast import Delete
from asyncore import read
from cProfile import label
from cgitb import text
import csv
from distutils import command
from email.mime import image
from tkinter.font import NORMAL
from turtle import bgcolor, right, width
from typing_extensions import IntVar
from unittest.mock import patch
import matplotlib
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
filename = 'error'
class_names=["Mass","Calcification", "Architectureal Distortion", "Asymmetry", "Ductal Dialtion", "Skin Tichening", "Nipple Retraction", "Lymphnode"]
birads_level_names=["BI-RADS 2", "BI-RADS 3","BI-RADS 4", "BI-RADS 5"]
data_directory_1 = "/Volumes/MLData/Paulis_Annotation/mammo__1W"
data_directory_2 = "/Volumes/0973111473/Paulis_annotation2/Mammo__1Betty"
joined_data="/Users/sam/Desktop/new extraction/mammo1.csv"
ann2 = pd.DataFrame()
first_doctor="Wube"
second_doctor="Betty"
final_annotations=[]
anns_1=[]
anns_2=[]
start_index=0
df_csv = pd.DataFrame(columns=["indx", "id", "patient_id","file_name","annotations", "needs_recheck"])
df_csv_ann = pd.DataFrame(columns=["indx", "id", "patient_id","file_name","class","BIRADS", "poly", "ann_by"])


class AnnotationChecker(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self,'ECG Annotation Platform')

        #change the icon
#        photo = tk.PhotoImage(file='logo.png')
#        tk.Tk.wm_iconphoto(self,False,photo)

        #getting screen width and height of display
        width= tk.Tk.winfo_screenwidth(self)
        height= tk.Tk.winfo_screenheight(self)

        #setting tkinter window size
        tk.Tk.wm_geometry(self,"%dx%d" % (width, height))
        # print(width,height)
        
        container = tk.Frame(self)
        container.pack()

        frame1 = StartPage(self,container)
        frame1.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)

        frame2 = TextPage(self,container)
        frame2.pack(side=tk.RIGHT,expand=False)
        
    def show_frame(self,cont):
        frame = self.frames[cont]
        frame.tkraise()

class TextPage(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        
        frame = tk.Frame(self)
        frame.grid(row=0,columnspan=2,sticky=tk.NW,padx=10)
        global anns_2,anns_1, first_doctor, second_doctor
        
        self.first_selected = []
        self.second_selected = []
        row_count=1
        label_first_doctor = ttk.Label(self,text=f'Select from Dr.{first_doctor} Annotation',font=LARGE_FONT)
        label_first_doctor.grid(column=0,row=0,padx=10,sticky=tk.NW)
        for anns in anns_1:
            var = tk.IntVar()
            self.first_selected.append(var)
            
            ttk.Checkbutton(frame, text=anns,variable=var).grid(column=0,row=row_count,sticky=tk.NSEW)
            row_count+=1

        label_second_doctor = ttk.Label(self,text=f'Select from Dr.{second_doctor} Annotation',font=LARGE_FONT)
        label_second_doctor.grid(column=row_count,row=0,padx=10,sticky=tk.NW)
        row_count+=1
        for anns in anns_2:
            var = tk.IntVar()
            self.second_selected.append(var)
            
            ttk.Checkbutton(frame, text=anns,variable=var).grid(column=0,row=row_count,sticky=tk.NSEW)
            row_count+=1
     
     
        label2 = ttk.Label(self,text='Description',font=LARGE_FONT)
        label2.grid(column=0,row=3,columnspan=2,padx=10,sticky=tk.NW)
    
        self.text3 = tk.Text(self, height=5, width=30)
        self.text3.tag_configure('bold_italics', font=NORM_FONT)
        self.text3.tag_configure('big', font=NORM_FONT)
        self.text3.tag_configure('color', foreground='#476042', font=NORM_FONT)
        self.text3.tag_bind('follow', '<1>', lambda e, t=self.text3: t.insert(tk.END, "Not now, maybe later!"))
        self.text3.grid(column=0,row=4,columnspan=2,padx=10,sticky=tk.NW)
        
        self.label_text = tk.StringVar()
        self.label_text.set('')
        
        self.label3 = ttk.Label(self,textvariable=self.label_text,font=SMALL_FONT,width=30)
        self.label3.grid(column=0,row=5,columnspan=2,sticky=tk.NW,padx=10)
        
        button2 = ttk.Button(self,text='+Add',command=self.donothing)
        button2.grid(column=0,row=6,padx=10,pady=5,sticky=tk.NW)

        button3 = ttk.Button(self,text='clear',command=self.donothing)
        button3.grid(column=1,row=6,pady=5,padx=10,sticky=tk.NW)

        label4 = ttk.Label(self,text='Diagnosis',font=LARGE_FONT)
        label4.grid(column=0,row=7,columnspan=2,padx=10,sticky=tk.NW)
        
        diagnosis = [
            'Anterior Myocardial Infarction',
            'Atrial Fibrillation',
            'Atrial Flutter',
            'First Degree AV Block',
            'Inferior Myocardial Infarction',
            'Lateral Myocardial Infarction',
            'Left Bundle Branch Block',
            'Left Ventricular High Voltage',
            'Left Ventricular Hypertrophy',
            'Normal Diagnosis',
            'Posterior Myocardial Infarction',
            'Premature Atrial Beats',
            'Premature Ventricular Complex',
            'Previous Myocardial Infraction',
            'Right Atrial Enlargement',
            'Right Bundle Branch Block',
            'Right Ventricular Hypertrophy',
            'Second-degree Antrioventricular Block',
            'Septal Hypertrophy',
            'Sinus Bradycardia',
            'Sinus Rhythm',
            'Sinus Tachycardia',
            'ST Segment Depression',
            'ST Segment Elevation',
            'Supra Ventricular Tachycardia',
            'T-wave Abnormalities',
            'Wolf-parkinson-white syndrome',
            'Other Myocardial Infarction',
            'Other Diagnosis']

        self.diag_variable = tk.StringVar(self)
        self.diag_variable.set(diagnosis[0]) # default value

        self.text4 = tk.Text(self, height=4, width=30)
        self.text4.tag_configure('bold_italics', font=NORM_FONT)
        self.text4.tag_configure('big', font=NORM_FONT)
        self.text4.tag_configure('color', foreground='#476042', font=NORM_FONT)
        self.text4.tag_bind('follow', '<1>', lambda e, t=self.text4: t.insert(tk.END, "Not now, maybe later!"))
        self.text4.grid(column=0,row=9,columnspan=2,padx=10,sticky=tk.NW)
        self.text4.grid_remove()

        diag = ttk.OptionMenu(self, self.diag_variable,diagnosis[0], *diagnosis,command=self.show_other_text)
        diag.grid(column=0,row=8,columnspan=3,padx=10,sticky=tk.NW)
        
        button4 = ttk.Button(self, text='Save',command=self.save_annotation)
        button4.grid(column=0,row=10,pady=5,padx=10,sticky=tk.NW)

        self.search_entry = ttk.Entry(self, width=10)
        self.search_entry.grid(column=0,row=11, padx=10,ipadx=5,ipady=5, pady=5, sticky=tk.NW)

        search_btn = ttk.Button(self, text="search", command=self.search)
        search_btn.grid(row=11, column=1, pady=5,sticky=tk.NW)

        delete_btn = ttk.Button(self, text="Delete", command=self.delete_annotation)
        delete_btn.grid(row=12, column=0, padx=10, pady=5,sticky=tk.NW)

    def delete_annotation(self):
        confirmation = tk.messagebox.askquestion('confirm','Are you sure?')
        query = self.search_entry.get()
        file_dir = os.getcwd()
        annotatin_dir = os.path.join(file_dir,'annotation')
        path = os.path.join(annotatin_dir,query+'.png')
    
        csv_path = os.path.join(annotatin_dir,'annotation_database.csv')
        if confirmation=='yes':
            data = pd.read_csv(csv_path)
            data = data[data.filename != query]
            data.to_csv(csv_path,index=False)
            os.remove(path)
    def donothing(self):
        return 0   
    def search(self):
        query = self.search_entry.get()
        popup = tk.Toplevel(self)

        size =  '1000x400'
        
        popup.geometry(size)
        # popup.resizable(0, 0)
        
        popup.wm_title("Annotation Search Result")
        TableMargin = tk.Frame(popup, width=500)
        TableMargin.pack()
        
        scrollbarx = ttk.Scrollbar(TableMargin, orient=tk.HORIZONTAL)
        scrollbary = ttk.Scrollbar(TableMargin, orient=tk.VERTICAL)

        tree = ttk.Treeview(
            TableMargin, 
            columns=('index','filename', 'lead','vertical_annotation','feature',
                'description', 'diagnosis','conclusion'), 
            height=400, selectmode="extended", 
            yscrollcommand=scrollbary.set, 
            xscrollcommand=scrollbarx.set)
        scrollbary.config(command=tree.yview)
        scrollbary.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbarx.config(command=tree.xview)
        scrollbarx.pack(side=tk.BOTTOM, fill=tk.X)
        tree.heading('index', text="index", anchor=tk.W)
        tree.heading('filename', text="filename", anchor=tk.W)
        tree.heading('lead', text="lead", anchor=tk.W)
        tree.heading('vertical_annotation', text="v_ann", anchor=tk.W)
        # tree.heading('x1', text="x1", anchor=tk.W)
        # tree.heading('x2', text="x2", anchor=tk.W)
        tree.heading('feature', text="feature", anchor=tk.W)
        tree.heading('description', text="description", anchor=tk.W)
        tree.heading('diagnosis', text="diagnosis", anchor=tk.W)
        tree.heading('conclusion', text="conclusion", anchor=tk.W)
        tree.column('#0', stretch=tk.NO, minwidth=0, width=0)
        tree.column('#1', stretch=tk.NO, minwidth=0, width=30)
        tree.column('#2', stretch=tk.NO, minwidth=0, width=100)
        tree.column('#3', stretch=tk.NO, minwidth=0, width=60)
        tree.column('#4', stretch=tk.NO, minwidth=0, width=100)
        tree.column('#5', stretch=tk.NO, minwidth=0, width=100)
        tree.column('#6', stretch=tk.NO, minwidth=0, width=200)
        tree.column('#7', stretch=tk.NO, minwidth=0, width=200)
        tree.column('#8', stretch=tk.NO, minwidth=0, width=200)
        tree.pack()
        file_dir = os.getcwd()
        annotatin_dir = os.path.join(file_dir,'annotation')

        with open(os.path.join(annotatin_dir,'annotation_database.csv')) as f:
            reader = csv.DictReader(f, delimiter=',')
            for i,row in enumerate(reader):
                index = i
                filename = row['filename']
                lead = row['lead']
                vertical_annotation = row['vertical_annotation']
                # x1 = row['x1']
                # x2 = row['x2']
                feature = row['feature']
                description = row['description']
                diagnosis = row['diagnosis']
                if row['conclusion'] is None:
                    conclusion = ''
                else: 
                    conclusion = row['conclusion']
                tree.insert("", 0, values=(index,filename, lead,vertical_annotation,feature,description,diagnosis,conclusion))
        selections = []
        for child in tree.get_children():
            if query in tree.item(child)['values']:   # compare strings in  lower cases.
                selections.append(child)
        if query:
            self.clear_fig_draw_image(query)
        tree.selection_set(selections)

    def clear_fig_draw_image(self,filename):
        global g_fig
        g_fig.clear()
        ax = g_fig.add_subplot()
        file_dir = os.getcwd()
        annotatin_dir = os.path.join(file_dir,'annotation')
        path = os.path.join(annotatin_dir,filename+'.png')

        arr_lena = mpimg.imread(path)
        imagebox = OffsetImage(arr_lena, zoom=1)
        ab = AnnotationBbox(imagebox, (0.5, 0.5))
        ax.add_artist(ab)
        g_canvas.draw()
            
    def show_other_text(self,*args):
        _grid_info = self.text4.grid_info()
        if(self.diag_variable.get()=='Other Diagnosis'):
            self.text4.grid(_grid_info)
        else:
            self.text4.grid_remove()
    
    def clear_up_things(self):
        txt = ''
        self.label_text.set(str(txt))
        final_annotation.clear()
        ecg_statement.clear()
        self.vertical_annotation.clear()
    def write_json(self,new_data, filename='data.json'):
        with open(filename,'r+') as file:
            # First we load existing data into a dict.
            file_data = json.load(file)
            # Join new_data with file_data inside emp_details
            file_data.append(new_data)
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            json.dump(file_data, file, indent = 6)
    
    def save_annotation(self):
        global color_count,ecg_statement
        confirmation = tk.messagebox.askquestion('confirm','Are you sure?')

        header = ['filename','lead','vertical_annotation','x1','x2','feature','description','diagnosis','conclusion']
        for ann in final_annotation:
            ann.append(self.diag_variable.get())
            if(self.diag_variable.get()=='Other Diagnosis'):
                ann.append(self.text4.get("1.0","end-1c"))    
            
        file_dir = os.getcwd()
        annotatin_dir = os.path.join(file_dir,'annotation')
        print(os.path.isdir(annotatin_dir))
        if not os.path.isdir(annotatin_dir):
            os.mkdir(annotatin_dir)
        path_to_file = os.path.join(annotatin_dir,'annotation_database.csv')

        if confirmation == 'yes':
            if os.path.exists(path_to_file):
                g_fig.savefig(os.path.join(annotatin_dir,filename+'.png'))  # save the figure to file
                with open(path_to_file,'a') as f:
                    writer = csv.writer(f)
                    writer.writerows(final_annotation)
                self.clear_up_things()
                if color_count<4:
                    color_count +=1
                else:
                    color_count = 0
            else:
                g_fig.savefig(os.path.join(annotatin_dir,filename+'.png'))  # save the figure to file
                with open(path_to_file,'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(final_annotation)
                self.clear_up_things()
                if color_count<4:
                    color_count +=1
                else:
                    color_count = 0
                    
class StartPage(tk.Frame):

    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        frame1 = tk.Frame(self)#,bg='#12ADB3')
        frame1.pack(side=tk.TOP,fill=tk.X)
        global joined_data, ann2
        
        ann2=pd.read_csv(joined_data)
        label1 = ttk.Label(frame1,text='Sarting Index')
        label1.pack(side=tk.LEFT)
       
        
       
        self.label_text = tk.StringVar(frame1)
        self.label_text.set(0)

        label3 = ttk.Entry(frame1,textvariable=self.label_text)
        label3.pack(side=tk.LEFT, padx=5)
        label2 = ttk.Label(frame1,text='Selected Annotation: '+joined_data)
        label2.pack(side=tk.LEFT)
        button0 = tk.Button(frame1,text='Load',command=self.next_figure)
        button0.pack(side=tk.LEFT,padx=10)
        button0.configure(bg='#12ADB3')
        button1 = tk.Button(frame1,text='Change',command=self.load_file)
        button1.pack(side=tk.LEFT,padx=10)
        button1.configure(bg='#12ADB3')
        width= tk.Tk.winfo_screenwidth(self)
        height= tk.Tk.winfo_screenheight(self)
               
        self.fig = Figure(figsize=(int(width*0.015),int(height*0.10)))
        self.fig.subplots_adjust(hspace=0.05, wspace=0.05,left=0.025,right=0.995,bottom=0.05,top=0.995)

        self.axes = []
        self.axes.append(self.fig.add_subplot(1,2,1)) 
        self.axes.append(self.fig.add_subplot(1,2,2)) 
        self.axes[0].grid(False)
        self.axes[1].grid(False)
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

    def next_figure(self):
        annotation_objects.clear()
        final_annotation.clear()
        ecg_statement.clear()
        interval.clear()
        mouse_enable = True
        global color_count,ann2,start_index,joined_data
        start_index=int(self.label_text.get())
        if(start_index==0):
            confirmation = tk.messagebox.askquestion('confirm','Are you sure to delete existing data?')
            if confirmation!="yes":
                return "Error"
        
        ann2=pd.read_csv(joined_data)
        im1,im2,ann1,ann2=self.load_annotation(start_index)
        self.axes[0].imshow(im1)
        self.axes[1].imshow(im2)

        self.canvas.draw()
        annotation.clear()

    def load_file(self):
        file = filedialog.askopenfilename(filetypes=(("dat or csv files",["*.dat","*.csv"]),("All files","*.*")))
        #print(file, self.label_text.get())
        
        
        annotation_objects.clear()
        final_annotation.clear()
        ecg_statement.clear()
        interval.clear()
        mouse_enable = True
        global color_count,ann2,start_index,joined_data
        joined_data=file
        start_index=int(self.label_text.get())
        if(start_index==0):
            confirmation = tk.messagebox.askquestion('confirm','Are you sure to delete existing data?')
            if confirmation!="yes":
                return "Error"
        
        ann2=pd.read_csv(file)
        im1,im2,ann1,ann2=self.load_annotation(start_index)
        self.axes[0].imshow(im1)
        self.axes[1].imshow(im2)

        self.canvas.draw()
        annotation.clear()
        
    def load_annotation(self, id):
        global ann2, anns_1,anns_2
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
            print("annotation by ",first_doctor)
            anns_1=self.extract_annotation(json_path_1)
            print("annotation by ",second_doctor)
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
            assert len(ann) == 4, "box should contain  class_indx,score,poly,indx"
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
                print(centroid.x,centroid.y)
                
                
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
                        anns.append([int(annotation["label"]),annotation["BIRADS_level"],polys, indx_counter])
                        print(indx_counter,"label:",annotation["label_name"],"Level:",annotation["BIRADS_level_name"])
                    except Exception as e:
                        print("error occured processing",json_path)
                    #print(df_loc["label"][0])
                if(annotation["label"]==8):
                    anns.append([8,annotation["Density_level"],[], indx_counter])
                if (annotation["label_name"]=="Normal"):
                    anns.append([9,0,[], indx_counter])

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
