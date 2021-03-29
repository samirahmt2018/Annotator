import tkinter as tk
from PIL import Image, ImageTk
def donothing():
   filewin = Toplevel(root)
   button = Button(filewin, text="Do nothing button")
   button.pack()
def on_resize(event):
    global rescaled_img
    global photo

    #print('[DEBUG] on_resize:', event.widget)

    # resize only when root window changes size
    if str(event.widget) == '.':
        # generate new image
        width  = event.width//2 # -2  # -2*border
        height = event.height   # -2  # -2*border
        rescaled_img = original_img.resize((width, height), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(rescaled_img)

        # replace images in labels
        label_left['image'] = photo
        label_right['image'] = photo

# ---- main ---

# resize at start
original_img = Image.open('M13.jpg')
rescale = 0.4
width = int(rescale * original_img.width)
height = int(rescale * original_img.height)
rescaled_img = original_img.resize((width, height), Image.ANTIALIAS)


root = tk.Tk()
menubar = tk.Menu(root)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="New", command=donothing)
filemenu.add_command(label="Open", command=donothing)
filemenu.add_command(label="Save", command=donothing)
filemenu.add_command(label="Save as...", command=donothing)
filemenu.add_command(label="Close", command=donothing)

filemenu.add_separator()

filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)
editmenu = tk.Menu(menubar, tearoff=0)
editmenu.add_command(label="Undo", command=donothing)
editmenu.add_separator()

editmenu.add_command(label="Cut", command=donothing)
editmenu.add_command(label="Copy", command=donothing)
editmenu.add_command(label="Paste", command=donothing)
editmenu.add_command(label="Delete", command=donothing)
editmenu.add_command(label="Select All", command=donothing)

menubar.add_cascade(label="Edit", menu=editmenu)
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help Index", command=donothing)
helpmenu.add_command(label="About...", command=donothing)
menubar.add_cascade(label="Help", menu=helpmenu)

photo = ImageTk.PhotoImage(rescaled_img)

label_left = tk.Label(root, image=photo, border=0) # if border > 0 then you have to use `-2*border` in on_resize
label_left.pack(side='left', fill='both', expand=True)

label_right = tk.Label(root, image=photo, border=0) # if border > 0 then you have to use `-2*border` in on_resize
label_right.pack(side='left', fill='both', expand=True)

# resize when window changed size
root.bind('<Configure>', on_resize)
root.config(menu=menubar)
root.mainloop()