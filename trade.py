#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 18:20:20 2020

@author: fhall
"""
import math
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as sm


### DATA
from data_loader import df_consumption, joiner_official, df_master


# df_master= merge6
df_master.columns


paris= pd.read_csv('data/paris.csv')
paris= paris.rename(columns={'base year': 'year'})
paris.dropna(inplace=True)
paris['year']= paris['year'].astype(int)                  
df_paris = pd.merge(paris,df_consumption[['iso_code','year','consumption_co2']],'left',left_on=(['iso_code','year']),right_on=(['iso_code','year']))
df_paris= df_paris.rename(columns={'iso_code': 'iso_code_a'})
# df_paris['reduction high']= df_paris['reduction high'].str.rstrip('%').astype('float') / 100.0
# Compute emissions goal for the selected countries
df_paris['Emissions_goal']= df_paris['consumption_co2']*(1-df_paris['reduction high'])
df_paris['priority_group'] = 1

# Join df_master and paris data
df_master = df_master[(df_master.gdp.notnull())]
df_master['gdp']= df_master['gdp']/1000000 # GDP in millon dollars
df = pd.merge(df_master,df_paris[['iso_code_a','Emissions_goal','priority_group']],'left',on=['iso_code_a'])
df = df.loc[df.consumption_co2.notnull()]

# COLUMNS NEEDED:
# GDP/Cap
df['gdp_percap'] = df.apply(lambda row: row['gdp']*1000 / row['population'], axis=1)
# consumption-based emissions per capita
df.rename(columns = {'consumption_co2':'consumption'}, inplace=True)
df['consumption_percap'] = df['consumption']*1000000 / df['population']
df['consumption_goal'] = df['Emissions_goal']*1000000 / df['population']

# trade per capita
df['exports_percap']=df['exports']/df['population']
df['imports_percap']=df['imports']/df['population']

df['exportstot_percap']=df['exports_a']*1000/df['population']
df['importstot_percap']=df['imports_a']*1000/df['population']

# import_share
df['imports_share'] = df.apply(lambda row: row['imports'] / row['imports_a'], axis=1)

# Marginal propensity of external consumption or total Imports: M/GDP
df['Mg_ImportsTot'] = df['imports_a']/df['gdp']

# Marginal propensity of imports for each trade partner
df['MgM_bilateral'] = df['imports']*100/df['gdp']

# Growth variables
growth= df[['country_a', 'iso_code_a','year','gdp','gdp_percap','imports_a','importstot_percap','Mg_ImportsTot','consumption_percap','population']]
growth= growth.drop_duplicates(subset=['iso_code_a', 'year'], keep='last') #get aggregates by country-year

#compute variation rates of GDP, MgC_imports, and consumption_percap for each year
growth = growth[growth['year']>= 2000]
# compute lagged variables
growth['gdp_lag'] = growth.groupby(['iso_code_a'])['gdp_percap'].shift(1)
growth['MgM_lag'] = growth.groupby(['iso_code_a'])['Mg_ImportsTot'].shift(1)
growth['consump_lag'] = growth.groupby(['iso_code_a'])['consumption_percap'].shift(1)
growth = growth.loc[growth['gdp_lag'].notnull()]

# compute variation rates 
growth['gdp_var']= (growth['gdp_percap']- growth['gdp_lag'])/growth['gdp_lag']
growth['MgM_var']= (growth['Mg_ImportsTot']- growth['MgM_lag'])/growth['MgM_lag']
growth['consump_var']= (growth['consumption_percap']- growth['consump_lag'])/growth['consump_lag']


# Dataframe with growth rates  per country
#Take average growth rates per country
df_growth = growth[['iso_code_a','gdp_var','MgM_var','consump_var']].groupby(['iso_code_a']).agg({'gdp_var':'mean','MgM_var':'mean','consump_var':'mean'}).reset_index()


# Use growth dataframe to compute parameters for the model Consumption ~ B0+ B1*C_t-1 + B2*GDP + B3*Imports
# get list of countries
list_countries= growth['iso_code_a'].unique()

# Iterate over each country
dict_results={}
for country in list_countries.tolist():
    df_country= growth[growth['iso_code_a']== country]
    X= df_country[['consump_lag','gdp_percap','importstot_percap']]
    Y= df_country['consumption_percap']
    result = sm.ols(formula="Y ~ X", data=df_country, missing='drop').fit()
    dict_results.setdefault('iso_code_a',[]).append(country)
    dict_results.setdefault('beta0',[]).append(result.params[0]) # Intercept
    dict_results.setdefault('beta1',[]).append(result.params[1]) # Consumption Lag to account for autocorrelation
    dict_results.setdefault('beta2',[]).append(result.params[2]) # Mg propensity GDP
    dict_results.setdefault('beta3',[]).append(result.params[3]) # Mg propensity Imports

# Convert dictionary with parameters to dataframe
df_params= pd.DataFrame.from_dict(dict_results)

## Merge computed parameters in the main dataframe
df= pd.merge(df, df_growth, on=['iso_code_a'], how='inner') #add annual variation rates
df= pd.merge(df, df_params, on=['iso_code_a'], how='inner') #add annual variation rates

df['GDP-X']= (df['gdp_percap']-df['exportstot_percap'])

# Filter year 2000 
df2000= df[df['year']==2000]

# Dataframe at the country level to define node attributes
nodes= df2000.drop_duplicates(subset=['country_a'], keep='first')
nodes= nodes.round(3)
df2000= df2000.round(3)

# Paris agreement priority groups
nodes['priority_group']= nodes['priority_group'].replace(np.nan, 0)

# Classify countries in four groups by GDP
nodes= nodes.sort_values(by=['gdp_percap'], ascending=False).reset_index(drop=True)
nodes['index1']=nodes.index
def classif(r):
    if r< 20:
        m= '1'
    elif r>=20 and r<60:
        m= '2'
    elif r>=60 and r<100:
        m= '3'
    elif r>= 100:
        m= '4'
    return m
nodes['group'] = nodes.index1.apply(classif)

nodes.sort_values(by=['gdp_percap'], ascending=False).reset_index(drop=True)


nodes['priority_group'].value_counts()


## Paris agreement
nodes.groupby(['priority_group'])[['consumption_percap','consumption_goal']].agg('sum')


nodes[['iso_code_a','country_a','gdp_percap','gdp_var','consumption_percap']][nodes['iso_code_a']=='CHN']


def initialize():
    global G, nextg, pos
    # Create graph with edge attributes: Imports, parteners_consumption, and Imports growth rate= alpha
    G = nx.from_pandas_edgelist(df2000[['country_a','country_b','imports_percap','exports_percap','MgM_bilateral','MgM_var']], 'country_a', 'country_b', 
                                edge_attr=['imports_percap','exports_percap','MgM_bilateral','MgM_var'], create_using= nx.MultiDiGraph())
        # set graph layout
    pos = nx.spring_layout(G)
        # convert dataframe to dictionary of attributes
    node_attr = nodes[['country_a','exportstot_percap','importstot_percap','GDP-X','gdp_var','consumption_percap','beta0','beta1','beta2','beta3','priority_group']].set_index('country_a').to_dict('index')
    nx.set_node_attributes(G, node_attr)
    
    # remove imbalanced node
    G.remove_node(920)
    
    # Scenario where low priority decreases propensity to import in half
    #for i, j, k, weight in G.edges(data="weight", keys=True): 
        #if G.nodes[i]['priority_group']== 0:
            #G[i][j][0]['MgM_var']= -0.5
            
    
    nextg= G.copy()


def update():
    global G, nextg

    # Update GDP with GDP growth rate
    for i in G.nodes():
        try:
            nextg.nodes[i]['GDP_percap'] = (1+ G.nodes[i]['gdp_var'])* (G.nodes[i]['GDP-X'] + G.nodes[i]['exportstot_percap'])
        except:
            continue
        
    # Update GDP_percap without exports (logistic growth)
    
    for i in G.nodes():
        try:
            #if G.nodes[i]['priority_group']== 0:
            nextg.nodes[i]['GDP-X'] = (1+ (G.nodes[i]['gdp_var']*(1-(G.nodes[i]['GDP-X']/65))))* G.nodes[i]['GDP-X']
        except:
            continue
            
    
    # Update Propensity of Imports (bilateral imports)
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        
        nextg[i][j][0]['MgM_bilateral']= (1 + G.edges[i,j,0]['MgM_var'])* (G.edges[i,j,0]['MgM_bilateral'])


    
    # Update Imports variation at edge level
    
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        
        nextg[i][j][0]['imports_percap']= (nextg.edges[i,j,0]['MgM_bilateral']/100)* nextg.nodes[i]['GDP_percap']
    
        
    # Get total imports
    
    for i in nextg.nodes(): 
        nextg.nodes[i]['importstot_percap'] = nextg.out_degree(i,'imports_percap')
    
    # Update bilateral exports based on updated bilateral imports:
    
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        g= nextg[i][j][0]['imports_percap']
        for j, y, z, w in nextg.edges(data="weight", keys=True):
            if y == i:
                nextg[j][y][0]['exports_percap'] = g
            else:
                continue
     
    # Compute total exports
    for i in nextg.nodes(): 
        nextg.nodes[i]['exportstot_percap'] = nextg.out_degree(i,'exports_percap')
 
    
    # Compute consumption-based emissions at node level
    for i in nextg.nodes():
        try:
            nextg.nodes[i]['consumption_percap']= nextg.nodes[i]['beta0'] + nextg.nodes[i]['beta1']*G.nodes[i]['consumption_percap'] + nextg.nodes[i]['beta2']*nextg.nodes[i]['GDP_percap'] + nextg.nodes[i]['beta3']*nextg.nodes[i]['importstot_percap']   
        except:
            nextg.nodes[i]['consumption_percap']=0
            
        if nextg.nodes[i]['consumption_percap']<0:
            nextg.nodes[i]['consumption_percap']=0
    
            
    # Scenario where high priority applies clean technology beta2 is negative= average beta2 in the group
    #for i in nextg.nodes(): 
        #if nextg.nodes[i]['priority_group'] != 0:
            #nextg.nodes[i]['beta2']= -100
            
    # Scenario Reduce propensity rate variation
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        #if nextg.nodes[i]['priority_group']!= 0:
        nextg[i][j][0]['MgM_var']= -0.2
            
    
    # Scenario Degrowth for all countries "Reduce growth convergence!! or any growth"
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        if nextg.nodes[i]['gdp_var']> 0.01 : 
            nextg.nodes[i]['gdp_var']= 0.01
        elif nextg.nodes[i]['priority_group']== 0 and nextg.nodes[i]['gdp_var']<= 0.01 :
            nextg.nodes[i]['gdp_var']= -0.01
        
    G= nextg.copy()


def emissions_trend():
    global nextg
    high_income=0
    uppermiddle_income= 0
    lowermiddle_income= 0
    low_income= 0
    for i in nextg.nodes():
        if nextg.nodes[i]['group']=='1':
            high_income+= nextg.nodes[i]['consumption_percap']
        elif nextg.nodes[i]['group']=='2':
            uppermiddle_income+= nextg.nodes[i]['consumption_percap']
        elif nextg.nodes[i]['group']=='3':
            lowermiddle_income+= nextg.nodes[i]['consumption_percap']
        else:
            low_income+= nextg.nodes[i]['consumption_percap']
    return high_income, uppermiddle_income, lowermiddle_income, low_income


def priority_groups_trend():
    global nextg
    high_priority=0
    low_priority= 0

    for i in nextg.nodes():
        if nextg.nodes[i]['priority_group']==1.0 or nextg.nodes[i]['priority_group']== 2.0:
            high_priority+= nextg.nodes[i]['consumption_percap']
        elif nextg.nodes[i]['priority_group']==0:
            low_priority+= nextg.nodes[i]['consumption_percap']

    return high_priority, low_priority


N= 5
print('here')
initialize()
emissions_highprio=[]
emissions_lowprio=[]

for i in range(N):
    update()
    print(i)
    X,Y = priority_groups_trend() # Get consumption by groups at the end of period
    emissions_highprio.append(X) # array of total consumption for high priority countries
    emissions_lowprio.append(Y) # array of total consumption for low countries


plt.figure(figsize=(10,6))
plt.plot(range(N),[x / 35 for x in emissions_highprio][0:N], label='High priority countries')
plt.plot(range(N),[x / 81 for x in emissions_lowprio][0:N], label='Low priority countries')
plt.plot([0, N], [7, 7], 'r-', label='Emissions goal')


plt.xlabel('Time', fontsize=14)
plt.ylabel('Average consumption-based CO2 per capita', fontsize=14)
plt.legend(fontsize=10)


nodes[(nodes['priority_group']==1.0) | (nodes['priority_group']== 2.0) ].describe()


nodes[(nodes['priority_group']==0.0) ].describe()


def grouping_grapher(df): 
    # df = network_df 
    y = 'consumption_percap' 
    grouped = df[['time',y,'region']].groupby(['time','region']).agg({y:'sum'}).reset_index()

    # sns.lineplot(x="year", y="consumption_percap",hue="iso_code_a", data=growth[growth['region']=='Europe'])
    sns.lineplot(x='time', y=y,hue='region', data=grouped)