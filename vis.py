import colorsys
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import cv2
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import matplotlib.patches as mpatches
import numpy as np

def add_bounding_box(out_boxes,out_classes,class_names, image):
    #print('Found {} boxes for {}'.format(len(out_boxes), 'img'))
    text_size=3
    thickness = (image.shape[0] + image.shape[1]) // 600
    fontScale=1
    ObjectsList = []
     # Generate colors for drawing bounding boxes.
    hsv_tuples = [(x / len(class_names), 1., 1.)
                    for x in range(len(class_names))]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    colors = list(
        map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)),colors))
    
    for i, c in reversed(list(enumerate(out_classes))):
        predicted_class = class_names[c]
        box = out_boxes[i]
        

        label = '{}'.format(predicted_class)
        #label = '{}'.format(predicted_class)
       

        left, top, right, bottom = box
        top = max(0, np.floor(top + 0.5).astype('int32'))
        left = max(0, np.floor(left + 0.5).astype('int32'))
        bottom = min(image.shape[0], np.floor(bottom + 0.5).astype('int32'))
        right = min(image.shape[1], np.floor(right + 0.5).astype('int32'))

        mid_h = (bottom-top)/2+top
        mid_v = (right-left)/2+left

        # put object rectangle
        cv2.rectangle(image, (left, top), (right, bottom), colors[c], thickness)

        # get text size
        (test_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, thickness/text_size, 1)

        # put text rectangle
        cv2.rectangle(image, (left, top), (left + test_width, top - text_height - baseline), colors[c], thickness=cv2.FILLED)

        # put text above rectangle
        cv2.putText(image, label, (left, top-2), cv2.FONT_HERSHEY_SIMPLEX, thickness/text_size, (0, 0, 0), 1)

        # add everything to list
        ObjectsList.append([top, left, bottom, right, mid_v, mid_h, label])

    return image, ObjectsList
def visualize(out_boxes,out_classes,class_names,image):

        #image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        original_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        original_image_color = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        
        r_image, ObjectsList = add_bounding_box(out_boxes,out_classes,class_names,original_image_color)
        return r_image, ObjectsList
def plot_image(image, boxes,class_labels):
    """Plots predicted bounding boxes on the image"""
    cmap = plt.get_cmap("tab20b")
    colors = [cmap(i) for i in np.linspace(0, 1, len(class_labels))]
    im = np.array(image)
    #print(im.shape)
    height, width, _ = im.shape

    # Create figure and axes
    fig, ax = plt.subplots(1)
    # Display the image
    ax.imshow(im)

    # box[0] is x midpoint, box[2] is width
    # box[1] is y midpoint, box[3] is height
    # Create a Rectangle patch
    my_handles=[]
    present_classes=[]
    for box in boxes:
        #print(len(box),box)
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
        ax.add_patch(rect)
        
        
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
            my_handles.append(mpatches.Patch(color=colors[int(class_pred)], label=class_labels[int(class_pred)]))
        present_classes.append(class_pred)
    
    ax.legend(handles=my_handles, loc=(1.04,0))
    
    plt.show()
