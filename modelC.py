import json
import os
import calendar
import pandas as pd
import streamlit as st
import plotly.express as px

colums = ["event_title","clean_location","entities_names","final_date","sentiment"]

def get_event_type(sentiment):
    if sentiment > 0:
        return 'Cooperation'
    elif sentiment < 0:
        return 'Conflict'
    else:
        return 'Neutral'

with open('clean_events_flat.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

a = pd.DataFrame(data)

a['event_date'] = pd.to_datetime(a['event_date'], format='%d/%m/%Y', errors='coerce')
a['event_start_date'] = pd.to_datetime(a['event_start_date'], format='%d/%m/%Y', errors='coerce')
a['event_end_date'] = pd.to_datetime(a['event_end_date'], format='%d/%m/%Y', errors='coerce')
a['final_date'] = a['event_date'].fillna(a['event_start_date'])
a['event_type'] = a['sentiment'].apply(get_event_type)

ententiesGroup = []
ententiesNameGroup = set()
ententiesGroupClean = []

os.system('cls')

for i in sorted(a['entities_names'].dropna().unique()):
    rest = i.find(';')
    ententiesName = i[:rest]
    ententiesGroup.append(ententiesName)

for i in ententiesGroup:
    if i in ententiesName:
        ententiesGroupClean.append(i)
    else:
        ententiesNameGroup.add(i)

ententiesNameGroup = pd.Series(list(ententiesNameGroup))
a = a.dropna(subset=['final_date'])

monthly_counts = a.groupby(a['final_date'].dt.to_period('M')).size().reset_index(name='event_count')
monthly_counts['final_date'] = monthly_counts['final_date'].dt.to_timestamp()

monthly_sentiment = a.groupby(a['final_date'].dt.to_period('M'))['sentiment'].mean().reset_index()
monthly_sentiment['final_date'] = monthly_sentiment['final_date'].dt.to_timestamp()

a['month'] = a['final_date'].dt.month
groupedByType = a.groupby([a['final_date'].dt.to_period('M'), 'event_type']).size().reset_index(name='event_count')

st.sidebar.title("Filters")
searchCountry = st.sidebar.selectbox("Search By Location", sorted(a['clean_location'].dropna().unique()))
searchEntity = st.sidebar.selectbox("Search By Entities", ["All"] + sorted(ententiesNameGroup.dropna().unique()))
sentimentFilter = st.sidebar.selectbox("Event type",("All","Conflict", "Cooperation", "Netural"))
search = st.sidebar.button("Search")

fig = px.line(monthly_counts, x='final_date', y='event_count', title='Event Count by Month')

if search:
    avgSentiment = a[a['clean_location'] == searchCountry]['sentiment'].mean()
    filtered = a[a['clean_location'] == searchCountry]
    filtered['event_type'] = filtered['sentiment'].apply(get_event_type)

    monthly_counts_filtered = filtered.groupby(filtered['final_date'].dt.to_period('M')).size().reset_index(name='event_count')
    monthly_counts_filtered['final_date'] = monthly_counts_filtered['final_date'].dt.to_timestamp()

    st.title(f"📈 Event Count Over Time For {searchCountry}")
    st.write(f"Avarage Sentimet for {searchCountry} is {avgSentiment}")

    if sentimentFilter == 'Cooperation':
        filtered_data = a[(a['clean_location'] == searchCountry) & (a['sentiment'] > 0)]
    if sentimentFilter == 'Conflict':
        filtered_data = a[(a['clean_location'] == searchCountry) & (a['sentiment'] < 0)]
    if sentimentFilter == 'Netural':
        filtered_data = a[(a['clean_location'] == searchCountry) & (a['sentiment'] == 0)]
    if sentimentFilter == 'All':
        filtered_data = a[(a['clean_location'] == searchCountry)]

    if searchEntity != "All":
        filtered_data = filtered_data[filtered_data['entities_names'].str.contains(searchEntity, na=False)]
    
    monthly_counts = filtered_data.groupby(filtered_data['final_date'].dt.to_period('M')).size().reset_index(name='event_count')
    monthly_counts['final_date'] = monthly_counts['final_date'].dt.to_timestamp()
    monthly_sentiment = filtered_data.groupby(a['final_date'].dt.to_period('M'))['sentiment'].mean().reset_index()
    monthly_sentiment['final_date'] = monthly_sentiment['final_date'].dt.to_timestamp()

    groupedByType = filtered.groupby([filtered['final_date'].dt.to_period('M'), 'event_type']).size().reset_index(name='event_count')
    groupedByType['final_date'] = groupedByType['final_date'].dt.to_timestamp()

    filtered_data['month'] = filtered_data['final_date'].dt.month
    monthlyPattern = filtered_data.groupby(['month', 'event_type']).size().reset_index(name='event_count')

    fig = px.line(monthly_counts, x='final_date',y='event_count',title=f'Event Count {searchCountry} {len(filtered_data)}')
    figPattern = px.bar(groupedByType,x='final_date',y='event_count',color='event_type', title='📊 Events by Type Over Time',barmode='group')
    fig_pattern = px.bar(monthlyPattern,x='month',y='event_count',color='event_type',barmode='group',title='📊 Recurring Event Patterns by Month')
    
    for t in ['Conflict', 'Cooperation', 'Neutral']:
        s = monthlyPattern[monthlyPattern['event_type'] == t]
        if not s.empty:
            max_index = s['event_count'].idxmax()
            top = s.loc[max_index]
            month_name = calendar.month_name[int(top['month'])]
            count = int(top['event_count'])
            st.write(f"Historically {month_name} has more {t} ({count})")

    st.plotly_chart(fig, use_container_width=True, key="chart")
    st.write(filtered_data[colums])
    st.plotly_chart(figPattern, use_container_width=True, key="chart_coop_pattern")
    st.write(filtered[['final_date', 'sentiment', 'event_type']])
    st.plotly_chart(fig_pattern, use_container_width=True, key="chart_coop_recognition")
   
else:
    st.title("📈 Event Count Over Time")
    groupedByType_all = a.groupby([a['final_date'].dt.to_period('M'), 'event_type']).size().reset_index(name='event_count')
    groupedByType_all['final_date'] = groupedByType_all['final_date'].dt.to_timestamp()
    monthlyPattern_all = a.groupby(['month', 'event_type']).size().reset_index(name='event_count')

    for t in ['Conflict', 'Cooperation', 'Neutral']:
        s = monthlyPattern_all[monthlyPattern_all['event_type'] == t]
        if not s.empty:
            max_index = s['event_count'].idxmax()
            top = s.loc[max_index]
            month_name = calendar.month_name[int(top['month'])]
            count = int(top['event_count'])
            st.write(f"Historically {month_name} has more {t} ({count})")

    st.plotly_chart(fig, use_container_width=True)
    st.write(a[colums])
    figPattern_all = px.bar(groupedByType_all, x='final_date', y='event_count', color='event_type', title='📊 Events by Type Over Time', barmode='group')
    st.plotly_chart(figPattern_all, use_container_width=True, key="chart_all_type")
    st.write(a[['final_date', 'sentiment', 'event_type']])
    fig_pattern_all = px.bar(monthlyPattern_all, x='month', y='event_count', color='event_type', barmode='group', title='📊 Recurring Event Patterns by Month')
    st.plotly_chart(fig_pattern_all, use_container_width=True, key="chart_all_pattern")
