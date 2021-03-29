# -*- coding: utf-8 -*-
# Advanced zoom example. Like in Google Maps.
# It zooms only a tile, but not the whole image. So the zoomed tile occupies
# constant memory and not crams it with a huge resized image for the large zooms.
import random
import tkinter as tk
from tkinter import Event, ttk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageDraw
import json  
from functools import partial  
from pydicom.filereader import dcmread
import skimage.io as io
import matplotlib.pyplot as plt
import numpy as np
import Zoom_Advanced
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
            current_frame.canvas.create_oval(x1, y1, x2, y2, fill=current_frame.label_color, outline=current_frame.label_color, width=5, tags=('points'))
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
        current_frame.annotations.append(({'label':current_frame.current_label,'poly':current_frame.list_of_points}))
        list_of_points2=[]
        for pt in current_frame.list_of_points:
            x, y =  pt
            x=x*scale+x_shift
            y=y*scale+y_shift
            list_of_points2.append((x,y))
        current_frame.canvas.create_polygon(list_of_points2, fill='', outline=current_frame.label_color, width=2,tags=('final_polygon'))
        
        #current_frame.canvas.coords(current_frame.poly,)
        current_frame.list_of_points=[]
        print(json.dumps(current_frame.annotations))
    
    #print(event.keysym)
    #print("pressed", repr(event.char))
def key(event):
        #print(app.canvas.bbox(app.container))
        #print(app2.canvas.bbox(app2.container))
        #if(app.canvas.bbox)
        print("current frame is",app.list_of_points, "Position", app.frame_position, "current frame is",app2.list_of_points, "Position", app2.frame_position)
        
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
        if(len(app2.list_of_points)>0):
            bbox = app2.canvas.bbox(app2.container)  # get image area
            bbox1 = (bbox[0] + 1, bbox[1] + 1, bbox[2] - 1, bbox[3] - 1)
            x_shift=bbox1[0]
            y_shift=bbox1[1]
            params=(app2.imscale,x_shift, y_shift)
            if(event.keysym=="BackSpace"):
                key_func(app2,"BackSpace", params)
            if(event.keysym=="Escape"):
                key_func(app2, "Escape", params)
            if(event.keysym=="Return"):
                key_func(app2, "Return", params)
def selecting_files():
    filename_l = filedialog.askopenfilename()
    app.init(path=filename_l, position="left")
    filename_r = filedialog.askopenfilename()
    app2.init(path=filename_r, position="right") 
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

def savejson():
    #print(filename_l)
    #print(filename_r)
    with open(app.path+'.json', 'w') as f:
        json.dump(app.annotations, f, indent=4)
    with open(app2.path+'.json', 'w') as f:
        json.dump(app2.annotations, f,indent=4)
def donothing():
    filewin = tk.Toplevel(root)
    button = tk.Button(filewin, text="Do nothing button")
    button.pack()
def change_label(lcolor, label):
    app.label_color=lcolor
    app2.label_color=lcolor
    app.current_label=label
    app2.current_label=label
       
path = 'M13.jpg'  # place path to your image here
current_label=0
label_color="green"
active_pane=0
filename_l=None
filename_r=None
root = tk.Tk()
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.geometry("%dx%d+0+0" % (w, h))
root.bind("<Key>", key)

frame = tk.Frame(root,  width=w/2, height=h, bd=1)
frame.pack(side="left", fill="both", expand=True)
#frame.tkraise()
frame2 = tk.Frame(root,  width=w/2, height=h, bd=1)
frame2.pack(side="right", fill="both", expand=True)
#frame2.tkraise()
app = Zoom_Advanced.Zoom_Advanced(frame)
app2 = Zoom_Advanced.Zoom_Advanced(frame2)
menubar = tk.Menu(root)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="OpenFiles", command=selecting_files)
#filemenu.add_command(label="Open Right", command=lambda: selecting_file2(app2))
filemenu.add_command(label="Save Annotations", command=savejson)
filemenu.add_command(label="Close", command=donothing)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)
labelmenu = tk.Menu(menubar, tearoff=0)
label_color="green"
active_pane=0
labelmenu.add_command(label="Benign Mass", background="green", command=partial(change_label,'green',0))
labelmenu.add_command(label="Malignant Mass", background="yellow", command=partial(change_label,'yellow',1))
labelmenu.add_command(label="Benign Calcification",background="orange", command=partial(change_label,'orange',2))
labelmenu.add_command(label="Malignant Calcification",background="cyan", command=partial(change_label,'cyan',3))
menubar.add_cascade(label="Change Label", menu=labelmenu)
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help Index", command=donothing)
helpmenu.add_command(label="About...", command=donothing)
menubar.add_cascade(label="Help", menu=helpmenu)

root.config(menu=menubar)
#menubar.pack()
#print(app2.list_of_points)
root.mainloop()