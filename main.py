import streamlit as st
import json
import networkx as nx
from collections import defaultdict, Counter
from itertools import combinations
import pandas as pd
from pyvis.network import Network
import tempfile
import os

st.set_page_config(page_title="Event-Entity Knowledge Graph", layout="wide")

# ---------- Helper Functions ----------
def sentiment_to_color(sent):
    """Map sentiment (-10..10) to color."""
    try:
        s = float(sent)
    except Exception:
        s = 0.0
    s = max(-10.0, min(10.0, s))
    if s < -1:
        intensity = int(255 * (min(9, abs(s)) / 10))
        return f"rgb(255,{255-intensity},{255-intensity})"  # redish
    elif s > 1:
        intensity = int(255 * (min(9, s) / 10))
        return f"rgb({255-intensity},255,{255-intensity})"  # greenish
    else:
        return "rgb(200,200,200)"


def build_graph(event_data, taxonomy):
    """Construct a weighted entity co-occurrence graph."""
    taxonomy_sentiment = {}
    for topcat, sub in taxonomy.items():
        for subtype, meta in sub.items():
            if isinstance(meta, dict) and "sentiment" in meta:
                taxonomy_sentiment[subtype] = meta["sentiment"]

    events = []
    for group in event_data:
        if isinstance(group, list):
            events.extend(group)
        elif isinstance(group, dict):
            events.append(group)

    cooccurrence = Counter()
    edge_event_examples = defaultdict(list)
    edge_sentiments = defaultdict(list)

    for ev in events:
        entities = ev.get("entities", [])
        names = list({ent.get("name", "").strip() for ent in entities if ent.get("name")})
        event_types = []
        for cat, types in ev.get("event_classifications", {}).items():
            if isinstance(types, list):
                event_types.extend(types)
            elif isinstance(types, dict):
                event_types.extend(list(types.keys()))
        event_sents = [taxonomy_sentiment[t] for t in event_types if t in taxonomy_sentiment]
        event_sent = sum(event_sents)/len(event_sents) if event_sents else 0.0

        for a, b in combinations(names, 2):
            key = tuple(sorted((a, b)))
            cooccurrence[key] += 1
            edge_event_examples[key].append(ev.get("event_title", ""))
            edge_sentiments[key].append(event_sent)

    G = nx.Graph()
    for (a, b), w in cooccurrence.items():
        avg_sent = sum(edge_sentiments[(a, b)]) / len(edge_sentiments[(a, b)]) if edge_sentiments[(a, b)] else 0.0
        G.add_edge(a, b, weight=w, sentiment=avg_sent,
                   examples=" | ".join(edge_event_examples[(a, b)][:3]))

    # ---------- Centrality Metrics ----------
    degree_dict = dict(G.degree(weight="weight"))
    nx.set_node_attributes(G, degree_dict, "degree")

    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)
    nx.set_node_attributes(G, betweenness, "betweenness")

    # ✅ FIXED eigenvector centrality (safe version)
    ecs = {}
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        n = len(sub)
        if n == 1:
            node = next(iter(sub.nodes()))
            ecs[node] = 1.0
        elif n == 2:
            for node in sub.nodes():
                ecs[node] = 1.0
        else:
            try:
                eig = nx.eigenvector_centrality_numpy(sub, weight="weight")
                ecs.update(eig)
            except Exception:
                # fallback: iterative version
                eig = nx.eigenvector_centrality(sub, weight="weight", max_iter=1000)
                ecs.update(eig)

    nx.set_node_attributes(G, ecs, "eigenvector")

    return G


def display_pyvis(G):
    """Render a NetworkX graph as an interactive Pyvis HTML file and return the path."""
    net = Network(height="750px", width="100%", bgcolor="#ffffff", notebook=False)
    for n, data in G.nodes(data=True):
        size = 10 + 40 * (data.get("eigenvector", 0) or 0)
        title = f"""
        <b>{n}</b><br>
        Degree: {data.get('degree', 0):.2f}<br>
        Betweenness: {data.get('betweenness', 0):.4f}<br>
        Eigenvector: {data.get('eigenvector', 0):.4f}
        """
        net.add_node(n, label=n, size=size, title=title)

    for u, v, d in G.edges(data=True):
        color = sentiment_to_color(d.get("sentiment", 0))
        title = f"""
        Weight: {d.get('weight', 0)}<br>
        Sentiment: {d.get('sentiment', 0):.2f}<br>
        Examples: {d.get('examples', '')}
        """
        net.add_edge(u, v, value=d.get("weight", 1), color=color, title=title)

    net.barnes_hut()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        return tmp.name


# ---------- Streamlit App ----------
st.title("🕸️ Event–Entity Knowledge Graph")
st.markdown("Build and visualize an entity co-occurrence network from event data.")

# File uploaders
col1, col2 = st.columns(2)
with col1:
    event_file = st.file_uploader("Upload event_information_sample.json", type=["json"])
with col2:
    taxonomy_file = st.file_uploader("Upload event_taxonomy.json", type=["json"])

if event_file and taxonomy_file:
    event_data = json.load(event_file)
    taxonomy = json.load(taxonomy_file)

    st.info("Building graph... please wait ⏳")
    G = build_graph(event_data, taxonomy)

    st.success(f"✅ Graph built with **{G.number_of_nodes()} nodes** and **{G.number_of_edges()} edges**")

    # Filters
    min_weight = st.slider("Minimum edge weight to display", 1, 10, 1)
    sentiment_range = st.slider("Sentiment range", -10.0, 10.0, (-10.0, 10.0))

    # Filter graph
    G_filtered = nx.Graph([
        (u, v, d) for u, v, d in G.edges(data=True)
        if d["weight"] >= min_weight and sentiment_range[0] <= d["sentiment"] <= sentiment_range[1]
    ])

    # Retain node attributes
    for n, data in G.nodes(data=True):
        if n in G_filtered.nodes:
            G_filtered.nodes[n].update(data)

    html_path = display_pyvis(G_filtered)
    st.components.v1.html(open(html_path, "r", encoding="utf-8").read(), height=800, scrolling=True)

    # Centrality table
    st.subheader("Top Entities by Centrality")
    df_nodes = pd.DataFrame([
        {
            "Entity": n,
            "Degree": d.get("degree", 0),
            "Betweenness": d.get("betweenness", 0),
            "Eigenvector": d.get("eigenvector", 0)
        }
        for n, d in G.nodes(data=True)
    ])
    top_entities = df_nodes.sort_values(by="Degree", ascending=False).head(20)
    st.dataframe(top_entities.reset_index(drop=True))

    csv = df_nodes.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download full centrality CSV", csv, "node_centralities.csv", "text/csv")
else:
    st.warning("⬆️ Please upload both event and taxonomy JSON files to begin.")
