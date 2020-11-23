#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 17:56:12 2020

@author: fhall & eespinosa
"""

import math
import matplotlib.pyplot as plt
import networkx as nx
# import numpy as np
# import pandas as pd
# from pylab import *

# import plotly.offline as py
# import plotly.graph_objects as go
# from pandas.compat import StringIO
# import random

##############################################################################
### DATA

from data_loader import dfex, df

# Dataframe of edges
nodes= df.drop_duplicates(subset=['country_A'], keep='first')


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
G = nx.from_pandas_edgelist(df[['country_A','country_B','Imports','Partn_consump','Alpha']], 'country_A', 'country_B', 
                            edge_attr=['Imports','Partn_consump','Alpha'], create_using= nx.MultiDiGraph())
    # set graph layout
pos = nx.spring_layout(G)
    # convert dataframe to dictionary of attributes
node_attr = nodes[['country_A','Consumption','Beta','Group']].set_index('country_A').to_dict('index')
    # incorporate dictionary of attributes: Consumption, Convergence_rate= Beta, Group= income level
nx.set_node_attributes(G, node_attr)


nextg = nx.MultiDiGraph()
for i, j, data in G.edges.data(): 
    nextg.add_edge(i, j, 0, Imports=(1 + data['Alpha'])* data['Imports'])
for i, j, k, weight in nextg.edges(data="weight", keys=True):
    tot_M=nextg.out_degree(i,'Imports') # total imports
    nextg[i][j][0]['Import_share'] = data['Imports']/tot_M # Imports share
   
    
##############################################################################
#### MAP

def initialize():
    global G, nextg, pos
    # Create graph with edge attributes: Imports, parteners_consumption, and Imports growth rate= alpha
    G = nx.from_pandas_edgelist(df[['country_A','country_B','Imports','Partn_consump','Alpha']], 'country_A', 'country_B', 
                                edge_attr=['Imports','Partn_consump','Alpha'], create_using= nx.MultiDiGraph())
        # set graph layout
    pos = nx.spring_layout(G)
        # convert dataframe to dictionary of attributes
    node_attr = nodes[['country_A','Consumption','Beta','Group']].set_index('country_A').to_dict('index')
        # incorporate dictionary of attributes: Consumption, Convergence_rate= Beta, Group= income level
    nx.set_node_attributes(G, node_attr)

    nx.set_edge_attributes(G, [], 'Consump_trans')
    nx.set_edge_attributes(G, [], "Consump_growth")
    
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
        nextg[i][j][0]['Imports']= (1 + data['Alpha'])* data['Imports'] 

    # Compute Imports Share for each edge
    for i, j, k, weight in nextg.edges(data="weight", keys=True):
        tot_M=nextg.out_degree(i,'Imports') # total imports
        nextg[i][j][0]['Import_share'] = data['Imports']/tot_M # Imports share

    # Compute Consumption transmission using= Import_share * Partner_consump

    for i, j, k, weight in nextg.edges(data="weight", keys=True):
        nextg[i][j][0]['Consump_trans'] = nextg.edges[i,j,0]['Import_share'] * data['Partn_consump']
        # nextg[i][j][0]['Consump_trans'] = data['Import_share']* data['Partn_consump']

        # Compute Consumption growth using= Consumption_transmission * Convergence rate Beta
        nextg[i][j][0]['Consump_growth'] = nextg.edges[i,j,0]['Consump_trans'] * nextg.nodes(data='Beta')[i]
        # nextg[i][j][0]['Consump_growth'] = data['Consump_trans'] * nextg.nodes(data='Beta')[i]
        
    # Compute total consumption in next period
    for i in nextg.nodes():
        consumption_growth = 0
        for j in nextg.neighbors(i):
            if math.isnan(nextg.edges[i,j,0]['Consump_growth']) == False:
                consumption_growth += nextg.edges[i,j,0]['Consump_growth']

        nextg.node[i]['Consumption'] = consumption_growth + nextg.nodes(data='Consumption')[i] 
        # nextg.node[i]['Consumption'] = nextg.out_degree(i,'Consump_growth')+ nextg.nodes(data='Consumption')[i] 
        #Update partener_consumption
        for j in nextg.nodes():
            if i in nextg.neighbors(j):
                nextg[j][i][0]['Partn_consump']= nextg.node[i]['Consumption']
    
    
    
# Total consumption by group of countries (by income-level)    
def consumption_patterns():
    global G
    high_income=0
    middle_income= 0
    low_income= 0
    for i in G.nodes():
        if G.node[i]['Group']==1:
            high_income+= G.node[i]['Consumption']
        elif G.node[i]['Group']==2:
            middle_income+= G.node[i]['Consumption']
        else:
            low_income+= G.node[i]['Consumption']
    return high_income, middle_income, low_income



N= 100
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
plt.plot(range(N),consumption_high, label='Consumption Middle-income countries')
plt.plot(range(N),consumption_high, label='Consumption Low-income countries')

plt.xlabel('Time')
plt.ylabel('Total energy consumption')









# def initialize():
#     global G, nextg, pos
#     # Create graph with edge attributes: Imports, parteners_consumption, and Imports growth rate= alpha
#     G = nx.from_pandas_edgelist(df[['country_A','country_B','Imports','Partn_consump','Alpha']], 'country_A', 'country_B', 
# edge_attr=['Imports','Partn_consump','Alpha'], create_using= nx.MultiDiGraph())
#         # set graph layout
#     pos = nx.spring_layout(G)
#         # convert dataframe to dictionary of attributes
#     node_attr = nodes[['country_A','Consumption','Beta','Group']].set_index('country_A').to_dict('index')
#     node_attr_nextg = nodes[['country_A','Consumption','Beta','Group']]
#         # incorporate dictionary of attributes: Consumption, Convergence_rate= Beta, Group= income level
#     nx.set_node_attributes(G, node_attr)
#     nx.set_node_attributes(nextg, node_attr_nextg)
#     # bb = nx.edge_betweenness_centrality(G,normalized=False)
#     nx.set_edge_attributes(G, [], 'Consump_trans')
#     nx.set_edge_attributes(G, [], "Consump_growth")
#     nx.set_edge_attributes(nextg, [], 'Consump_trans')
#     nx.set_edge_attributes(nextg, [], "Consump_growth")

    
# #def observe():
#     #global G, nextg, pos
#     #cla()
#     #plt.figure(figsize=(14,14))
#     #nx.draw(G, cmap = cm.winter, vmin = 0, vmax = 1, pos = pos, node_size=12, width=0.1,
#             #node_color = [G.node[i]['Consumption'] for i in G.nodes()])
 
#     #plt.savefig("network.png", dpi=1000)
    
    
# def update():
#     global G, nextg
    
#     # Compute Imports variation 
#     nextg = nx.MultiDiGraph()
#     for i, j, data in G.edges.data(): 
#         nextg.add_edge(i, j, 0, Imports=(1 + data['Alpha'])* data['Imports'])
        
#     # Compute Imports Share for each edge
#     for i, j, k, weight in nextg.edges(data="weight", keys=True):
#         tot_M=nextg.out_degree(i,'Imports') # total imports
#         nextg[i][j][0]['Import_share'] = data['Imports']/tot_M # Imports share

#     for i, j, data in nextg.edges.data():
#         # Compute Consumption transmission using= Import_share * Partner_consump
#         nextg.edges[i,j,0]['Consump_trans'] = data['Import_share']* G.get_edge_data(i,j)[0]['Partn_consump']
        
#         # Compute Consumption growth using= Consumption_transmission * Convergence rate Beta
#         nextg.edges[i,j,0]['Consump_growth']= G.edges[i,j,0]['Consump_trans']* nx.get_node_attributes(G, 'Beta')[i]

        
#     # for i, j, data in nextg.get_edge_data:
#     #     # Compute Consumption transmission using= Import_share * Partner_consump
#     #     nextg[i][j]['Consump_trans']= data['Import_share']* data['Part_consump']
        
#     #     # Compute Consumption growth using= Consumption_transmission * Convergence rate Beta
#     #     nextg[i][j]['Consump_growth']= data['Consump_trans']* data['Beta']

#     # Compute total consumption in next period
#     for i in nextg.nodes():
#         consumption_growth = 0
#         for j in nextg.nodes():
#             if (j != i) & (nextg.edges[i,j,0]['Consump_growth'] != 'nan'):
#                 consumption_growth += nextg.edges[i,j,0]['Consump_growth']
#         nextg.node[i]['Consumption'] = consumption_growth + G.nodes[i]['Consumption'] 
#         #Update partener_consumption
#         for j in nextg.nodes():
#             if i in nextg.neighbors(j):
#                 nextg[j][i]['Partn_consump'] = nextg.nodes[i]['Consumption']

                
#     G = nextg.copy()
    
    
    
# # Total consumption by group of countries (by income-level)    
# def consumption_patterns():
#     global G
#     high_income=0
#     middle_income= 0
#     low_income= 0
#     for i in G.nodes():
#         if G.node[i]['Group']==1:
#             high_income+= G.node[i]['Consumption']
#         elif G.node[i]['Group']==2:
#             middle_income+= G.node[i]['Consumption']
#         else:
#             low_income+= G.node[i]['Consumption']
#     return high_income, middle_income, low_income



# N= 5
# initialize()
# consumption_high=[]
# consumption_middle=[]
# consumption_low=[]

# for i in range(N):

#     H, M, L = consumption_patterns() # Get consumption by groups at the end of period
#     consumption_high.append(H) # array of total consumption for high income countries
#     consumption_middle.append(M) # array of total consumption for middle income countries
#     consumption_low.append(L) # array of total consumption for middle income countries
        
#     update()
    

    
# plt.plot(range(N),consumption_high, label='Consumption High-income countries')
# plt.plot(range(N),consumption_high, label='Consumption Middle-income countries')
# plt.plot(range(N),consumption_high, label='Consumption Low-income countries')

# plt.xlabel('Time')
# plt.ylabel('Total energy consumption')