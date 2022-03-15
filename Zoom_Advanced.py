
from tkinter import ttk
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageDraw
import json  
from functools import partial  
from pydicom.filereader import dcmread
import skimage.io as io
import matplotlib.pyplot as plt
import numpy as np
import pydicom
import math
from pydicom.pixel_data_handlers.util import apply_voi_lut

class AutoScrollbar(ttk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')

class Zoom_Advanced(ttk.Frame):
    ''' Advanced zoom of the image '''
    coord=[]  # for saving coord of each click position
    Dict_Polygons={}   # Dictionary for saving polygons
    list_of_points=[]
    annotations=[]
    current_label=0
    current_label_name=""
    label_color="gray"
    dash_type=(10,1)
    birads_level=1
    birads_level_name="Bi-RADS 1"
    container=None
    imscale=1
    image=None
    age=0
    delta=1.3
    width=None
    height=None
    path=""
    def __init__(self, mainframe):
        ttk.Frame.__init__(self, master=mainframe)
        vbar = AutoScrollbar(self.master, orient='vertical')
        hbar = AutoScrollbar(self.master, orient='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        self.imscale=1
        self.image=None
        self.age=0
        self.list_of_points=[]
        self.annotations=[]
        #self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self.master, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        self.width, self.height=self.master.winfo_screenmmwidth()/2,self.master.winfo_screenmmheight()
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.frame_position="UNKNOWN"
    def reset(self, mainframe):
        ttk.Frame.__init__(self, master=mainframe)
        vbar = AutoScrollbar(self.master, orient='vertical')
        hbar = AutoScrollbar(self.master, orient='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        self.imscale=1
        self.image=None
        self.age=0
        self.list_of_points=[]
        self.annotations=[]
        #self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self.master, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        self.width, self.height=self.master.winfo_screenmmwidth()/2,self.master.winfo_screenmmheight()
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.frame_position="UNKNOWN"
    
    def init(self, path, position):
        ''' Initialize the main Frame '''
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<Button-2>', self.draw_polygons)
        self.canvas.bind('<Button-3>', self.draw_polygons)
        self.canvas.bind('<ButtonPress-1>', self.move_from)
        self.canvas.bind('<B1-Motion>',     self.move_to)
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.wheel)  # only with Linux, wheel scroll up
        #self.canvas.focus_set()
        
        #self.master.title('Zoom with mouse wheel')
        # Vertical and horizontal scrollbars for canvas
        #print(self.position)
        self.path=path
        self.frame_position=position
        self.label_color="green"
        if(position=="left"):
            self.active_pane=0
        else:
            self.active_pane=1
        #self.window.after(100, self.selecting_file)
        ds = pydicom.dcmread(path, force=True)

        try:
            self.age=ds.PatientAge
        except:
            self.age='-1Y'
        #shape = ds.pixel_array.shape
        image_2d = ds.pixel_array.astype(float)
        if 'WindowWidth' in ds:
            print('Dataset has windowing')
            windowed  = apply_voi_lut(ds.pixel_array, ds)
            #plt.imshow(windowed, cmap="gray", vmax=windowed.max(), vmin=windowed.min)
            #plt.show()
            image_2d=windowed.astype(float)
            
        

        # Convert to float to avoid overflow or underflow losses.
        #image_2d = ds.pixel_array.astype(float)

        # Rescaling grey scale between 0-255
        image_2d_scaled = (np.maximum(image_2d,0) / image_2d.max()) * 255.0

        # Convert to uint
        image_2d_scaled = np.uint8(image_2d_scaled)

        self.image = Image.fromarray(image_2d_scaled,'L')  # open image
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        # Plot some optional random rectangles for the test purposes
        
        self.show_image()
    

    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        #print(event.delta)
        if event.num == 5 or event.delta < -0:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if event.num == 4 or event.delta > 0:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None):
        ''' Show image on the Canvas '''
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection
     
    def draw_polygons(self,event):
        if(self.frame_position=="left"):
            self.active_pane=0
        else:
            self.active_pane=1
        #global poly, list_of_points
        self.canvas.delete('polygon')
        self.canvas.delete('points')
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        bbox1 = (bbox[0] + 1, bbox[1] + 1, bbox[2] - 1, bbox[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        x_shift=bbox1[0]
        y_shift=bbox1[1]
        
        #canvas_w=bbox2[2]-bbox2[0]
        #canvas_height=bbox2[3]-bbox2[1]
        ori_w,ori_h=self.image.size

        im_w=bbox[2]-bbox[0]
        im_h=bbox[3]-bbox[1]
       
        scale=im_h*im_w/(ori_h*ori_w)
        #print(canvas_w,canvas_height)
        #print(self.list_of_points)
        ac_x=math.floor((x-x_shift)/self.imscale)
        ac_y=math.floor((y-y_shift)/self.imscale)
        #x=(x-x_shift)/scale
        #y=(y-y_shift)/scale
        # print(x,y)
        self.list_of_points.append((ac_x,ac_y))
        list_of_points2=[]
        for pt in self.list_of_points:
            x, y =  pt
            x=x*self.imscale+x_shift
            y=y*self.imscale+y_shift
            list_of_points2.append((x,y))
            if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
            else: return  # zoom only inside image area
            #draw dot over position which is clicked
            x1, y1 = (x - 1), (y - 1)
            x2, y2 = (x + 1), (y + 1)
            self.canvas.create_oval(x1, y1, x2, y2, fill=self.label_color, outline=self.label_color, width=0, tags=('points'))    
        numberofPoint=len(list_of_points2)
        # Draw polygon
        if numberofPoint>2:
            self.current_polygon=self.poly=self.canvas.create_polygon(list_of_points2, fill='', outline=self.label_color, width=2,tags=('polygon'),dash=self.dash_type)
            self.canvas.coords(self.poly,)

            
        elif numberofPoint==2 :
            print('line')
            self.current_polygon=self.canvas.create_line(list_of_points2, tags=('polygon'))
        else:
            print('dot')

    