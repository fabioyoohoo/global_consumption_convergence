#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 15:27:13 2020

@author: fhall & eespinosa
"""

import pandas as pd


'''
PURPOSE:
    This data loader speeds up the data loading process for multiple runs
    by allowing a tidy data frame to be saved to the local /data subfolder and
    uploaded for each new run. If this file does not exist on the first run, the
    try-except clauses will pull in the needed files and save these to the /data
    subfolder for later use. '''


### LOOP OVER ALL FILES AND PULL FROM LOCAL /data
try:
    
    df_master = pd.read_csv('data/df_master.csv',index_col = 0)
    df_consumption = pd.read_csv('data/df_consumption.csv',index_col = 0)
    joiner_official = pd.read_csv('data/joiner_official.csv', index_col = 0)
    df_paris = pd.read_csv('data/df_paris.csv',index_col = 0)
    
    print('files loaded successfully')
    
### LOOP OVER ALL FILES AND PULL FROM GITHUB IF NOT LOCAL
except IOError:

    
    try: # load s1 data
        s1 = pd.read_csv('data/s1.csv',index_col=0)
        print('opened s1')
    except IOError:
        s1 = pd.read_csv('https://raw.githubusercontent.com/fabioyoohoo/global_consumption_convergence/main/data/s1.csv',
                         index_col=0)
        s1.rename(columns = {'a': 'country_a', 'b': 'country_b'}, inplace=True)
        s1.to_csv('data/s1.csv')
    
    try:
        consumption = pd.read_csv('data/consumption.csv', index_col=0)
        print('opened consumption')
    except IOError:
        consumption = pd.read_csv('https://github.com/owid/co2-data/blob/master/owid-co2-data.csv?raw=true')
        consumption = consumption.loc[consumption.iso_code.notnull()]
        consumption.to_csv('data/consumption.csv')
    
    
    try:
        gdp = pd.read_csv('data/gdp.csv', index_col=0)
        print('opened gdp')
    except IOError:
        gdp = pd.read_csv('https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv')
        gdp.drop(['Country Name'],axis=1,inplace=True)
        gdp.rename(columns = {'Country Code':'iso_code','Year':'year','Value':'value'}, inplace=True)
        gdp.to_csv('data/gdp.csv')
        
        
    try:
        joiner_official = pd.read_csv('data/joiner_official.csv', index_col = 0)
        print('opened joiner')
    except IOError:
        joiner_official = pd.read_csv('https://raw.githubusercontent.com/fabioyoohoo/global_consumption_convergence/main/data/joiner_official.csv')
        joiner_official.drop(['a_name'],axis=1,inplace=True)
        joiner_official.to_csv('data/joiner_official.csv')
    
    
    try:
        paris = pd.read_csv('data/paris.csv', index_col = 0)
        print('opened paris')
    except IOError:
        # pull from github
        paris = pd.read_csv('https://raw.githubusercontent.com/fabioyoohoo/global_consumption_convergence/main/data/paris.csv')
        paris.to_csv('data/paris.csv')
        
    
    try:
        regions = pd.read_csv('data/regions.csv', index_col=0)
        print('opened regions')
    except:
        regions = pd.read_csv('https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv')
        location = pd.read_csv('https://gist.githubusercontent.com/tadast/8827699/raw/f5cac3d42d16b78348610fc4ec301e9234f82821/countries_codes_and_coordinates.csv')
        
        location = location[['Alpha-3 code','Latitude (average)','Longitude (average)']]
        location = location.rename({'Alpha-3 code':'iso_code_a','Latitude (average)':'lat','Longitude (average)':'lon'},axis=1)
        location['iso_code_a'] = location['iso_code_a'].str.replace('"','')
        location['iso_code_a'] = location['iso_code_a'].str.replace(' ','')
        location['lat'] = location['lat'].str.replace('"','').astype('float')
        location['lon'] = location['lon'].str.replace('"','').astype('float')
        
        regions = regions.rename({'alpha-3':'iso_code_a'},axis=1)
        regions = regions[['iso_code_a','region','sub-region','region-code','sub-region-code']]
        
        region = pd.merge(regions,location,'left',on=['iso_code_a'])
        regions.to_csv('data/regions.csv')
        
        
    ##########################################################################
    #### MERGE FILES TOGETHER
    
    consumption = pd.merge(consumption,gdp,'left',on=['iso_code','year'])
    consumption['gdp'].fillna(consumption['value'],inplace=True)
    df_consumption = consumption[['iso_code','year','co2','consumption_co2','population','gdp']]
    df_consumption.to_csv('data/df_consumption.csv')
    
    df_consumption_a = df_consumption.rename({'iso_code':'iso_code_a'},axis=1)
    df_consumption_b = df_consumption.rename({'iso_code':'iso_code_b','co2':'co2_b','consumption_co2':'consumption_co2_b',
                                              'population':'population_b','gdp':'gdp_b'},axis=1)
    
    joiner_b = joiner_official.rename({'country_a':'country_b'},axis=1)
    
    merge1 = pd.merge(s1,joiner_official,how='left',on=['country_a'])
    merge2 = pd.merge(merge1, joiner_b,how='left',on=['country_b'])
    merge2 = merge2.rename({'iso_code_x':'iso_code_a','iso_code_y':'iso_code_b'},axis=1)
    merge2 = merge2.loc[merge2['iso_code_a'].notnull()]
    merge2 = merge2.loc[merge2['iso_code_b'].notnull()]
    
    
    # merge df_master and consumption
    merge3 = pd.merge(merge2,df_consumption_a, 'left',on = ['iso_code_a','year'])
    merge4 = pd.merge(merge3,df_consumption_b, 'left',on = ['iso_code_b','year'])
    
    
    merge4 = merge4.loc[merge4.consumption_co2.notnull()]
    merge4 = merge4.loc[merge4.consumption_co2_b.notnull()]
    
    # compute total imports and exports
    country_a = merge4[['country_a','year','imports','exports']].groupby(['country_a','year']).agg({'imports':'sum','exports':'sum'}).reset_index()
    country_a.rename(columns = {'imports':'imports_a','exports':'exports_a'}, inplace=True)
    
    country_b = merge4[['country_b','year','imports','exports']].groupby(['country_b','year']).agg({'imports':'sum','exports':'sum'}).reset_index()
    country_b.rename(columns = {'imports':'imports_b','exports':'exports_b'}, inplace=True)    
    
    
    merge5 = pd.merge(merge4,country_a, 'left', on = ['country_a','year'])
    merge6 = pd.merge(merge5,country_b, 'left', on = ['country_b','year'])
    merge7 = pd.merge(merge6,regions,'left',on=['iso_code_a'])
    
    # save df_master
    merge7.to_csv('data/df_master.csv')
    

    # PARIS - note Japan's target is set on 2013 emissions levels...
    polution = df_consumption[['iso_code','year','consumption_co2']]
    polution_base = polution[(polution['year']== 1990) | ((polution['year']== 2005) & 
                                                     ((polution['iso_code']=='CHN') | 
                                                      (polution['iso_code']=='USA') | 
                                                      (polution['iso_code']=='BRA') | 
                                                      (polution['iso_code']=='IND') |                 
                                                      (polution['iso_code']=='CAN') | 
                                                      (polution['iso_code']=='AUS'))) | 
                        ((polution['year']== 2013) & (polution['iso_code']=='JPN'))]
    polution_base = polution_base.drop(['year'],axis=1)
    polution_base.rename(columns = {'consumption_co2':'consumption_co2_base'},inplace=True)
    
    df_paris = pd.merge(paris,polution_base,'left',on=['iso_code'])
    df_paris['emissions_goal'] = df_paris['consumption_co2_base']*(1-df_paris['reduction high'])
    # df_paris = pd.merge(df_paris,polution,'left',on=['iso_code','year'])
    # df_paris['cagr'] = df_paris.apply(lambda row: 
    #                           ((row['consumption_co2_x'] * (1 - row['reduction high'])) 
    #                            / row['consumption_co2_y'])**(1/(row['target year']-2013))-1, axis=1)
    df_paris.dropna(inplace=True)
    df_paris['base year'] = df_paris['base year'].astype(int)
    df_paris['target year'] = df_paris['target year'].astype(int)
    df_paris.rename(columns = {'iso_code':'iso_code_a'},inplace=True)
        
    df_paris.to_csv('data/df_paris.csv')
