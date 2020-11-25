#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 15:27:13 2020

@author: fhall & eespinosa
"""

import pandas as pd
import requests
import json as json
from zipfile import ZipFile
from io import BytesIO
from urllib.request import urlopen


'''
PURPOSE:
    This data loader speeds up the data loading process for multiple runs
    by allowing a tidy data frame to be saved to the local /data subfolder and
    uploaded for each new run. If this file does not exist on the first run, the
    try-except clauses will pull in the needed files and save these to the /data
    subfolder for later use. '''


### LOOP OVER ALL FILES AND PULL FROM LOCAL /data
try:

    df_master = pd.read_csv('data/df_master.csv')
    consumption = pd.read_csv('data/consumption.csv')

### LOOP OVER ALL FILES AND PULL FROM GITHUB IF NOT LOCAL
except IOError:
    
    try: # load s1 data
        s1 = pd.read_csv('data/s1.csv')
        print('opened s1')
    except IOError:
        s1 = pd.read_csv('https://raw.githubusercontent.com/fabioyoohoo/global_consumption_convergence/main/data/s1.csv',
                         index_col=0)
        s1.rename(columns = {'a': 'country_a', 'b': 'country_b'}, inplace=True)
        s1.to_csv('data/s1.csv')

    try:
        s6 = pd.read_csv('data/s6.csv')
        print('opened s6')
    except IOError:
        url = 'https://github.com/fabioyoohoo/global_consumption_convergence/blob/main/data/s6.csv.zip?raw=true'
        z = urlopen(url)
        myzip = ZipFile(BytesIO(z.read())).extract('s6.csv')
        s6 = pd.read_csv(myzip, index_col = 0)
        s6.rename(columns = {'Country A': 'country_a', 'Country B': 'country_b', 'Year': 'year'}, inplace=True)
        s6.to_csv('data/s6.csv')

    try:
        s7 = pd.read_csv('data/s7.csv')
        print('opened s7')
    except IOError:
        url = 'https://raw.githubusercontent.com/fabioyoohoo/global_consumption_convergence/main/data/trade_groups.csv'
        s7 = pd.read_csv(url, engine = 'python', index_col = 0)
        s7.rename(columns = {"Country's numerical code": 'country_a', 
                             "Country's 3-letter code": 'iso_code', 
                             'Community label': 'community'}, inplace=True)
        s7.to_csv('data/s7.csv')
        
    try:
        consumption = pd.read_csv('data/energy.csv')
    except IOError:
        consumption = pd.read_csv('https://github.com/owid/co2-data/blob/master/owid-co2-data.csv?raw=true')
        consumption.to_csv('data/consumption.csv')
    
    ##########################################################################
    #### MERGE FILES TOGETHER
    
    # merge s1:s6 on country_a and country_b -> x
    # merge x:s7 on country_a
    # merge x:consumption on iso_code
    
    merge1 = pd.merge(s1,s6,how='left',on =['country_a', 'country_b', 'year'])
    merge2 = pd.merge(merge1,s7,how='left',on=['country_a','year'])
    df_master = pd.merge(merge2,consumption,how='left',on=['iso_code','year'])
    df_master = df_master.loc[df_master['iso_code'].notnull()]
    
    df_master.to_csv('data/df_master.csv')

