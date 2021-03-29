import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk, Image, ImageDraw
import json  
from functools import partial  
from pydicom.filereader import dcmread
import skimage.io as io
import matplotlib.pyplot as plt
import numpy as np
    
class App():
    coord=[]  # for saving coord of each click position
    Dict_Polygons={}   # Dictionary for saving polygons
    list_of_points=[]
    annotations=[]
    list_of_points_r=[]
    annotations_r=[]
    
    poly = None
    current_polygon=None
    current_label=None
    label_color="green"
    active_pane=0
    filename_l=None
    filename_r=None
    def dicomtopil(self, dataset):
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

    def savejson(self):
        print(self.filename_l)
        print(self.filename_r)
        with open(self.filename_l+'.json', 'w') as f:
            json.dump(self.annotations, f, indent=4)
        with open(self.filename_r+'.json', 'w') as f:
            json.dump(self.annotations_r, f,indent=4)
    def donothing(self):
        filewin = tk.Toplevel(self.window)
        button = tk.Button(filewin, text="Do nothing button")
        button.pack()
    def change_label(self, lcolor, label):
        self.label_color=lcolor
        self.current_label=label
        print(lcolor)
        print(label)
    def __init__(self):
        self.window = tk.Tk()
        menubar = tk.Menu(self.window)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Left", command=self.selecting_file)
        filemenu.add_command(label="Open Right", command=self.selecting_file2)
        filemenu.add_command(label="Save Annotations", command=self.savejson)
        filemenu.add_command(label="Close", command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.window.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        labelmenu = tk.Menu(menubar, tearoff=0)
        self.label_color="green"
        self.active_pane=0
        labelmenu.add_command(label="Benign Mass", background="green", command=partial(self.change_label,'green',0))
        labelmenu.add_command(label="Malignant Mass", background="yellow", command=partial(self.change_label,'yellow',1))
        labelmenu.add_command(label="Benign Calcification",background="orange", command=partial(self.change_label,'orange',2))
        labelmenu.add_command(label="Malignant Calcification",background="cyan", command=partial(self.change_label,'cyan',3))
        menubar.add_cascade(label="Change Label", menu=labelmenu)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help Index", command=self.donothing)
        helpmenu.add_command(label="About...", command=self.donothing)
        menubar.add_cascade(label="Help", menu=helpmenu)

        #self.window.after(100, self.selecting_file)
        self.current_polygon=0
        self.current_label=0
        self.coord=[]  # for saving coord of each click position
        self.Dict_Polygons={}   # Dictionary for saving polygons
        self.list_of_points=[]
        self.list_of_points_r=[]
        self.annotations_r=[]
        self.annotations=[]
        self.poly = None
        self.window.config(menu=menubar)
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.canvas = tk.Canvas(self.window, width=screen_width/2, height=screen_height)
        self.canvas.focus_set()
        self.canvas.bind('<Button-1>', self.draw_polygons)
        self.canvas.bind("<Key>", self.key)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.rcanvas = tk.Canvas(self.window, width=screen_width/2, height=screen_height)
        self.rcanvas.focus_set()
        self.rcanvas.bind('<Button-1>', self.draw_polygons2)
        self.rcanvas.bind("<Key>", self.key)
        self.rcanvas.pack(side="right", fill="both", expand=True)
       
        self.window.mainloop()
        
    def draw_polygons(self,event):
        self.active_pane=0
        #global poly, list_of_points
        self.canvas.delete('polygon')

        self.list_of_points.append((event.x, event.y))

        for pt in self.list_of_points:
            x, y =  pt
            #draw dot over position which is clicked
            x1, y1 = (x - 1), (y - 1)
            x2, y2 = (x + 1), (y + 1)
            self.canvas.create_oval(x1, y1, x2, y2, fill=self.label_color, outline=self.label_color, width=5, tags=('points'))
        # add clicked positions to list

        numberofPoint=len(self.list_of_points)
        # Draw polygon
        if numberofPoint>2:
            self.current_polygon=self.poly=self.canvas.create_polygon(self.list_of_points, fill='', outline=self.label_color, width=2,tags=('polygon'))
            self.canvas.coords(self.poly,)

        elif numberofPoint==2 :
            print('line')
            self.current_polygon=self.canvas.create_line(self.list_of_points, tags=('polygon'))
        else:
            print('dot')
    def draw_polygons2(self,event):
        self.active_pane=1
        #global poly, list_of_points
        self.rcanvas.delete('polygon')
        self.list_of_points_r.append((event.x, event.y))
        for pt in self.list_of_points_r:
            x, y =  pt
            #draw dot over position which is clicked
            x1, y1 = (x - 1), (y - 1)
            x2, y2 = (x + 1), (y + 1)
            self.rcanvas.create_oval(x1, y1, x2, y2, fill=self.label_color, outline=self.label_color, width=5, tags=('points'))
        # add clicked positions to list

        numberofPoint=len(self.list_of_points_r)
        # Draw polygon
        if numberofPoint>2:
            self.current_polygon=self.poly=self.rcanvas.create_polygon(self.list_of_points_r, fill='', outline=self.label_color, width=2,tags=('polygon'))
            self.rcanvas.coords(self.poly,)

        elif numberofPoint==2 :
            print('line')
            self.current_polygon=self.rcanvas.create_line(self.list_of_points_r, tags=('polygon'))
        else:
            print('dot')

    def key(self,event):
        if(self.active_pane==0):
            if(event.keysym=="BackSpace"):
                self.canvas.delete('points')
                self.canvas.delete(self.current_polygon)
                #print(self.current_polygon)
                self.list_of_points.pop()
                for pt in self.list_of_points:
                    x, y =  pt
                    #draw dot over position which is clicked
                    x1, y1 = (x - 1), (y - 1)
                    x2, y2 = (x + 1), (y + 1)
                    self.canvas.create_oval(x1, y1, x2, y2, fill=self.label_color, outline=self.label_color, width=5, tags=('points'))
                # add clicked positions to list

                numberofPoint=len(self.list_of_points)
                # Draw polygon
                if numberofPoint>2:
                    self.current_polygon=self.poly=self.canvas.create_polygon(self.list_of_points, fill='', outline=self.label_color, width=2,tags=('polygon'))
                    self.canvas.coords(self.poly,)

                elif numberofPoint==2 :
                    print('line')
                    self.current_polygon=self.canvas.create_line(self.list_of_points, tags=('polygon'))
                else:
                    print('dot')

            if(event.keysym=="Escape"):
                print(self.current_polygon)
                self.canvas.delete('points')
                self.canvas.delete(self.current_polygon)
                self.list_of_points=[]
            if(event.keysym=="Return"):
                print("Return was pressed")
                self.canvas.delete('points')
                self.annotations.append(({'label':self.current_label,'poly':self.list_of_points}))
                self.canvas.create_polygon(self.list_of_points, fill='', outline=self.label_color, width=2,tags=('final_polygon'))
                #self.canvas.coords(self.poly,)
                self.list_of_points=[]
                print(json.dumps(self.annotations))
            #print(event.keysym)
            #print("pressed", repr(event.char))
        elif(self.active_pane==1):
            if(event.keysym=="BackSpace"):
                self.rcanvas.delete('points')
                self.rcanvas.delete(self.current_polygon)
                #print(self.current_polygon)
                self.list_of_points_r.pop()
                for pt in self.list_of_points_r:
                    x, y =  pt
                    #draw dot over position which is clicked
                    x1, y1 = (x - 1), (y - 1)
                    x2, y2 = (x + 1), (y + 1)
                    self.rcanvas.create_oval(x1, y1, x2, y2, fill=self.label_color, outline=self.label_color, width=5, tags=('points'))
                # add clicked positions to list

                numberofPoint=len(self.list_of_points_r)
                # Draw polygon
                if numberofPoint>2:
                    self.current_polygon=self.poly=self.rcanvas.create_polygon(self.list_of_points_r, fill='', outline=self.label_color, width=2,tags=('polygon'))
                    self.rcanvas.coords(self.poly,)

                elif numberofPoint==2 :
                    print('line')
                    self.current_polygon=self.rcanvas.create_line(self.list_of_points_r, tags=('polygon'))
                else:
                    print('dot')

            if(event.keysym=="Escape"):
                print(self.current_polygon)
                self.rcanvas.delete('points')
                self.rcanvas.delete(self.current_polygon)
                self.list_of_points_r=[]
            if(event.keysym=="Return"):
                self.rcanvas.delete('points')
                print("Return was pressed on right canvas")
                self.annotations_r.append(({'label':self.current_label,'poly':self.list_of_points_r}))
                self.rcanvas.create_polygon(self.list_of_points_r, fill='', outline=self.label_color, width=2,tags=('final_polygon'))
                #self.rcanvas.coords(self.poly,)
                self.list_of_points_r=[]
                print(json.dumps(self.annotations_r))
            #print(event.keysym)
            #print("pressed", repr(event.char))

    
    def save_as_png(self,fileName):
        # save postscipt image 
        self.canvas.postscript(file = fileName + '.eps') 
        # use PIL to convert to PNG 
        img = Image.open(fileName + '.eps') 
        img.save(fileName + '.png', 'png')

    def selecting_file(self):
        self.filename_l = filedialog.askopenfilename()
        #print(self.filename_l)
        #self.file_path = filedialog.askopenfilename(initialdir='images/', initialfile='example.jpg')
        ds=dcmread(self.filename_l)
        
        self.image = self.dicomtopil(ds)
        #self.image=self.image.convert('L')
        #print(img.shape)
        #self.image = Image.fromarray(img,'L')
        #plt.imshow(self.image, cmap=plt.cm.gray) 
        #plt.show()
        aes=np.asarray(self.image)
        print(np.amax(aes))
        #print(self.image.size)
        self.width, self.height = self.image.size
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        scale=min(screen_width/(2*self.width),screen_height/self.height)
        print(scale)
        self.image = self.image.resize((512,512))
        self.width, self.height = self.image.size
        print(self.image.size)
        
        self.draw  = ImageDraw.Draw(self.image)
        self.photo = ImageTk.PhotoImage(image=self.image)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        
    def selecting_file2(self):
        self.filename_r = filedialog.askopenfilename()
        #self.file_path = filedialog.askopenfilename(initialdir='images/', initialfile='example.jpg')
        self.imager = Image.open(self.filename_r)
        print(self.imager)
        self.width, self.height = self.imager.size
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        scale=min(screen_width/self.width,screen_height/self.height)
        self.imager = self.imager.resize((int(self.width*scale), int(self.height*scale)), Image.ANTIALIAS)
        self.width, self.height = self.imager.size
        self.drawr  = ImageDraw.Draw(self.imager)
        self.photor = ImageTk.PhotoImage(image=self.imager)
        self.rcanvas.create_image(0, 0, image=self.photor, anchor=tk.NW)
        
    def draw_circle(self, event):
        # display on canvas
        self.canvas.create_oval((event.x-5, event.y-5, event.x+5, event.y+5), width=2, outline='#FF0000')
        # draw on self.image
        self.draw.ellipse((event.x-5, event.y-5, event.x+5, event.y+5), width=2, outline=(255,0,0))

    def save(self):
        self.image.save('output.jpg')

# --- main ---

App()