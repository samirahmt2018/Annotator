#!/usr/bin/python
#-*-coding:utf-8-*-
import os
import sys
if sys.version_info<(3, 0):
  import tkinter as tk #import tkinter library
  from tkfiledialog import askopenfilename, asksaveasfilename
else:
  import tkinter as tk #import tkinter library
  from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import ImageTk, Image, ImageDraw
from time import sleep
import numpy as np
import cv2 as cv
def_width=1080
def_height=720
image_height=720
frame_left_width=360
#Too small selected area we need to discard,Prevent misuse
mini_rect_area=20
class rawimageeditor:
  def _init_(self, win, img, rects):
    #Variables x and y are used to record the position of the left mouse button down
    self.x=tk.intvar (value=0)
    self.y=tk.intvar (value=0)
    self.sel=False
    self.lastdraw=None
    self.lastdraws=[]
    self.imagescale=1.0
    self.dispwidth=def_width #The maximum height of the image display area,width
    self.dispheight=def_height
    self.rawimage=img
    self.calcimagescale (self.rawimage)
    self.dispwidth=int (self.imagescale * self.rawimage.width)
    self.dispheight=int (self.imagescale * self.rawimage.height)
    #Image zoom
    self.dispimage=self.rawimage.resize ((self.dispwidth, self.dispheight))
    #select area
    self.selpositions=[]
    for r in rects:
      self.selpositions.append ((r [0] * self.imagescale, r [1] * self.imagescale, r [2] * self.imagescale, r [3] * self.imagescale))
    #Create a top-level component container
    self.top=tk.toplevel (win, width=self.dispwidth, height=self.dispheight)
    #Do not show maximize, minimize buttons
    self.top.overrideredirect (True)
    #make toplevelwindow remain on top until destroyed, or attribute changes.
    self.top.attributes ("-topmost", "true")
    self.canvas=tk.canvas (self.top, bg="white", width=self.dispwidth, height=self.dispheight)
    self.tkimage=imagetk.photoimage (self.dispimage)
    self.canvas.create_image (self.dispwidth //2, self.dispheight //2, image=self.tkimage)
    for r in self.selpositions:
      draw=self.canvas.create_rectangle (r [0], r [1], r [2], r [3], outline="green")
      self.lastdraws.append (draw)
    #Position of the left mouse button
    def onleftbuttondown (event):
      self.x.set (event.x)
      self.y.set (event.y)
      self.sel=True
      #Redraw the selected area
      for draw in self.lastdraws:
        self.canvas.delete (draw)
      self.lastdraws=[]
      for r in self.selpositions:
        draw=self.canvas.create_rectangle (r [0], r [1], r [2], r [3], outline="green")
        self.lastdraws.append (draw)
    self.canvas.bind ("<button-1>", onleftbuttondown)
    #Mouse left button to move,Show selected area
    def onleftbuttonmove (event):
      if not self.sel:
        return
      try:
        #Delete the graphics just finished,Otherwise, it will be a dark rectangle when the mouse moves
        self.canvas.delete (self.lastdraw)
      except Exception as e:
        pass
      self.lastdraw=self.canvas.create_rectangle (self.x.get (), self.y.get (), event.x, event.y, outline="green")
    self.canvas.bind ("<b1-motion>", onleftbuttonmove)
    def onleftbuttonup (event):
      self.sel=False
      sleep (0.1)
      left, right=sorted ([self.x.get (), event.x])
      top, bottom=sorted ([self.y.get (), event.y])
      if (right-left) * (bottom-top)>mini_rect_area:
        self.selpositions.append ((left, top, right, bottom))
      #self.top.destroy ()
    #Right mouse button down
    def onrightbuttondown (event):
      self.sel=False
      self.top.destroy ()
    self.canvas.bind ("<button-2>", onrightbuttondown)
    self.canvas.bind ("<buttonrelease-1>", onleftbuttonup)
    self.canvas.pack (fill=tk.both, expand=tk.yes)
  def calcimagescale (self, image):
    w=image.width
    h=image.height
    self.imagescale=1.0
    #Calculate the minimum zoom ratio,Guaranteed original aspect ratio
    if w>self.dispwidth and h>self.dispheight:
      ws=self.dispwidth * 1.0/w
      hs=self.dispheight * 1.0/h
      if ws<hs:
        self.imagescale=ws
      else:
        self.imagescale=hs
    elif w>self.dispwidth and h<self.dispheight:
      self.imagescale=self.dispwidth * 1.0/w
    elif w<self.dispwidth and h>self.dispheight:
      self.imagescale=self.dispheight * 1.0/h
  def waitforwindow (self, win):
    win.wait_window (self.top)
  def selectedpositions (self):
    #Convert to original pixel position
    realpos=[]
    for r in self.selpositions:
      realpos.append ((r [0]/self.imagescale, r [1]/self.imagescale, r [2]/self.imagescale, r [3]/self.imagescale))
    return realpos
class mainwin (tk.tk):
  def _init_(self):
    if sys.version_info>= (3, 0):
      super () ._init_()
    else:
      tk.tk ._init_(self)
    self.title ("Image Processing Tool")
    self.geometry ("{} x {}". format (def_width, def_height))
    self.rawimagepath=""
    self.rawimage=None #self.rawimage raw image,Not scaled
    self.transrawimage=None #self.transrawimage The original image after conversion processing,Not scaled
    self.dispimage=None #self.dispimage displays the image,May be scaled
    self.imagescale=1.0 #image scale,Zoom processing when displaying according to the zoom ratio,When selecting a region later,Requires zoom restore
    self.leftframewidth=frame_left_width
    self.framedispheight=def_height #height of the entire window
    self.labeltextheight=20 #height of the text label
    self.btnheight=40 #height of the button
    self.imagedispwidth=image_height #The maximum height of the image display area,width
    self.imagedispheight=self.framedispheight/2-self.labeltextheight * 2
    #select area
    self.lirect=[]
    self.rawimageeditor=None
    self.setupui ()
  def scaledisplayimage (self, image):
    w=image.width
    h=image.height
    self.imagescale=1.0
    #Calculate the minimum zoom ratio,Guaranteed original aspect ratio
    if w>self.imagedispwidth and h>self.imagedispheight:
      ws=self.imagedispwidth * 1.0/w
      hs=self.imagedispheight * 1.0/h
      if ws<hs:
        self.imagescale=ws
      else:
        self.imagescale=hs
    elif w>self.imagedispwidth and h<self.imagedispheight:
      self.imagescale=self.imagedispwidth * 1.0/w
    elif w<self.imagedispwidth and h>self.imagedispheight:
      self.imagescale=self.imagedispheight * 1.0/h
    #Image zoom
    return image.resize ((int (self.imagescale * w), int (self.imagescale * h)))
  #Used when opening pictures,Pass the value (picture) to the display function
  def openanddisplayimage (self):
    self.rawimagepath=self.selectimagefile ()
    if ""!=self.rawimagepath:
      self.rawimage=image.open (self.rawimagepath)
      self.rawimage=self.rawimage.convert ("rgba")
      self.drawrawimagedisp ()
  def drawlistbox (self):
    self.l_box.delete (0, tk.end)
    for item in self.lirect:
      r="{}, {}, {}, {}". format (round (item [0], 1), round (item [1], 1), round (item [2], 1), round ( item [3], 1))
      self.l_box.insert (0, r)
  def drawrawimagedisp (self, selitems=[]):
    self.dispimage=self.scaledisplayimage (self.rawimage)
    self.dispimage=self.dispimage.convert ("rgb")
    draw=imagedraw.draw (self.dispimage)
    for i in range (len (self.lirect)):
      r=self.lirect [i]
      if i in selitems:
        draw.rectangle ((r [0] * self.imagescale, r [1] * self.imagescale, r [2] * self.imagescale, r [3] * self.imagescale), outline="red")
      else:
        draw.rectangle ((r [0] * self.imagescale, r [1] * self.imagescale, r [2] * self.imagescale, r [3] * self.imagescale), outline="green")
    img=imagetk.photoimage (self.dispimage)
    self.image_l_raw.config (image=img)
    self.image_l_raw.image=img
  def deleteselecteditemfromlistbox (self):
    #print (self.l_box.get (self.l_box.curselection ()))
    idx=self.l_box.curselection ()
    if len (idx)>0:
      kp=[]
      for v in range (len (self.lirect)):
        if v not in idx:
          kp.append (self.lirect [v])
      self.lirect=kp
      self.drawlistbox ()
      self.drawrawimagedisp ()
  #Used when opening pictures,Get address
  def selectimagefile (self):
    path=tk.stringvar ()
    file_entry=tk.entry (self, state="readonly", text=path)
    path_=askopenfilename ()
    path.set (path_)
    return file_entry.get ()
  def rawimagelabelclicked (self, event):
    if None!=self.rawimage:
      if None == self.rawimageeditor:
        self.rawimageeditor=rawimageeditor (self, self.rawimage, self.lirect)
        self.rawimageeditor.waitforwindow (self.image_l_raw)
        self.lirect=self.rawimageeditor.selectedpositions ()
        self.rawimageeditor=None
        self.drawlistbox ()
        self.drawrawimagedisp ()
  def onrectlistboxselect (self, event):
    idx=self.l_box.curselection ()
    if len (idx)>0:
      self.drawrawimagedisp (idx)
  def drawtransimagedisp (self):
    transimage=self.scaledisplayimage (self.transrawimage)
    transimage=transimage.convert ("l")
    img=imagetk.photoimage (transimage)
    self.image_l_trans.config (image=img)
    self.image_l_trans.image=img
  def dotransrawimage (self):
    self.transrawimage=image.new ("l", (self.rawimage.width, self.rawimage.height))
    for r in self.lirect:
      im=self.rawimage.crop (r)
      cv_im=cv.cvtcolor (np.asarray (im), cv.color_rgb2bgr)
      hsv=cv.cvtcolor (cv_im, cv.color_bgr2hsv)
      _, _, v=cv.split (hsv)
      avg=np.average (v.flatten ())
      pixels=im.load ()
      for j in range (im.height):
        for i in range (im.width):
          hv=v [j, i]
          if hv<avg * 1.2:
            #im.putpixel ((i, j), 0) #slow
            pixels [i, j]=0
          else:
            im.putpixel ((i, j), (255, 255, 255, 255))
      self.transrawimage.paste (im, (int (r [0]), int (r [1])), mask=None)
    self.drawtransimagedisp ()
  def ontransrawimagebtnclicked (self):
    if None!=self.rawimage:
      self.dotransrawimage ()
  def onsavetransrawimagebtnclicked (self):
    if None!=self.transrawimage:
      ext=os.path.splitext (self.rawimagepath) [-1]
      (path, name)=os.path.split (self.rawimagepath)
      filename=asksaveasfilename (title="Save Picture", initialfile=name, filetypes=(("jpeg files", "* {}". format (ext)), ("all files", "*. *")) )
      if ""!=filename:
        self.transrawimage.save (filename)
  def setupui (self):
    #Left menu bar
    left_f=tk.frame (self, height=self.framedispheight, width=self.leftframewidth)
    left_f.pack (side=tk.left)
    #Names and positions of various function buttons
    btnopen=tk.button (left_f, text="open image", command=self.openanddisplayimage)
    btnopen.place (y=25, x=30, width=300, height=self.btnheight)
    btntrans=tk.button (left_f, text="process image", command=self.ontransrawimagebtnclicked)
    btntrans.place (y=85, x=30, width=300, height=self.btnheight)
    l_selrect=tk.label (left_f, text="mouse selected")
    l_selrect.place (x=0, y=165, width=self.leftframewidth, height=self.labeltextheight)
    "" "List" ""
    self.l_box=tk.listbox (left_f) #create two list components
    self.l_box.place (x=0, y=165 + self.labeltextheight, width=self.leftframewidth, height=270)
    self.l_box.bind ("<listboxselect>", self.onrectlistboxselect)
    self.drawlistbox ()
    #Delete selected
    btndel=tk.button (left_f, text="delete selected", command=self.deleteselecteditemfromlistbox)
    btndel.place (y=460, x=30, width=300, height=self.btnheight)
    btnsave=tk.button (left_f, text="Save result", command=self.onsavetransrawimagebtnclicked)
    btnsave.place (y=550, x=30, width=300, height=self.btnheight)
    #Right image display bar
    right_f=tk.frame (self, height=self.framedispheight, width=self.imagedispwidth)
    right_f.pack (side=tk.right)
    l_rawt=tk.label (right_f, text="raw image")
    l_rawt.place (x=0, y=0, width=self.imagedispwidth, height=self.labeltextheight)
    self.image_l_raw=tk.label (right_f, relief="ridge")
    self.image_l_raw.place (x=0, y=self.labeltextheight, width=self.imagedispwidth, height=self.imagedispheight)
    self.image_l_raw.bind ("<button-1>", self.rawimagelabelclicked)
    l_transt=tk.label (right_f, text="Processed image")
    l_transt.place (x=0, y=self.labeltextheight + self.imagedispheight, width=self.imagedispwidth, height=self.labeltextheight)
    self.image_l_trans=tk.label (right_f, relief="ridge")
    self.image_l_trans.place (x=0, y=self.labeltextheight + self.imagedispheight + self.labeltextheight, width=self.imagedispwidth, height=self.imagedispheight)
if __name__ == "__main__":
  win=mainwin ()
  #Enter the message loop
  win.mainloop ()