from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State
import os

shcc_kika = pd.read_csv('https://raw.githubusercontent.com/brokegradstudent/capstone-data/main/2020-2023-aid-worker-kika-incident-data.csv')
shcc_kika = shcc_kika.iloc[1:]
shcc_kika_dt = pd.to_datetime(shcc_kika["Date"],
                             format='%d/%m/%Y')
shcc_kika["Date Time"] = shcc_kika_dt

def total_workers(row):
    return max(pd.to_numeric(row["Aid Workers Killed"]) + pd.to_numeric(row["Aid Workers Injured"]), 
    pd.to_numeric(row["Aid Workers Kidnapped"]),
    pd.to_numeric(row["Aid Workers Arrested"]))
shcc_kika["Total Workers Affected"] = shcc_kika.apply(total_workers, axis=1)

def incident_type(row):
    killed = pd.to_numeric(row["Aid Workers Killed"])>0
    injured = pd.to_numeric(row["Aid Workers Injured"])>0
    kidnapped = pd.to_numeric(row["Aid Workers Kidnapped"])>0
    arrested = pd.to_numeric(row["Aid Workers Arrested"])>0
    if arrested: 
        if killed:
            return "Arrests and Killings"
        if injured:
            return "Arrests and Injuries"
        return "Arrests"
    if kidnapped:
        if killed:
            return "Kidnappings and Killings"
        if injured:
            return "Kidnappings and Injuries"
        return "Kidnappings"
    if killed:
        return "Killings"
    if injured:
        return "Injuries"
    return "Other"

shcc_kika["Incident Type"] = shcc_kika.apply(incident_type, axis=1)

shcc_kika_grouped_by_country = shcc_kika.groupby(by=["Country", "Incident Type"], group_keys = False).sum().reset_index()

incident_overview_by_country = px.bar(shcc_kika_grouped_by_country, x = "Country", color = "Incident Type", y = "Total Workers Affected", height = 1000)
incident_overview_by_country.update_xaxes(categoryorder='category ascending')
incident_overview_by_country.update_layout(title = "Figure 3: Incident Type Frequency by Country", xaxis_title = "Country", yaxis_title = "Total Health Workers Affected", title_xanchor = "center", title_x = 0.5)

shcc_kika_grouped_by_country_code = shcc_kika.groupby(by=["Country ISO", "Country"], group_keys = False).sum().reset_index()

health_worker_heat_map = px.choropleth(shcc_kika_grouped_by_country_code, locations = "Country ISO",
                    color = "Total Workers Affected",
                    hover_name = "Country", projection = "natural earth",
                    color_continuous_scale = px.colors.sequential.Plasma, height = 1000)
health_worker_heat_map.update_geos(
    showland=True, landcolor="#e0e0e0")
health_worker_heat_map.update_layout(title = "Figure 4: Total Health Workers Attacked Globally, 2020-2023", title_xanchor = "center", title_x = 0.5)

app = Dash('SHCC KIKA 2020-2023')
app.layout = html.Div([
    html.H1("Attacks on Health Workers 2020-2023", style={'textAlign':'center'}),
    html.A("Source data" , href ="https://data.humdata.org/dataset/sind-aid-worker-kka-dataset"),
    html.H2("Section 1: Global-Level Data Analysis", style={'textAlign':'center'}),
    dcc.Graph(id = "Incident Map"),
    html.H3("Use these checkboxes to filter the results for Figures 1 and 2!"),
    dcc.Checklist(
        ['Killed', 'Injured', 'Kidnapped', "Arrested"],
        ['Killed', 'Injured', 'Kidnapped', "Arrested"],
        id = "Map Options", inline=True),
    dcc.Graph(id = "Incident Type Frequency by Month/Year", style={'width':'75%', "display": "inline-block"}),
    dcc.Graph(figure = incident_overview_by_country, style={'width':'75%', "display": "inline-block"}),
    dcc.Graph(figure = health_worker_heat_map, style={'width':'75%', "display": "inline-block"}),
       html.H2("Section 2: Country-Level Data Analysis", style={'textAlign':'center'}),
    html.H3("Use this dropdown menu to look at individual country data for Figures 5-7!"),
    dcc.Dropdown(np.sort(pd.unique(shcc_kika["Country"])), "Afghanistan", id = "country_specific", style={'width':'300px', "display": "inline-block"}),
    dcc.Graph(id = "Time Distribution"),
    html.Div([
        html.Div(dcc.Graph(id = "Perpetrators"), style = {"width": "50%"}),
        html.Div(dcc.Graph(id = "Provinces"), style = {"width": "50%"})], style = {"display":"flex"})
], style={'textAlign':'center'})

@app.callback(Output('Time Distribution', 'figure'),
                Output('Perpetrators', 'figure'),
                Output('Provinces', 'figure'),
                Input('country_specific', 'value'))

def update_country_specific(country):
    country_df = shcc_kika[shcc_kika["Country"] == country]
    actor_grouped = country_df.groupby(["Actor Name"]).count()
    time_dis = px.bar(country_df, x = country_df["Date Time"] + pd.offsets.MonthBegin(-1), 
        y = "Total Workers Affected", color = "Incident Type", height = 1000, hover_data = ["Date"])
    time_dis.update_layout(barmode ='stack', title = "Figure 5: Country-Level Time Distribution of Attacks on Health Workers", xaxis_title = "Month and Year", yaxis_title = "Total Health Workers Affected", title_xanchor = "center", title_x = 0.5)
    time_dis.update_xaxes(categoryorder='category ascending')
    provinces = px.bar(country_df, x = country_df["Admin 1"], color = "Incident Type", height = 750, title = "Figure 7: Incident Type Frequency by State/Province/District")
    provinces.update_layout(xaxis_title = "State/Province/District", yaxis_title = "Total Health Workers Affected", title_xanchor = "center", title_x = 0.5)
    provinces.update_layout(barmode='stack')
    provinces.update_xaxes(categoryorder='category ascending')
    perpetrators = px.bar(actor_grouped, y="Total Workers Affected",title = "Figure 6: Perpetrators of Local Attacks on Health Workers")
    perpetrators.update_layout(xaxis_title = "Identified Actors", yaxis_title = "Number of Attributed Incidents", height = 750, title_xanchor = "center", title_x = 0.5)
    perpetrators.update_xaxes(categoryorder='total descending')
   
    return time_dis, perpetrators, provinces

def filter_map(killed, injured, kidnapped, arrested):
    filtered_df = shcc_kika
    if not killed: 
        filtered_df = filtered_df[pd.to_numeric(filtered_df["Aid Workers Killed"])==0]
    if not injured:
        filtered_df = filtered_df[pd.to_numeric(filtered_df["Aid Workers Injured"])==0]
    if not kidnapped:
        filtered_df = filtered_df[pd.to_numeric(filtered_df["Aid Workers Kidnapped"])==0]
    if not arrested:
        filtered_df = filtered_df[pd.to_numeric(filtered_df["Aid Workers Arrested"])==0]
    return filtered_df

@app.callback(Output('Incident Map', 'figure'),
                Input('Map Options', 'value'))
def update_map(checklist):
    kill = 'Killed' in checklist
    injure = "Injured" in checklist
    kidnap = "Kidnapped" in checklist
    arrest = "Arrested" in checklist
    fig = px.scatter_geo(filter_map(kill, injure, kidnap, arrest), lat = "Latitude", lon = "Longitude", color = "Incident Type", title = "Figure 1: Health Workers %s - 2020-2023" %(', '.join(checklist)),
                     hover_name = "SiND Event ID", size = "Total Workers Affected", height = 1000,
                     hover_data = ["Date", "Country"],
                     projection = "natural earth")
    fig.update_layout(title_xanchor = "center", title_x = 0.5)
    fig.update_geos(showcountries = True, countrycolor = "#999999")
    return fig

@app.callback(Output('Incident Type Frequency by Month/Year', 'figure'),
                Input('Map Options', 'value'))
def update_overview_chart(checklist):
    kill = 'Killed' in checklist
    injure = "Injured" in checklist
    kidnap = "Kidnapped" in checklist
    arrest = "Arrested" in checklist
    overview_df = filter_map(kill, injure, kidnap, arrest)
    fig = px.bar(overview_df, x = overview_df["Date Time"] + pd.offsets.MonthBegin(-1), 
    y = "Total Workers Affected", color = "Incident Type", height = 1000)
    fig.update_layout(barmode ='stack', title = "Figure 2: Time Distribution of Global Incidents", xaxis_title = "Month/Year", yaxis_title ="Total Health Workers Affected",  )
    fig.update_layout(title_xanchor = "center", title_x = 0.5)
    fig.update_xaxes(categoryorder='category ascending')

    return fig

if __name__ == '__main__':
    app.run_server(debug = True, host='0.0.0.0', port = 1054)