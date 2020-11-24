#!/usr/bin/env python
# coding: utf-8


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
#from pandas.compat import StringIO
import random
import json


# ## Energy consumption data


with open('energy_consumption_btu.json') as f:
    data_list = json.loads(f.read())

# To organize important data in list of dictionaries
A= {'country':[],'descript':[], 'year':[], 'consumption':[] }
DF=pd.DataFrame()
for x in data_list:
    descrip= x['name']
    L= descrip.split(',')
    for y in x['data']:
        A['country'].append(L[1])
        A['descript'].append(L[0])
        year= y['date']
        val= y['value']
        A['year'].append(year)
        A['consumption'].append(val)        


df= pd.DataFrame.from_dict(A)
replace_vals= {315532800000: '1980', 347155200000: '1981',378691200000: '1982',410227200000:'1983',441763200000:'1984',               473385600000:'1985', 504921600000:'1986' ,536457600000:'1987' ,567993600000:'1988' ,599616000000:'1989' ,631152000000: '1990',              662688000000:'1991' ,694224000000: '1992',725846400000:'1993' ,757382400000:'1994' ,788918400000:'1995' , 820454400000:'1996' ,              852076800000:'1997' ,883612800000: '1998', 915148800000:'1999' , 946684800000:'2000' , 978307200000:'2001' , 1009843200000:'2002' ,               1041379200000:'2003' , 1072915200000:'2004' ,1104537600000:'2005' , 1136073600000:'2006' ,1167609600000:'2007' , 1199145600000:'2008' ,              1230768000000:'2009' , 1262304000000:'2010' ,1293840000000:'2011' ,1325376000000: '2012', 1356998400000:'2013' , 1388534400000:'2014',               1420070400000: '2015', 1451606400000:'2016' , 1483228800000:'2017' }
df=df.replace({'year': replace_vals})
df['consumption']=pd.to_numeric(df['consumption'],errors='coerce')
df= df.rename({'country': 'a_name'}, axis=1)
df['a_name']=df['a_name'].str.strip()
df['a_name']=df['a_name'].replace('United States', 'United States of America' )
df



df['a_name'].unique()


# ## Trade data



dfex= pd.read_csv('data/Database_S1.csv')
dfex.columns=['Ind','Country A', 'Country B', 'Year', 'a_name', 'b_name','imports','exports']
dfex = dfex.drop('Ind', 1)



# Complete bilateral trade data
dfex2= dfex
dfex2.columns=['Country B', 'Country A', 'Year', 'b_name', 'a_name','exports','imports']
dfex= dfex.append(dfex2, ignore_index=True)




dfex.columns=['Country A', 'Country B', 'Year', 'a_name', 'b_name','imports','exports']
dfex= dfex.drop_duplicates(subset=['Country A', 'Country B', 'Year'], keep= 'first')
dfex['Year']= dfex['Year'].astype(str)
dfex= dfex.rename({'Year': 'year'}, axis=1)
dfex





# Merge trade data with energy consumption
dfex= pd.merge(dfex, df[(df['descript']=='Total energy consumption')], on= ['a_name','year'], how='inner')





# Get energy consumption of trade partners
df= df.rename({'a_name': 'b_name'}, axis=1)
dfex= pd.merge(dfex, df[(df['descript']=='Total energy consumption')], on= ['b_name','year'], how='inner')





dfex= dfex.rename({'consumption_x': 'consumption','consumption_y': 'partn_consump'}, axis=1)
dfex = dfex.drop(['descript_x','descript_y'], axis=1)





# Get trade shares with partners 
dfex['exports_tot']= dfex.groupby(['Country A','year'])['exports'].transform('sum')
dfex['imports_tot']= dfex.groupby(['Country A','year'])['imports'].transform('sum')
dfex['exp_share']= dfex['exports']/dfex['exports_tot']
dfex['imp_share']= dfex['imports']/dfex['imports_tot']


# ### GDP data






