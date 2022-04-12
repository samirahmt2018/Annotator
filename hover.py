import matplotlib.pyplot as plt
import pandas as pd
%matplotlib widget
# https://www.kaggle.com/ajaypalsinghlo/world-happiness-report-2021
df = pd.read_csv('/Users/sam/Downloads/archive (3)/world-happiness-report.csv')
df = df[df['year'] == 2020]
x_name = 'Healthy life expectancy at birth'
y_name = 'Freedom to make life choices'
tooltip_name = 'Country name'
x = df[x_name]
y = df[y_name]
tt = df[tooltip_name].values
plt.close('all')
fig, ax = plt.subplots(1, figsize=(12,6))
# plot and labels
sc = ax.scatter(x,y)
plt.xlabel(x_name)
plt.ylabel(y_name)
# cursor grid lines

# annotation
annot = ax.annotate("", xy=(0,0), xytext=(5,5),textcoords="offset points")
annot.set_visible(False)
# xy limits
def hover(event):
    # check if event was in the axis
    if event.inaxes == ax:
        # draw lines and make sure they're visible
        
        
        # get the points contained in the event
        cont, ind = sc.contains(event)
        print(cont,ind)
        
        annot.xy = (event.xdata, event.ydata)
        annot.set_text("annotated")
        annot.set_visible(True) 
        if cont:
            
            # change annotation position
            annot.xy = (event.xdata, event.ydata)
            # write the name of every point contained in the event
            annot.set_text("{}".format(', '.join([tt[n] for n in ind["ind"]])))
            annot.set_visible(True)    
        else:
            annot.set_visible(False)
    
fig.canvas.mpl_connect("motion_notify_event", hover)
plt.show()