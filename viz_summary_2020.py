# Basic data and viz
from os import name
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Dash stuff
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

# Read in data for all years
data = pd.read_csv("msa_merged_data.csv")
data["BEGIN_DATE_GMT"] = pd.to_datetime(data["BEGIN_DATE_GMT"])
data.set_index("BEGIN_DATE_GMT", drop=False, inplace=True)

# Read in predictions for 2020
data_2020 = pd.read_csv("forecasted_2020_data.csv")
data_2020["BEGIN_DATE_GMT"] = pd.to_datetime(data_2020["BEGIN_DATE_GMT"])
data_2020.set_index("BEGIN_DATE_GMT", drop=False, inplace=True)


def plot_oil_v_demand(data):
    year_change = data.groupby("year")["AIL_DEMAND"].mean().pct_change() * 100
    oil_avg = data.groupby("year")["WTI spot"].mean()
    # Temp vs. Consumption Line Graph
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(x=year_change.index,
                         y=year_change,
                         name="Average AIL Demand"
                         ), secondary_y=False)
    fig.add_trace(go.Scatter(x=oil_avg.index,
                             y=oil_avg,
                             name="WTI Spot Price"
                             ), secondary_y=True)

    # Set x-axis title
    fig.update_xaxes(title_text="Time")

    # Set y-axes titles
    fig.update_yaxes(
        title_text="AIL Demand (% Change)", secondary_y=False)
    fig.update_yaxes(title_text="WTI Oil Spot ($)",
                     range=[0, 120],
                     secondary_y=True)
    fig.update_layout(title_text="Annual Average AIL Demand vs. WTI Spot Price from 2011 - 2020",
                      xaxis=dict(tickmode='array',
                                 tick0=0,
                                 tickvals=np.arange(1, 365, 30),
                                 ticktext=['Jan', 'Feb', 'Mar', 'April', 'May',
                                           'June', 'July', "Aug", "Sep", "Oct", "Nov", "Dec"]
                                 )
                      )
    return fig


def plot_avg_pool_price(data):
    pool_price_avg = data.groupby("year")["POOL_PRICE"].mean()
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=pool_price_avg.index,
                             y=pool_price_avg
                             ))

    fig.update_yaxes(range=[0, 90])
    fig.update_layout(title="Average Pool Price",
                      shapes=[dict(
                          type="line",
                          name="Average from 2010 to 2020",
                          yref='y1',
                          y0=data["POOL_PRICE"].mean(),
                          y1=data["POOL_PRICE"].mean(),
                          xref='x1',
                          x0=pool_price_avg.index.min(),
                          x1=pool_price_avg.index.max(),
                          line=dict(
                              color="Red",
                              width=4,
                              dash="dashdot",
                          ))]
                      )

    return fig


def plot_normalized_demand(data):
    temp_df = data[["AIL_DEMAND", "year"]]
    base_temp = 18
    degree_days = []
    for value in data['Avg_temp']:
        if (value < base_temp) or (value > base_temp):
            degree_days.append((base_temp - value)*(1/24))
        else:
            degree_days.append(0)

    temp_df['Normalized_AIL_Demand'] = temp_df["AIL_DEMAND"] / degree_days

    fig = go.Figure()

    for year in np.unique(temp_df["year"]):
        fig.add_trace(go.Violin(x=temp_df['year'][temp_df['day'] == year],
                                y=temp_df['Normalized_AIL_Demand'][temp_df['year'] == year],
                                name=year,
                                box_visible=True,
                                meanline_visible=True))
    fig.update_layout(title="Temperature Normalized Demand (Base = 18C) ")
    return fig


app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children="Alberta's Internal Load 2020",
            className="header-title"),

    html.H2(children="Summary",
            className="header-description"),

    html.Div(
        children=[
            html.Div(children=dcc.Graph(
                figure=plot_avg_pool_price(data),
                id='avg_pool_price_fig'),
                className='card'
            ),
        ],
        style={'display': "inflex-flex",
               "min-width": "35%"},
        className="wrapper"),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(
                figure=plot_oil_v_demand(data),
                id='oil_v_demand_fig'),
                className='card'
            ),
        ],
        style={'display': "inline-flex",
               "min-width": "35%"},
        className="wrapper"),

    html.H2(children="Forecasted Load",
            className="header-description"),

    html.Div(
        children=[
            html.H3(children="Choose Time Range"),
            dcc.DatePickerRange(
                id='summary-date-range',
                min_date_allowed=data_2020["BEGIN_DATE_GMT"].min().date(),
                max_date_allowed=data_2020["BEGIN_DATE_GMT"].max().date(),
                start_date=data_2020["BEGIN_DATE_GMT"].min().date(),
                end_date=data_2020["BEGIN_DATE_GMT"].max().date(),
            )],
        className="menu"
    ),

    html.Div(
        children=[
            html.Div(children=dcc.Graph(
                id='ail_2020_fig'),
                className='card'
            ),
        ],
        className="wrapper"),
]
)


@app.callback(
    Output('ail_2020_fig', 'figure'),
    [Input("summary-date-range", "start_date"),
     Input("summary-date-range", "end_date")]
)
def plot_ail_2020(start_date, end_date):
    condition = (data_2020["BEGIN_DATE_GMT"] >= start_date) & (
        data_2020["BEGIN_DATE_GMT"] <= end_date)

    filtered_data = data_2020[condition]

    filtered_data = filtered_data.rolling(24 * 30).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=filtered_data.index,
                             y=filtered_data["Actual_Load"],
                             name="Actual Load",
                             mode='lines'))
    fig.add_trace(go.Scatter(x=filtered_data.index,
                             y=filtered_data["Predicted_Load"],
                             name="Predicted Load",
                             mode='lines'))
    fig.add_trace(go.Scatter(x=filtered_data.index,
                             y=filtered_data["Temperature_Norm_Load"],
                             name="2019 Temperature Normalized Load",
                             mode='lines'))
    fig.update_xaxes(range=[filtered_data.index.min(),
                            pd.to_datetime("2021-01-15")])
    fig.update_layout(title="Alberta Internal Load 2020: 30-day Rolling Average",
                      xaxis=dict(
                            tickmode='array',
                          tickvals=pd.date_range(start=filtered_data.index.min(),
                                                 end="2021-01-15", freq='M')
                      ),
                      xaxis_tickformat='%B'
                      )

    return fig


app.run_server(host='127.0.0.1', port=8000, debug=False)
