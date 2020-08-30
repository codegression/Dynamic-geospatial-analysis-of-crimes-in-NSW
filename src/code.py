#!/usr/bin/env python
# coding: utf-8

# # Dynamic geospatial analysis of crimes in NSW

# Python code to perform dynamic geospatial analysis of crimes based on data from the NSW Bureau of Crime Statistics and Research.

# # Loading libraries

# Let's load relevant Python libraries.

# In[1]:


import numpy as np 
import pandas as pd 
from IPython.display import display, Image, Markdown
import matplotlib.pyplot as plt 
import matplotlib as mpl
import geopandas as gpd
import os
import shutil
import imageio
import warnings
warnings.filterwarnings("ignore")
#pd.set_option('display.max_rows', 500)
#pd.set_option('display.max_columns', 500)
#pd.set_option('display.width', 1000)


# # Loading data

# The dataset was acquired from https://www.bocsar.nsw.gov.au/Pages/bocsar_datasets/Datasets-.aspxNSW.

# In[2]:


data = pd.read_excel('LGA_trends.xlsx', skiprows=3)


# # Data cleaning

# In[3]:


data.shape


# The dataset has 8133 rows and 10 columns.

# In[4]:


data.head(10)


# In[5]:


data.tail(15)


# The original Excel file contains a footer which got loaded into the dataset. Rows # 8122 and above need to be removed.

# In[6]:


data = data[:8122]
data.tail()


# Lets analyze unique values for 'Local Government Area'

# In[7]:


countLGA = data['Local Government Area'].value_counts(dropna =False)

print('Unique values =', len(countLGA))
print()

for i in range(len(countLGA)):
    print(countLGA.index[i], ":\t", countLGA[i])


# In[8]:


countOffence = data['Offence type'].value_counts(dropna =False)

print('Unique values =', len(countOffence))
print()

for i in range(len(countOffence)):
    print(countOffence.index[i], ":\t", countOffence[i])


# No missing values in the above two columns. 

# Let's rename the first two columns for brevity and delete the last 3 columns which are not necessary

# In[9]:


data.rename(columns={'Local Government Area': 'LGA'}, inplace=True)
data.rename(columns={'Offence type': 'Offence'}, inplace=True)
data = data.iloc[:, :7]


# Let's just get rid of * in 'Murder' and 'Manslaughter'

# In[10]:


data.Offence.replace("Murder *", "Murder", inplace=True)
data.Offence.replace("Manslaughter *", "Manslaughter", inplace=True)


# In[11]:


data.head()


# Let's check for missing values

# In[12]:


data[data.isna().any(axis=1)]


# There are no missing values.

# In[13]:


data.tail()


# Let's remove rows with LGA = 'In Custody' since we are only interested in geospatial information.

# In[14]:


data = data[data.LGA!='In Custody']


# In[15]:


data.tail()


# In[16]:


data.describe()


# # Preparing map data

# I am going to import data of NSW Local Government Areas from the official Australian Government website https://data.gov.au/dataset/ds-dga-f6a00643-1842-48cd-9c2f-df23a3a1dc1e/details.

# In[17]:


LGA = gpd.read_file('geodata/NSW_LGA_POLYGON_shp.shp')


# In[18]:


LGA.columns


# In[19]:


LGA.head(50)


# We are only interested in two columns: 'NSW_LGA__3' and 'geometry'. Lets drop the rest
# 

# In[20]:


LGA = LGA.loc[:, ['NSW_LGA__3', 'geometry']]


# Let's rename the 'NSW_LGA__3' column.

# In[21]:


LGA.rename(columns={'NSW_LGA__3': 'Name'}, inplace=True)


# In[22]:


LGA.Name = LGA.Name.str.title()


# In[23]:


LGA.Name.unique()


# In[24]:


LGA.head()


# Let's make sure all the LGA's in the original dataset have poloygons in the geo dataset.

# In[25]:


lga_geo = list(LGA.Name.unique())
for lga in data.LGA.unique():
    if lga not in lga_geo:
        print(lga, "is not in the geo data")


# There are some LGAs in the original dataset that do not exist in the geo dataset. This is because of spelling differences. Let's correct them.

# In[26]:


LGA.Name.replace("Cootamundra-Gundagai Regional", "Cootamundra-Gundagai", inplace=True)
LGA.Name.replace("Glen Innes Severn Shire", "Glen Innes Severn", inplace=True)
LGA.Name.replace("Greater Hume", "Greater Hume Shire", inplace=True)
LGA.Name.replace("Ku-Ring-Gai", "Ku-ring-gai", inplace=True)
LGA.Name.replace("Unincorporated", "Unincorporated Far West", inplace=True)
LGA.Name.replace("Upper Hunter", "Upper Hunter Shire", inplace=True)
LGA.Name.replace("Warrumbungle", "Warrumbungle Shire", inplace=True)


# "Lord Howe Island" is really not in the geo dataset. Let's just exclude rows that contain "Lord Howe Island" in the original dataset.

# In[27]:


data = data[data.LGA!='Lord Howe Island']


# We are now ready for analysis

# In[28]:


data.head()


# In[38]:


LGA.head()


# In[37]:


places = data.LGA.unique()
lgas = LGA.Name.unique()
for lga in lgas:
    if lga not in places:
        print(lga)


# # Constructing a mapping function

# To draw a heat map, we need to join 'LGA' and 'data' dataframes. Let's draw 3 levels of zoom levels: 
# 
# 1. Covering the entire NSW
# 2. Zooming into the 'Greater Metropolitan Area'
# 3. Zooming into the 'Sydney Metropolitan Area'
# 
# **Note that the the boundaries of 'Greater Metropolitan Area' and 'Sydney Metropolitan Area' are not official**. These are just arbitrary zoom levels used in this analysis.

# In[30]:


def drawMap(offence_type, colormap='jet', edgecolor='black', labelcolor='white', period='Apr 2019 - Mar 2020'):    
    crime_data = []
    
    if (offence_type=='Total'):
        crime_data = data.groupby('LGA').agg('sum')
        print('There is a total of', int(crime_data[period].sum()), "cases in the entire NSW from " + period.replace('-', 'to') + '.')
    else:
        display(Markdown("# Analysis of '" + offence_type + "'"))       
        crime_data = data[data.Offence==offence_type]
        print('There is a total of', int(crime_data[period].sum()), "'" + offence_type + "' cases in the entire NSW from " + period.replace('-', 'to') + '.')
    merged_data = LGA.merge(crime_data, left_on='Name', right_on='LGA', how='left')    
    
    
    print()
    display(Markdown("### Entire NSW"))
    
    ax = merged_data.plot(cmap=colormap, column=period,
                   linewidth=1, edgecolor=edgecolor,                   
                   legend=True, figsize=(35,15))
    ax.set_axis_off()
    ax.set_xlim(140.5, 154)
    ax.set_ylim(-38, -28)
    
    plt.title(offence_type + " from " + period.replace('-', 'to'), fontsize=22)
    plt.show()
    print()
    
    merged_data['coords'] = merged_data['geometry'].apply(lambda x: x.representative_point().coords[:])
    merged_data['coords'] = [coords[0] for coords in merged_data['coords']]
    
    ###############################################################
    display(Markdown("### Greater Metropolitan Area"))
    x_min = 150.50
    x_max = 151.50
    y_min = -34.25
    y_max = -33.25
    
    values=[]
    for i, row in merged_data.iterrows():
        x_ = row['coords'][0]
        y_ = row['coords'][1]
        if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
            values.append(row[period])
            
    if (offence_type=='Total'):
        print('There is a total of', int(sum(values)), "cases from " + period.replace('-', 'to') + ".")
    else:
        print('There is a total of', int(sum(values)), "'" + offence_type + "' cases from " + period.replace('-', 'to') + '.')    
    
    ax = merged_data.plot(cmap=colormap, column=period,
            linewidth=1, edgecolor=edgecolor,
            legend=True, figsize=(35,15))
    
    ax.set_axis_off()
   
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

   
    
    for i, row in merged_data.iterrows():
        x_ = row['coords'][0]
        y_ = row['coords'][1]
    
        if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
            if row['Name']!='Unincorporated Far West':
                if row[period] > max(values) * 0.8:
                    if labelcolor=='white':
                        plt.annotate(s=row['Name'], fontsize=12, color='black', xy=row['coords'], horizontalalignment='center')  
                    else:
                        plt.annotate(s=row['Name'], fontsize=12, color='white', xy=row['coords'], horizontalalignment='center')
                else:
                    plt.annotate(s=row['Name'], fontsize=12, color=labelcolor, xy=row['coords'], horizontalalignment='center')               
    plt.title(offence_type + " from " + period.replace('-', 'to'), fontsize=18)                
    plt.show()   
   
    print()
    
    #############################################################
    display(Markdown("### Sydney Metropolitan Area"))
    x_min = 150.95
    x_max = 151.3
    y_min = -34.0
    y_max = -33.6
    
    values=[]
    for i, row in merged_data.iterrows():
        x_ = row['coords'][0]
        y_ = row['coords'][1]
        if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
            values.append(row[period])
            
    if (offence_type=='Total'):
        print('There is a total of', int(sum(values)), "cases in the above regions from " + period.replace('-', 'to') + '.')
    else:
        print('There is a total of', int(sum(values)), "'" + offence_type + "' cases in the above regions from " + period.replace('-', 'to') + '.')
        
    
    ax = merged_data.plot(cmap=colormap, column=period,
            linewidth=1, edgecolor=edgecolor,
            legend=True, figsize=(18,16))
    ax.set_axis_off()
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    print()
    
    
            
    for i, row in merged_data.iterrows():
        x_ = row['coords'][0]
        y_ = row['coords'][1]
    
        if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
             if row['Name']!='Unincorporated Far West':
                if row[period] > max(values) * 0.8:
                    if labelcolor=='white':
                        plt.annotate(s=row['Name'], fontsize=12, color='black', xy=row['coords'], horizontalalignment='center')  
                    else:
                        plt.annotate(s=row['Name'], fontsize=12, color='white', xy=row['coords'], horizontalalignment='center')
                else:
                    plt.annotate(s=row['Name'], fontsize=12, color=labelcolor, xy=row['coords'], horizontalalignment='center')
    
    plt.title(offence_type + " from " + period.replace('-', 'to'), fontsize=18)
    plt.show()
   
    print()
    
   
    crimes = [int(crime_data[period].sum()), int(sum(values))]   
    plt.pie(crimes, labels=['Entire NSW', 'Sydney Metropolitan Area'], autopct='%1.0f%%', pctdistance=0.8)  
    center=plt.Circle( (0,0), 0.6, color='white')
    p=plt.gcf()
    p.gca().add_artist(center)
    plt.show()    
    print()
    print()


# In[60]:


def drawAnimatedMap(offence_type, colormap='jet', edgecolor='black', labelcolor='white'):    
    crime_data = []
    periods = data.columns[-5:]
   
    
    if (offence_type=='Total'):
        crime_data = data.groupby('LGA').agg('sum')
        print('There is a total of', int(crime_data[periods[-1]].sum()), "cases in the entire NSW from " + periods[-1].replace('-', 'to') + '.')
    else:
        display(Markdown("# Analysis of '" + offence_type + "'"))       
        crime_data = data[data.Offence==offence_type]
        print('There is a total of', int(crime_data[periods[-1]].sum()), "'" + offence_type + "' cases in the entire NSW from " + periods[-1].replace('-', 'to') + '.')
    merged_data = LGA.merge(crime_data, left_on='Name', right_on='LGA', how='left')    
    vmax = max(list(crime_data.max(axis=0))[2:])
    
    
    print()
    display(Markdown("### Entire NSW"))
    plt.ioff() ##### Turn off plotting
    if not os.path.exists('temp'):
        os.mkdir('temp')
    images = []
    for period in periods:
        ax = merged_data.plot(cmap=colormap, column=period,
                       linewidth=1, edgecolor=edgecolor,     
                       vmax=vmax,
                       legend=True, figsize=(35,15))
        ax.set_axis_off()
        ax.set_xlim(140.5, 154)
        ax.set_ylim(-38, -28)


        plt.title(offence_type + " from " + period.replace('-', 'to'), fontsize=22)
        plt.savefig('temp/' + period + '.png', bbox_inches = 'tight', pad_inches = 0.1)
        plt.close()               
        images.append(imageio.imread('temp/' + period + '.png'))
        
    imageio.mimsave('temp/merged.gif', images, duration=0.5)
    display(Image(filename='temp/merged.gif'))
    print()
    
    merged_data['coords'] = merged_data['geometry'].apply(lambda x: x.representative_point().coords[:])
    merged_data['coords'] = [coords[0] for coords in merged_data['coords']]
    
    ###############################################################
    display(Markdown("### Greater Metropolitan Area"))
    x_min = 150.50
    x_max = 151.50
    y_min = -34.25
    y_max = -33.25
    
    values=[]
    for i, row in merged_data.iterrows():
        x_ = row['coords'][0]
        y_ = row['coords'][1]
        if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
            values.append(row[periods[-1]])
            
    if (offence_type=='Total'):
        print('There is a total of', int(sum(values)), "cases from " + periods[-1].replace('-', 'to') + ".")
    else:
        print('There is a total of', int(sum(values)), "'" + offence_type + "' cases from " + periods[-1].replace('-', 'to') + '.')    
    
    images = []
    for period in periods:
        ax = merged_data.plot(cmap=colormap, column=period,
                linewidth=1, edgecolor=edgecolor,
                vmax=vmax,
                legend=True, figsize=(35,15))

        ax.set_axis_off()

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)



        for i, row in merged_data.iterrows():
            x_ = row['coords'][0]
            y_ = row['coords'][1]

            if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
                if row['Name']!='Unincorporated Far West':
                    if row[period] > max(values) * 0.8:
                        if labelcolor=='white':
                            plt.annotate(s=row['Name'], fontsize=12, color='black', xy=row['coords'], horizontalalignment='center')  
                        else:
                            plt.annotate(s=row['Name'], fontsize=12, color='white', xy=row['coords'], horizontalalignment='center')
                    else:
                        plt.annotate(s=row['Name'], fontsize=12, color=labelcolor, xy=row['coords'], horizontalalignment='center')               
        plt.title(offence_type + " from " + period.replace('-', 'to'), fontsize=18)                
        plt.savefig('temp/' + period + '.png',  bbox_inches = 'tight', pad_inches = 0.1)
        plt.close()               
        images.append(imageio.imread('temp/' + period + '.png'))
        
    imageio.mimsave('temp/merged.gif', images, duration=0.5)
    display(Image(filename='temp/merged.gif'))
   
    print()
    
    #############################################################
    display(Markdown("### Sydney Metropolitan Area"))
    x_min = 150.95
    x_max = 151.3
    y_min = -34.0
    y_max = -33.6
    
    values=[]
    for i, row in merged_data.iterrows():
        x_ = row['coords'][0]
        y_ = row['coords'][1]
        if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
            values.append(row[periods[-1]])
            
    if (offence_type=='Total'):
        print('There is a total of', int(sum(values)), "cases in the above regions from " + periods[-1].replace('-', 'to') + '.')
    else:
        print('There is a total of', int(sum(values)), "'" + offence_type + "' cases in the above regions from " + periods[-1].replace('-', 'to') + '.')
        
    images = []
    for period in periods:
        ax = merged_data.plot(cmap=colormap, column=period,
                linewidth=1, edgecolor=edgecolor,
                vmax=vmax,
                legend=True, figsize=(18,16))
        ax.set_axis_off()

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        print()



        for i, row in merged_data.iterrows():
            x_ = row['coords'][0]
            y_ = row['coords'][1]

            if x_ > x_min and x_ < x_max and y_ > y_min and y_ < y_max:
                 if row['Name']!='Unincorporated Far West':
                    if row[period] > max(values) * 0.8:
                        if labelcolor=='white':
                            plt.annotate(s=row['Name'], fontsize=12, color='black', xy=row['coords'], horizontalalignment='center')  
                        else:
                            plt.annotate(s=row['Name'], fontsize=12, color='white', xy=row['coords'], horizontalalignment='center')
                    else:
                        plt.annotate(s=row['Name'], fontsize=12, color=labelcolor, xy=row['coords'], horizontalalignment='center')

        plt.title(offence_type + " from " + period.replace('-', 'to'), fontsize=18) 
        
        plt.savefig('temp/' + period + '.png', bbox_inches = 'tight', pad_inches = 0.1)
        plt.close()               
        images.append(imageio.imread('temp/' + period + '.png'))
        
    imageio.mimsave('temp/merged.gif', images, duration=0.5)
    display(Image(filename='temp/merged.gif'))
    print()
    
   
    crimes = [int(crime_data[periods[-1]].sum()), int(sum(values))]   
    plt.pie(crimes, labels=['Entire NSW', 'Sydney Metropolitan Area'], autopct='%1.0f%%', pctdistance=0.8)  
    center=plt.Circle( (0,0), 0.6, color='white')
    p=plt.gcf()
    p.gca().add_artist(center)
    plt.show()    
    shutil.rmtree('temp')
    print()
    print()
   


# In[62]:


for offence in data.Offence.unique():
    drawAnimatedMap(offence,  'OrRd', 'black', 'black')
    #drawMap(offence, 'OrRd', 'black', 'black')


# # Analysis of total crimes
# 

# In[61]:


drawAnimatedMap('Total', 'OrRd', 'black', 'black')


# In[63]:


drawMap('Total', 'OrRd', 'black', 'black')


# In[ ]:




