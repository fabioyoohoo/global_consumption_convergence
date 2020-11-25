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
# from pylab import *

# import plotly.offline as py
# import plotly.graph_objects as go
# from pandas.compat import StringIO
# import random

##############################################################################
### DATA
year = 2010
from data_loader import df_master, df_consumption, joiner_official


# create subsets of the data
df_subset = df_master[df_master['year'] == year]
df_subset = df_subset.loc[df_subset.iso_code.notnull()]

consumption_subset = df_consumption[df_consumption['year'] == year]
consumption_subset = consumption_subset.loc[consumption_subset.co2.notnull()]
consumption_subset = consumption_subset.loc[consumption_subset['country']!='World']


# THINGS THE SUBSET DATAFRAME NEEDS
meta = consumption_subset[(consumption_subset.gdp.notnull()) | (consumption_subset.value.notnull())]
meta['gdp'].fillna(meta['value'],inplace=True)
meta.drop(['value'],axis=1,inplace=True)
meta = meta[['iso_code','year','co2','gdp','population']]

country_b = df_subset[['country_b','imports','exports']].groupby(['country_b']).agg({'imports':'sum','exports':'sum'}).reset_index()
country_b = pd.merge(country_b, joiner_official, left_on='country_b', right_on='country_a')
country_b.drop(['country_a'],axis=1,inplace=True)
country_b = pd.merge(country_b, meta, 'inner', on=['iso_code'])
country_b.rename(columns = {'imports':'impots_b','exports':'exports_b','iso_code':'iso_code_b',
                            'co2':'co2_b','gdp':'gdp_b','population':'population_b'}, inplace=True)

country_a = df_subset[['country_a','imports','exports']].groupby(['country_a']).agg({'imports':'sum','exports':'sum'}).reset_index()
country_a.rename(columns = {'imports':'imports_a','exports':'exports_a'}, inplace=True)

# FINAL MERGE
df = pd.merge(df_subset,meta,'left',on=['iso_code','year'])
df = df.loc[df.co2.notnull()]

# COLUMNS NEEDED:
# group - GDP/Cap
df['gdp_per_cap'] = df.apply(lambda row: row['gdp'] / row['population'], axis=1)
# consumption - already have as co2
df.rename(columns = {'co2':'consumption'}, inplace=True)
# partn_consump
df = pd.merge(df,country_b,'left',on=['country_b','year'])
df = pd.merge(df,country_a,'left',on=['country_a'])
df = df.loc[df.iso_code_b.notnull()]
# export_share
df['exports_share'] = df.apply(lambda row: row['exports'] / row['exports_a'], axis=1)
# import_share
df['imports_share'] = df.apply(lambda row: row['imports'] / row['imports_a'], axis=1)

# trade_relation

# consumption_transmission
df['consump_trans'] = 0
# consumption growth
co2_growth = df_consumption[df_consumption['year'].isin([2005,2005,2007,2008,2009,2010])]
co2_growth = co2_growth[['iso_code','co2_growth_abs']].groupby(['iso_code']).agg({'co2_growth_abs':'mean'}).reset_index()
df = pd.merge(df,co2_growth,'inner',on=['iso_code'])

# alpha
df['alpha'] = 1
# beta
df['beta'] = 1

df = df.rename(columns = {'co2_growth_abs':'consump_growth','co2_b':'partn_consump','community':'group'})
df = df[~df['country_b'].isin([970,955])] # remove nodes that don't have any outgoing links

# Dataframe of edges
# 'country_a','consumption','beta','group'
nodes = df[['country_a','consumption','beta','group']].groupby(['country_a']).agg({'consumption':'mean','beta':'mean','group':'mean'}).reset_index()
nodes = nodes.drop_duplicates(subset=['country_a'], keep='first')
# nodes = df.drop_duplicates(subset=['country_a'], keep='first')
# nodes= df.drop_duplicates(subset=['country_A'], keep='first')

##############################################################################
### FUNCTIONS

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


##############################################################################
### CREATE GRAPH

# Create graph with edge attributes: Imports, parteners_consumption, and Imports growth rate= alpha
G = nx.from_pandas_edgelist(df[['country_a','country_b','imports','partn_consump','alpha']], 'country_a', 'country_b', 
                            edge_attr=['imports','partn_consump','alpha'], create_using= nx.MultiDiGraph())
    # set graph layout
pos = nx.spring_layout(G)
    # convert dataframe to dictionary of attributes
node_attr = nodes[['country_a','consumption','beta','group']].set_index('country_a').to_dict('index')
    # incorporate dictionary of attributes: Consumption, Convergence_rate= Beta, Group= income level
nx.set_node_attributes(G, node_attr)


nextg = nx.MultiDiGraph()
for i, j, data in G.edges.data(): 
    nextg.add_edge(i, j, 0, Imports=(1 + data['alpha'])* data['imports'])
for i, j, k, weight in nextg.edges(data="weight", keys=True):
    tot_M=nextg.out_degree(i,'imports') # total imports
    nextg[i][j][0]['import_share'] = data['imports']/tot_M # Imports share
   
    
##############################################################################
#### MAP

def initialize():
    global G, nextg, pos
    # Create graph with edge attributes: Imports, parteners_consumption, and Imports growth rate= alpha
    G = nx.from_pandas_edgelist(df[['country_a','country_b','imports','partn_consump','alpha']], 'country_a', 'country_b', 
                                edge_attr=['imports','partn_consump','alpha'], create_using= nx.MultiDiGraph())
        # set graph layout
    pos = nx.spring_layout(G)
        # convert dataframe to dictionary of attributes
    node_attr = nodes[['country_a','consumption','beta','group']].set_index('country_a').to_dict('index')
        # incorporate dictionary of attributes: Consumption, Convergence_rate= Beta, Group= income level
    nx.set_node_attributes(G, node_attr)

    nx.set_edge_attributes(G, [], 'consump_trans')
    nx.set_edge_attributes(G, [], 'consump_growth')
    
    nextg= G.copy()
    
#def observe():
    #global G, nextg, pos
    #cla()
    #plt.figure(figsize=(14,14))
    #nx.draw(G, cmap = cm.winter, vmin = 0, vmax = 1, pos = pos, node_size=12, width=0.1,
            #node_color = [G.node[i]['Consumption'] for i in G.nodes()])
 
    #plt.savefig("network.png", dpi=1000)
    
    
def update():
    global G, nextg

    # Compute Imports variation 
    for i, j, k, weight in nextg.edges(data="weight", keys=True): 
        #nextg.add_edge(i, j, 0, Imports=(1 + data['Alpha'])* data['Imports'])
        nextg[i][j][0]['imports']= (1 + data['alpha'])* data['imports'] 

    # Compute Imports Share for each edge
    for i, j, k, weight in nextg.edges(data="weight", keys=True):
        tot_M=nextg.out_degree(i,'imports') # total imports
        nextg[i][j][0]['import_share'] = data['imports']/tot_M # Imports share

    # Compute Consumption transmission using = Import_share * Partner_consump
    for i, j, k, weight in nextg.edges(data="weight", keys=True):
        nextg[i][j][0]['consump_trans'] = nextg.edges[i,j,0]['import_share'] * data['partn_consump']
        # nextg[i][j][0]['Consump_trans'] = data['Import_share']* data['Partn_consump']

        # Compute Consumption growth using= Consumption_transmission * Convergence rate Beta
        nextg[i][j][0]['consump_growth'] = nextg.edges[i,j,0]['consump_trans'] * nextg.nodes(data='beta')[i]
        # nextg[i][j][0]['Consump_growth'] = data['Consump_trans'] * nextg.nodes(data='Beta')[i]
        
    # Compute total consumption in next period
    # for i in nextg.nodes():
    for i in nodes['country_a']:
        nextg.node[i]['consumption'] = nextg.out_degree(i,'consump_growth') + nextg.nodes(data='consumption')[i] 
        #Update partener_consumption
        for j in nextg.nodes():
            if i in nextg.neighbors(j):
                nextg[j][i][0]['partn_consump']= nextg.node[i]['consumption']
    
    # Compute total consumption in next period
    # for i in nextg.nodes():
    #     consumption_growth = 0
    #     for j in nextg.nodes():
    #         if (j != i) & (nextg.edges[i,j,0]['consump_growth'] != 'nan'):
    #             consumption_growth += nextg.edges[i,j,0]['consump_growth']
    #     nextg.node[i]['consumption'] = consumption_growth + G.nodes[i]['consumption'] 
    #     #Update partener_consumption
    #     for j in nextg.nodes():
    #         if i in nextg.neighbors(j):
    #             nextg[j][i]['partn_consump'] = nextg.nodes[i]['consumption']
    
    
# Total consumption by group of countries (by income-level)    
def consumption_patterns():
    global nextg
    high_income=0
    middle_income= 0
    low_income= 0
    for i in nodes['country_a']:
        if nextg.node[i]['group']==1:
            high_income+= nextg.node[i]['consumption']
        elif nextg.node[i]['group']==2:
            middle_income+= nextg.node[i]['consumption']
        else:
            low_income+= nextg.node[i]['consumption']
    return high_income, middle_income, low_income

N= 10
initialize()
consumption_high=[]
consumption_middle=[]
consumption_low=[]

for i in range(N):
    
    H, M, L = consumption_patterns() # Get consumption by groups at the end of period
    consumption_high.append(H) # array of total consumption for high income countries
    consumption_middle.append(M) # array of total consumption for middle income countries
    consumption_low.append(L) # array of total consumption for middle income countries
        
    update()
    

    
plt.plot(range(N),consumption_high, label='Consumption High-income countries')
plt.plot(range(N),consumption_middle, label='Consumption Middle-income countries')
plt.plot(range(N),consumption_low, label='Consumption Low-income countries')

plt.xlabel('Time')
plt.ylabel('Total carbon dioxide from consumption')

