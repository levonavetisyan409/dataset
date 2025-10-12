import pandas as pd
import pydeck as pdk
import streamlit as st
import json

def sentiment_color(sent):
    if sent < 0:
        return [255, 0, 0, 180]
    if sent == 0:
        return [255, 165, 0, 180]
    else:
        return [0, 200, 0, 180]

with open('clean_events_flat.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

if isinstance(data, list) and isinstance(data[0], list):
    all_events = [event for group in data for event in group]
else:
    all_events = data

df = pd.DataFrame(all_events)

required_cols = {'event_title', 'event_location', 'latitude', 'longitude', 'sentiment', 'event_date', 'entities_names'}
required_cols.issubset(df.columns)

map_df = df.dropna(subset=['latitude', 'longitude'])
map_df['sentiment'] = pd.to_numeric(map_df['sentiment'], errors='coerce').fillna(0)
map_df['color'] = map_df['sentiment'].apply(sentiment_color)

map_df['event_date_dt'] = pd.to_datetime(map_df['event_date'], format='%m/%d/%Y', errors='coerce')
min_date = map_df['event_date_dt'].min()
max_date = map_df['event_date_dt'].max()

st.sidebar.title("Event Location Map")
st.sidebar.header("Filters")
sentimentFilter = st.sidebar.selectbox("Event type",("Conflict", "Cooperation", "Netural"))
dateFilter = st.sidebar.slider("Date", min_date.year, max_date.year, max_date.year)
applyFilter = st.sidebar.button("Apply")


if applyFilter:
    if sentimentFilter == "Conflict":
        filtered_df = map_df[map_df['sentiment'] < 0]
    elif sentimentFilter == "Netural":
        filtered_df = map_df[map_df['sentiment'] == 0]
    else:
        filtered_df = map_df[map_df['sentiment'] > 0]
    
    filtered_df = filtered_df[filtered_df['event_date_dt'].dt.year == dateFilter]
    
    st.write(f"Selected: {sentimentFilter} events from {dateFilter}")
else:
    filtered_df = map_df

layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position='[longitude, latitude]',
    get_color='color',
    get_radius=5000,
    pickable=True,
)

tooltip = { "html": """<b>{event_title}</b> 
<br/>{event_location} 
<br/>Names: {entities_names} <br/>
Date: {event_date}
<br/>sentiment: {sentiment} """, 
"style": {"color": "white",}
}

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(
        latitude=map_df['latitude'].mean(),
        longitude=map_df['longitude'].mean(),
        zoom=2,
        pitch=0,
    ),
    tooltip=tooltip
)
st.title("Event Location Map")
st.write(f"We found {len(map_df['event_title'])} events")

st.pydeck_chart(deck)