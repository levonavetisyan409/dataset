import json
import pandas as pd
import networkx as nx
import streamlit as st
from itertools import combinations
from collections import Counter

with open('clean_events_flat.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data)
G = nx.Graph()
pairCounter = Counter()

dataSentiment = df['sentiment']

for event_entities in df['entities_names']:
    entities = []
    for e in event_entities.split(";"):
        e = e.strip()
        if e != '':
            entities.append(e)
    
    if len(entities) > 1:
        for pair in combinations(sorted(entities), 2):
            pairCounter[pair] += 1

allEntities = set()
for eventEntities in df['entities_names']:
    for e in eventEntities.split(";"):
        e = e.strip()
        if e != '':
            allEntities.add(e)

G.add_nodes_from(allEntities)

for (i, j), w in pairCounter.items():
    G.add_edge(i, j, weight=w)

degree = dict(G.degree())
betwenness = nx.betweenness_centrality(G, weight='weight')
eigenvector = nx.eigenvector_centrality(G, max_iter=100, weight='weight')

dataCertenty = pd.DataFrame({
    'degree': pd.Series(degree),
    'betwenness': pd.Series(betwenness),
    'eigenvector': pd.Series(eigenvector)
})

st.title("Centrality Metrics")
st.write(dataCertenty)