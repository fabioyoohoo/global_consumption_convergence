#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 15:27:13 2020

@author: fhall & eespinosa
"""

import pandas as pd
import requests
import json as json 

'''
PURPOSE: 
    This data loader speeds up the data loading process for multiple runs
    by allowing a tidy data frame to be saved to the local /data subfolder and 
    uploaded for each new run. If this file does not exist on the first run, the
    try-except clauses will pull in the needed files and save these to the /data
    subfolder for later use.
'''

### LOOP OVER ALL FILES AND PULL FROM LOCAL /data
try:

    dfex = pd.read_csv('data/dfex.csv')
    df = pd.read_csv('data/df_toy_model.csv')
   

### LOOP OVER ALL FILES AND PULL FROM GITHUB IF NOT LOCAL
except:
    
    try:
        df = pd.read_csv('data/df_toy_model.csv')
    except:
        df = pd.read_csv('https://raw.githubusercontent.com/fabioyoohoo/global_consumption_convergence/draft/toy%20model%20trade.csv')
        df.rename(columns= {'Country_A': 'country_A', 'Country_B': 'country_B','Partners_consump':'Partn_consump', 'Income_level': 'Group', 
                    'Convergence rate': 'Beta', 'Imports growth rate': 'Alpha'}, inplace=True)
        df.to_csv('data/df_toy_model.csv')
    
    
    try:
        s1 = pd.read_csv('data/s1.csv')
        print('opened s1')
    except:
        s1 = pd.read_csv("https://github.com/fabioyoohoo/global_consumption_convergence/blob/main/s6.csv.zip?raw=true",
                         compression='zip', header=0, sep=',', quotechar='"')
        s1.to_csv('data/s1.csv')
    
    
    try:
        s6 = pd.read_csv('data/s6.csv')
        print('opened s6')
    except:
        s6 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Table_S6.csv")
        s6.to_csv('data/s6.csv')
    
    
    try:
        s7 = pd.read_csv('data/s7.csv')
        print('opened s7')
    except:    
        s7 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Table_S7.dat", sep='  ', header = 1, engine = 'python')
        years = []
        for i in range(len(s7)):
            if s7.loc[i,"Country's numerical code"] > 1800:
                year = s7.loc[i,"Country's numerical code"]
            years.append(year)
        s7['year'] = years
        s7 = s7.dropna   ()
        s7.to_csv('data/s7.csv')
    
    
    try:
        dfConsumption = pd.read_csv('data/dfConsumption.csv')
    except:
        resp = requests.get("https://github.com/fabioyoohoo/global_consumption_convergence/blob/main/energy_consumption_btu.json?raw=true")    
        data_list = json.loads(resp.text)
        
        A= {'country':[],'descript':[], 'year':[], 'consumption':[] }
        DF=pd.DataFrame()
        for x in data_list:
            descrip = x['name']
            L = descrip.split(',')
            for y in x['data']:
                A['country'].append(L[1])
                A['descript'].append(L[0])
                year= y['date']
                val= y['value']
                A['year'].append(year)
                A['consumption'].append(val)
         
        df = pd.DataFrame.from_dict(A)
        replace_vals= {315532800000: '1980', 347155200000: '1981',378691200000: '1982',410227200000:'1983',441763200000:'1984',\
                   473385600000:'1985', 504921600000:'1986' ,536457600000:'1987' ,567993600000:'1988' ,599616000000:'1989' ,631152000000: '1990',\
                  662688000000:'1991' ,694224000000: '1992',725846400000:'1993' ,757382400000:'1994' ,788918400000:'1995' , 820454400000:'1996' ,\
                  852076800000:'1997' ,883612800000: '1998', 91514880000:'1999' , 946684800000:'2000' , 978307200000:'2001' , 1009843200000:'2002' , \
                  1041379200000:'2003' , 1072915200000:'2004' ,1104537600000:'2005' , 1136073600000:'2006' ,1167609600000:'2007' , 1199145600000:'2008' ,\
                  1230768000000:'2009' , 1262304000000:'2010' ,1293840000000:'2011' ,1325376000000: '2012', 1356998400000:'2013' , 1388534400000:'2014', \
                  1420070400000: '2015', 1451606400000:'2016' , 1483228800000:'2017' }
        df = df.replace({'year': replace_vals})
        df['consumption']=pd.to_numeric(df['consumption'],errors='coerce')
        df = df.rename({'country': 'a_name'}, axis=1)
        df['a_name']=df['a_name'].str.strip()
        df['a_name']=df['a_name'].replace('United States', 'United States of America' )
        df.to_csv('data/dfConsumption.csv')
        dfConsumption = df
        
    
    ##########################################################################
    #### MERGE FILES TOGETHER
    
    # format s1
    s1.columns = ['Ind','Country A', 'Country B', 'Year', 'a_name', 'b_name','imports','exports']
    dfex = s1.drop('Ind', 1)
    
    dfex = pd.merge(dfex, s6)
    dfex['Year']= dfex['Year'].astype(int)
    dfex= dfex.rename({'Year': 'year'}, axis=1)
    
    dfex = pd.merge(dfex, dfConsumption[(dfConsumption['descript']=='Total energy consumption')], on= ['a_name','year'], how='inner')
    
    # Get trade shares with partners 
    dfex['exports_tot']= dfex.groupby(['Country A','year'])['exports'].transform('sum')
    dfex['imports_tot']= dfex.groupby(['Country A','year'])['imports'].transform('sum')
    dfex['exp_share']= dfex['exports']/dfex['exports_tot']
    dfex['imp_share']= dfex['imports']/dfex['imports_tot']
    
    
    # Get energy consumption of partners
    dfConsumption = dfConsumption.rename({'a_name': 'b_name'}, axis=1)
    dfex = pd.merge(dfex, dfConsumption[(dfConsumption['descript']=='Total energy consumption')], on= ['b_name','year'], how='inner')
    
    dfex= dfex.rename({'consumption_x': 'consumption','consumption_y': 'consumption_partner'}, axis=1)
    dfex = dfex.drop(['descript_x','descript_y'], axis=1)
    dfex.to_csv('data/dfex.csv')





#### OLD CODE #####

# try:
#     s1 = pd.read_csv('data/s1.csv')
#     print('opened s1')
# except:
#     s1 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Database_S1.csv",index_col = False)
#     s1.columns = ['a','b','year','a_name','b_name','imports','exports']
#     s1.to_csv('data/s1.csv')

# try:
#     s3 = pd.read_csv('data/s3.csv')
#     print('opened s3')
# except:
#     s3 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Table_S3.dat", header=1,sep='\s\s+')
#     years = []
#     for i in range(len(s3)):
#         if s3.loc[i,"Country A"] > 1800:
#             year = s3.loc[i,"Country A"]
#         years.append(year)
#     s3['year'] = years
#     s3 = s3.dropna()
#     s3.to_csv('data/s3.csv')

# try:
#     s4 = pd.read_csv('data/s4.csv')
#     print('opened s4')
# except:
#     s4 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Table_S4.dat",sep='  ', index_col=False, header = 0, engine = 'python')
#     s4.to_csv('data/s4.csv')

# try:
#     s5 = pd.read_csv('data/s5.csv')
#     print('opened s5')
# except: 
#     s5 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Table_S5.dat",sep='  ', header = 1, engine = 'python')
#     years = []
#     for i in range(len(s5)):
#         if s5.loc[i,"Country's numerical code"] > 1800:
#             year = s5.loc[i,"Country's numerical code"]
#         years.append(year)
#     s5['year'] = years
#     s5 = s5.dropna()
#     s5.to_csv('data/s5.csv')

# try:
#     s6 = pd.read_csv('data/s6.csv')
#     print('opened s6')
# except:
#     s6 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Table_S6.csv")
#     s6.to_csv('data/s6.csv')

# try:
#     s7 = pd.read_csv('data/s7.csv')
#     print('opened s7')
# except:    
#     s7 = pd.read_csv("http://morfeo.ffn.ub.es/wta1870-2013/downloadable/Table_S7.dat", sep='  ', header = 1, engine = 'python')
#     years = []
#     for i in range(len(s7)):
#         if s7.loc[i,"Country's numerical code"] > 1800:
#             year = s7.loc[i,"Country's numerical code"]
#         years.append(year)
#     s7['year'] = years
#     s7 = s7.dropna   ()
#     s7.to_csv('data/s7.csv')


# try:
#     carbon = pd.read_csv('data/carbon.csv')
#     print('opened carbon file')
# except:
#     carbon = pd.read_csv('https://github.com/owid/co2-data/blob/master/owid-co2-data.csv?raw=true')
