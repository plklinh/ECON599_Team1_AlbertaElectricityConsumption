# Basic data and viz
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Dash stuff
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

# Violin Plots of AIL by Year


def plot_ail_dstribution_by_year(data):
    demand_dist_by_year = go.Figure()
    for y in range(data.year.min(), data.year.max() + 1):
        demand_dist_by_year.add_trace(go.Violin(
            y=data[data["year"] == y]["AIL_DEMAND"],
            name=y,
            box_visible=True,
            meanline_visible=True))
    demand_dist_by_year.update_layout(
        title_text="Distribution of AIL by Year")
    return demand_dist_by_year

# Boxplots of AIl by Hour by Year


def plot_ail_distribution_by_hour(data):
    demand_dist_by_hour = px.box(data, x="AIL_DEMAND",
                                 title='Boxplots of Hourly AIL by Year',
                                 facet_col="HE", color="year",
                                 facet_col_wrap=4,
                                 facet_col_spacing=0.01,
                                 facet_row_spacing=0.01,
                                 height=1200
                                 )
    return demand_dist_by_hour

# Temp vs. Consumption Line Graph


def plot_temp_v_demand_line(data):
    data_daily_avg = data.resample("D").mean()

    temp_v_demand_line = make_subplots(specs=[[{"secondary_y": True}]])
    temp_v_demand_line = make_subplots(specs=[[{"secondary_y": True}]])
    temp_v_demand_line.add_trace(go.Scatter(x=data_daily_avg.index,
                                            y=data_daily_avg["AIL_DEMAND"],
                                            name="Temperature",
                                            mode="lines"
                                            ), secondary_y=False)
    temp_v_demand_line.add_trace(go.Scatter(x=data_daily_avg.index,
                                            y=data_daily_avg["Weighted_Avg_Temp"],
                                            name="Electricity Consumption",
                                            mode="lines"
                                            ), secondary_y=True)
    temp_v_demand_line.update_layout(height=500,
                                     title_text="Daily Average Temperature vs. Consumption from 2010 - 2020")
    # Set x-axis title
    temp_v_demand_line.update_xaxes(title_text="Time")
    # Set y-axes titles
    temp_v_demand_line.update_yaxes(
        title_text="Electricity Consumption", secondary_y=False)
    temp_v_demand_line.update_yaxes(title_text="Temperature", secondary_y=True)
    return temp_v_demand_line

# Temp vs. Consumption Scatter Plot


def plot_temp_v_demand_scatter(data):
    data_daily_avg = data.resample("D").mean()
    temp_v_demand_scatter = px.scatter(data_daily_avg, x="Weighted_Avg_Temp",
                                       y="AIL_DEMAND",
                                       title="Temperature vs. Consumption"
                                       )
    return temp_v_demand_scatter


# Reading in data
data = pd.read_csv("msa_merged_data.csv")
data["BEGIN_DATE_GMT"] = pd.to_datetime(data["BEGIN_DATE_GMT"])
data["Weighted_Avg_Temp.1_hour_lag"] = data["Weighted_Avg_Temp"].shift(1)
data['year'] = data['BEGIN_DATE_GMT'].dt.year
data.set_index("BEGIN_DATE_GMT", drop=False, inplace=True)

demand_dist_by_year = plot_ail_dstribution_by_year(data)
demand_dist_by_hour = plot_ail_distribution_by_hour(data)
temp_v_demand_line = plot_temp_v_demand_line(data)
temp_v_demand_scatter = plot_temp_v_demand_scatter(data)

# Setting up Dash app, it automatically uses the style sheets from assets folder
app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children='Exploring Electricity Consumption in Alberta 2010-2020',
            className="header-title"),

    html.H2(children="Alberta Internal Load"),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(figure=demand_dist_by_year,
                                        id='demand-dist-by-year'),
                     className="card"
                     ),
            html.Div(children=dcc.Graph(figure=demand_dist_by_hour,
                                        id='demand-dist-by-hour'),
                     className="card"
                     ),
        ],
        className="wrapper"),

    html.H2(children="Relationship between Demand and Temperature"),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(figure=temp_v_demand_line,
                                        id='temp-v-demand-line'),
                     className="card"
                     ),
            html.Div(children=dcc.Graph(figure=temp_v_demand_scatter,
                                        id='temp-v-demand-scatter'),
                     className="card"
                     ),
        ],
        className="wrapper"),
]
)

# Run app
app.run_server(host='127.0.0.1', port=8000, debug=False)
