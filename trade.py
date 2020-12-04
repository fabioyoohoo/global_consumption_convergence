#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 17:56:12 2020

@author: fhall & eespinosa
"""
import math
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as sm



### DATA
from data_loader import df_consumption, joiner_official, df_master, df_paris

df_master.columns


# Paris agreement data
# paris= pd.read_csv('data/paris.csv')
# polution = df_consumption[['iso_code','year','consumption_co2']]

# # Select countries and consumption levels according to Paris agreement
# polution = polution[(polution['year']== 1990) | ((polution['year']== 2005) & ((polution['iso_code']=='CHN') | (polution['iso_code']=='USA') | (polution['iso_code']=='BRA') | (polution['iso_code']=='IND') |                 (polution['iso_code']=='CAN') | (polution['iso_code']=='AUS'))) | ((polution['year']== 2013) &                 (polution['iso_code']=='JPN'))]

# df_paris = pd.merge(paris,polution,'left',left_on=('iso_code'),right_on=('iso_code'))
# df_paris['reduction high']= df_paris['reduction high'].str.rstrip('%').astype('float') / 100.0

# # Compute emissions goal for the selected countries
# df_paris['Emissions_goal']= df_paris['consumption_co2']*(1-df_paris['reduction high'])
# df_paris.dropna(inplace=True)
# df_paris['year']= df_paris['year'].astype(int)
# df_paris


## back to df_master
df_master = df_master[(df_master.gdp.notnull())]
df_master['gdp']= df_master['gdp']/1000000 # GDP in millon dollars
# df = pd.merge(df_master,df_paris[['iso_code','base_year','emisions_goal']],'left',on=['iso_code','year']) # why on year?
df = pd.merge(df_master,df_paris[['iso_code_a','target year','emissions_goal']],'left',on=['iso_code_a'])
df = df.loc[df.consumption_co2.notnull()] # not needed


# COLUMNS NEEDED:
# group - GDP/Cap
df['gdp_percap'] = df.apply(lambda row: row['gdp'] / row['population'], axis=1)

# consumption-based emissions per capita
df.rename(columns = {'consumption_co2':'consumption'}, inplace=True)
df['consumption_percap'] = df['consumption']*1000000000000 / df['population']
df['consumption_goal'] = df['emissions_goal']*1000000000000 / df['population']

# import_share
df['imports_share'] = df.apply(lambda row: row['imports'] / row['imports_a'], axis=1)

# Marginal propensity of external consumption or total Imports: M/GDP
df['Mg_imports_tot'] = df['imports_a']/df['gdp']

# Marginal propensity of imports for each trade partner
df['MgM_bilateral'] = df['imports']*100/df['gdp']


# Growth variables
growth= df[['country_a', 'iso_code_a','year','region','sub-region','gdp','imports_a','Mg_imports_tot','consumption_percap','population']]
growth= growth.drop_duplicates(subset=['iso_code_a', 'year'], keep='last') #get aggregates by country-year
growth


# Plot consumption percapita over time
regional_consumption = growth[['region','consumption_percap','year']].groupby(['region','year']).agg({'consumption_percap':'sum'}).reset_index()
# sns.lineplot(x="year", y="consumption_percap",hue="iso_code_a", data=growth[growth['region']=='Europe'])
sns.lineplot(x="year", y="consumption_percap",hue="region", data=regional_consumption)

#compute variation rates of GDP, MgC_imports, and consumption_percap for each year
growth = growth[growth['year']>= 2000]
# compute lagged variables
growth['gdp_lag'] = growth.groupby(['iso_code_a'])['gdp'].shift(1)
growth['MgM_lag'] = growth.groupby(['iso_code_a'])['Mg_imports_tot'].shift(1)
growth['consump_lag'] = growth.groupby(['iso_code_a'])['consumption_percap'].shift(1)
growth = growth.loc[growth['gdp_lag'].notnull()]

# compute variation rates 
growth['gdp_var']= (growth['gdp']- growth['gdp_lag'])/growth['gdp_lag']
growth['MgM_var']= (growth['Mg_imports_tot']- growth['MgM_lag'])/growth['MgM_lag']
growth['consump_var']= (growth['consumption_percap']- growth['consump_lag'])/growth['consump_lag']


# Dataframe with growth rates  per country
#Take average growth rates per country
df_growth = growth[['iso_code_a','gdp_var','MgM_var','consump_var']].groupby(['iso_code_a']).agg({'gdp_var':'mean','MgM_var':'mean','consump_var':'mean'}).reset_index()


# Use growth dataframe to compute parameters for the model Consumption ~ B0+ B1*GDP + B2*Imports
# get list of countries
list_countries= growth['iso_code_a'].unique()

# Iterate over each country
dict_results={}
for country in list_countries.tolist():
    df_country= growth[growth['iso_code_a']== country]
    X= df_country[['gdp','imports_a']]
    Y= df_country['consumption_percap']
    result = sm.ols(formula="Y ~ X", data=df_country, missing='drop').fit()
    dict_results.setdefault('iso_code_a',[]).append(country)
    dict_results.setdefault('beta0',[]).append(result.params[0]) # Intercept
    dict_results.setdefault('beta1',[]).append(result.params[1]) # Mg propensity GDP
    dict_results.setdefault('beta2',[]).append(result.params[2]) # Mg propensity Imports
    #dic_results.setdefault('resid',[]).append(np.mean(result.resid)) #Residuals


result.summary()



# Convert dictionary with parameters to dataframe
df_params= pd.DataFrame.from_dict(dict_results)

## Merge computed parameters in the main dataframe
df= pd.merge(df, df_growth, on=['iso_code_a'], how='inner') #add annual variation rates
df= pd.merge(df, df_params, on=['iso_code_a'], how='inner') #add annual variation rates


df['GDP-X']= df['gdp']-df['exports_a']



df2000= df[df['year']==2000]


# ## Dynamic Model


# Dataframe at the country level to define node attributes
nodes= df2000.drop_duplicates(subset=['country_a'], keep='first')
nodes= nodes.round(2)
df2000= df2000.round(3)



# Classify countries in four groups by GDP
nodes= nodes.sort_values(by=['gdp'], ascending=False).reset_index(drop=True)
nodes['index1']=nodes.index
def classif(r):
    if r< 20:
        m= '1'
    elif r>=20 and r<60:
        m= '2'
    elif r>=60 and r<100:
        m= '3'
    else:
        m= '4'
    return m
nodes['group'] = nodes.index1.apply(classif)
nodes




def initialize():
    global G, nextg, pos
    # Create graph with edge attributes: Imports, parteners_consumption, and Imports growth rate= alpha
    G = nx.from_pandas_edgelist(df2000[['country_a','country_b','imports','exports','MgM_bilateral','MgM_var']], 'country_a', 'country_b', 
                                edge_attr=['imports','exports','MgM_bilateral','MgM_var'], create_using= nx.MultiDiGraph())
    
    
    
        # set graph layout
    pos = nx.spring_layout(G)
        # convert dataframe to dictionary of attributes
    node_attr = nodes[['country_a','exports_a','imports_a','GDP-X','gdp_var','consumption_percap','beta0','beta1','beta2','group','region','sub-region']].set_index('country_a').to_dict('index')
    nx.set_node_attributes(G, node_attr)
    
    # remove imbalanced node
    G.remove_node(920)
    
    nextg= G.copy()



def update():
    global G, nextg
    
    # Update GDP with GDP growth rate
    for i in G.nodes():
        try:
            nextg.nodes[i]['GDP'] = (1+ nextg.nodes[i]['gdp_var'])* (nextg.nodes[i]['GDP-X'] + nextg.nodes[i]['exports_a'])
        except KeyError:
            pass
    
    # Update GDP without exports
    for i in G.nodes():
        try:
            nextg.nodes[i]['GDP-X'] = (1+ G.nodes[i]['gdp_var'])* G.nodes[i]['GDP-X']
        except KeyError:
            pass
    
    # Update Imports variation at edge level
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        nextg[i][j][0]['imports']= (1 + (nextg.edges[i,j,0]['MgM_var']))* (nextg.edges[i,j,0]['MgM_bilateral']/100)* nextg.nodes[i]['GDP']
         
    
    # Get total imports
    for i in nextg.nodes(): 
        nextg.nodes[i]['imports_a'] = nextg.out_degree(i,'imports')
     
    # Update bilateral exports based on updated bilateral imports:
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        g= nextg[i][j][0]['imports']
        for j, y, z, w in nextg.edges(data="weight", keys=True):
            if y== i:
                nextg[j][y][0]['exports'] = g
                #print(nextg[j][y][0]['exports'])
            else:
                pass
            
    # Compute total exports
    for i in nextg.nodes(): 
        nextg.nodes[i]['exports_a'] = nextg.out_degree(i,'exports')
     
    # Compute consumption-based emissions at node level
    for i in nextg.nodes(): 
        try:
            nextg.nodes[i]['Emissions']= nextg.nodes[i]['beta0'] + nextg.nodes[i]['beta1']*nextg.nodes[i]['GDP'] + nextg.nodes[i]['beta2']*nextg.nodes[i]['imports_a']   
        except KeyError:
           nextg.nodes[i]['Emissions']=0
        # print(i, nextg.nodes[i]['Emissions'])
    
    G = nextg
    return nextg

# def update():
#     global G, nextg

#     # Update GDP with GDP growth rate
#     for i in G.nodes():
#         try:
#             nextg.nodes[i]['GDP'] = (1+ G.nodes[i]['gdp_var'])* (G.nodes[i]['GDP-X'] + G.nodes[i]['exports_a'])
#         except:
#             pass
        
#     # Update GDP without exports
    
#     for i in G.nodes():
#         try:
#             nextg.nodes[i]['GDP-X'] = (1+ G.nodes[i]['gdp_var'])* G.nodes[i]['GDP-X']
#         except:
#             pass
    
#     # Update Imports variation at edge level
    
#     for i, j, k, weight in nextg.edges(data="weight", keys=True): 
#         nextg[i][j][0]['imports']= (1 + nextg.edges[i,j,0]['MgM_var'])* (nextg.edges[i,j,0]['MgM_bilateral']/100)* nextg.nodes[i]['GDP']
    
#     # Get total imports
    
#     for i in nextg.nodes(): 
#         nextg.nodes[i]['imports_a'] = nextg.out_degree(i,'imports')
    
#     # Update bilateral exports based on updated bilateral imports:
    
#     for i, j, k, weight in nextg.edges(data="weight", keys=True): 
#         g= nextg[i][j][0]['imports']
#         for j, y, z, w in nextg.edges(data="weight", keys=True):
#             if y== i:
#                 nextg[j][y][0]['exports'] = g
#             else:
#                 pass
     
#     # Compute total exports
#     for i in nextg.nodes(): 
#         nextg.nodes[i]['exports_a'] = nextg.out_degree(i,'exports')
 
    
#     # Compute consumption-based emissions at node level
#     for i in nextg.nodes():
#         try:
#             nextg.nodes[i]['Emissions']= nextg.nodes[i]['beta0'] + nextg.nodes[i]['beta1']*nextg.nodes[i]['GDP'] + nextg.nodes[i]['beta2']*nextg.nodes[i]['imports_a']   
    
#         except:
#             pass
#     g, nextg= nextg, g


def emissions_trend():
    global nextg
    high_income=0
    uppermiddle_income= 0
    lowermiddle_income= 0
    low_income= 0
    for i in nextg.nodes():
        if nextg.nodes[i]['group']=='1':
            high_income+= nextg.nodes[i]['Emissions']
        elif nextg.nodes[i]['group']=='2':
            uppermiddle_income+= nextg.nodes[i]['Emissions']
        elif nextg.nodes[i]['group']=='3':
            lowermiddle_income+= nextg.nodes[i]['Emissions']
        else:
            low_income+= nextg.nodes[i]['Emissions']
    return high_income, uppermiddle_income, lowermiddle_income, low_income


print('here')
N= 5
initialize()
emissions_high=[]
emissions_middleUpper=[]
emissions_middleLower=[]
emissions_low=[]
networks = []

for i in range(N):
    X = update()
    networks.append(X)
    
    print(i)
    H, U, M, L = emissions_trend() # Get consumption by groups at the end of period
    emissions_high.append(H) # array of total consumption for high income countries
    emissions_middleUpper.append(U) # array of total consumption for middle income countries
    emissions_middleLower.append(M)
    emissions_low.append(L) # array of total consumption for middle income countries
    print(i)
    


plt.plot(range(N),emissions_high,        label='Consumption High-income countries')
plt.plot(range(N),emissions_middleUpper, label='Consumption upperMiddle-income countries')
plt.plot(range(N),emissions_middleLower, label='Consumption lowerMiddle-income countries')
plt.plot(range(N),emissions_low,         label='Consumption Low-income-countries')
plt.legend()
plt.xlabel('Time')
plt.ylabel('Total carbon dioxide from consumption')


def networkBuild(a,b,imports,exports,year):
    print('makeing a trade graph for: ',year)
    a = list(a)
    b = list(b)
    imports = list(imports)
    exports = list(exports)
    
    g = nx.Graph()
    countries = set(a)
    
    for i in countries:
        g.add_node(i)
    
    for i in range(len(a)):
        g.add_edge(b[i],a[i], weight = imports[i])
        g.add_edge(a[i],b[i], weight = exports[i])
        
    return g


def plotNetwork(g):
    ax, fig = plt.subplots()
    nx.draw(g, with_labels = True)
    plt.show()

def recordNetworkInfo(g):
    '''
    captures metrics on the network parameter: 
        degree distribution, 
        spectral gap
    '''
    info = dict()
    info['sg'] = sorted(nx.laplacian_spectrum(g))[1]
    return info
