import json
import pandas as pd
import streamlit as st
import plotly.express as px

with open('clean_events_flat.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

a = pd.DataFrame(data)

a['event_date'] = pd.to_datetime(a['event_date'], format='%d/%m/%Y', errors='coerce')
a['event_start_date'] = pd.to_datetime(a['event_start_date'], format='%d/%m/%Y', errors='coerce')
a['event_end_date'] = pd.to_datetime(a['event_end_date'], format='%d/%m/%Y', errors='coerce')
a['final_date'] = a['event_date'].fillna(a['event_start_date'])

a = a.dropna(subset=['final_date'])

monthly_counts = a.groupby(a['final_date'].dt.to_period('M')).size().reset_index(name='event_count')
monthly_counts['final_date'] = monthly_counts['final_date'].dt.to_timestamp()

st.title("📈 Event Count Over Time")
st.sidebar.title("Filters")
searchCountry = st.sidebar.selectbox("Search By countries", sorted(a['clean_location'].dropna().unique()))
sentimentFilter = st.sidebar.selectbox("Event type",("Conflict", "Cooperation", "Netural", "All"))
search = st.sidebar.button("Search")

fig = px.line(
    monthly_counts,
    x='final_date',
    y='event_count',
    title='Event Count by Month'
)

if search:
    if sentimentFilter == 'Cooperation':
        st.plotly_chart(fig, use_container_width=True, key="chart_coop")
        st.write(searchCountry, len(a[(a['clean_location'] == searchCountry) & (a['sentiment'] > 0)]))
        st.write(a[(a['clean_location'] == searchCountry) & (a['sentiment'] > 0)])

    if sentimentFilter == 'Conflict':
        st.plotly_chart(fig, use_container_width=True, key="chart_conflict")
        st.write(searchCountry, len(a[(a['clean_location'] == searchCountry) & (a['sentiment'] < 0)]))
        st.write(a[(a['clean_location'] == searchCountry) & (a['sentiment'] < 0)])

    if sentimentFilter == 'Netural':
        st.plotly_chart(fig, use_container_width=True, key="chart_net")
        st.write(searchCountry, len(a[(a['clean_location'] == searchCountry) & (a['sentiment'] == 0)]))
        st.write(a[(a['clean_location'] == searchCountry) & (a['sentiment'] == 0)])

if sentimentFilter == 'All':
    st.plotly_chart(fig, use_container_width=True, key="All")
    st.write(searchCountry, len(a[a['clean_location'] == searchCountry]))
    st.write(a[a['clean_location'] == searchCountry])
else:
    st.plotly_chart(fig, use_container_width=True)
