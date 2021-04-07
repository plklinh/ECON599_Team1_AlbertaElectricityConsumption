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


"""
Plot Annual Average AIL vs WTI Spot Price

Input: Data from 2010 - 2020
Returns: Figure
"""


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


"""
Plot Average Pool Price

Input: Data from 2010 - 2020
Returns: Figure
"""


def plot_avg_pool_price(data):
    pool_price_avg = data.groupby("year")["POOL_PRICE"].mean()
    fig = go.Figure()

    avg_price = data["POOL_PRICE"].mean()

    fig.add_trace(go.Scatter(x=pool_price_avg.index,
                             y=pool_price_avg
                             ))
    fig.add_hline(y=avg_price, line_dash="dot",
                  line_color="Red",
                  annotation_text="Average Price 2010-2020: {:.2f}".format(
                      avg_price),
                  annotation_position="bottom left",
                  annotation_font_size=12,
                  annotation_font_color="red"
                  )

    fig.update_yaxes(range=[0, 90])

    fig.update_layout(title="Average Pool Price",
                      xaxis_title="(CAD)"
                      )

    return fig


"""
Plot Tempearture Normalized Demand based on Heating and Colling degree days

Input: Data from 2010 - 2020
Returns: Figure
"""


def plot_normalized_demand(data):
    temp_df = data[["AIL_DEMAND", "Degree_days"]].copy()
    temp_df = temp_df.groupby(by=temp_df.index.date).sum()
    temp_df.index = pd.to_datetime(temp_df.index)
    temp_df['Normalized_AIL_Demand'] = temp_df.AIL_DEMAND / temp_df.Degree_days

    fig = go.Figure()
    for year in range(2010, 2021):
        fig.add_trace(go.Box(x=temp_df[temp_df.index.year == year].index.year,
                             y=temp_df['Normalized_AIL_Demand'][temp_df.index.year == year],
                             name=str(year)
                             ))

    fig.update_layout(
        title="Distribition of Daily Demand per Heating/Cooling Degree Days (Base = 18 Celsius) ")
    return fig


# Read in data for all years
data = pd.read_csv("msa_merged_data.csv")
data["BEGIN_DATE_GMT"] = pd.to_datetime(data["BEGIN_DATE_GMT"])
data.set_index("BEGIN_DATE_GMT", drop=False, inplace=True)

# Read in predictions for 2020
data_2020 = pd.read_csv("forecasted_2020_data.csv")
data_2020["BEGIN_DATE_GMT"] = pd.to_datetime(data_2020["BEGIN_DATE_GMT"])
data_2020.set_index("BEGIN_DATE_GMT", drop=False, inplace=True)

# Setting up Dash app, it automatically uses the style sheets from asses folder
app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children="Alberta's Internal Load 2020",
            className="header-title"),

    html.H2(children="Summary",
            className="header-description"),

    html.Div(children=[
        html.Div(
            children=[
                html.Div(children=dcc.Graph(
                    figure=plot_oil_v_demand(data),
                    id='oil_v_demand_fig'),
                    className='card'
                ),
            ],

            className="wrapper"),
        html.Div(
            children=[
                html.Div(children=dcc.Graph(
                    figure=plot_avg_pool_price(data),
                    id='avg_pool_price_fig'),
                    className='card'
                ),
            ],
            style={"min-width": "40%"},
            className="wrapper"),
    ],
        style={'display': "inline-flex"},
    ),


    html.Div(
        children=[
            html.Div(children=dcc.Graph(
                figure=plot_normalized_demand(data),
                id='normalized_demand_fig'),
                className='card'
            ),
        ],
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

"""
Plot 30 Day Moving Average of 2020's AIL: actual, forecasted and normalized using 2020 temperature
Reuires preloaded data of these measures.
Returns Graph with data from selected time range

Input: Start date, End date
Returns: Figure
"""


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
                                                 end=filtered_data.index.max() + pd.Timedelta(15, unit="D"),
                                                 freq='M')
                      ),
                      xaxis_tickformat='%B'
                      )

    return fig


# Run app
app.run_server(host='127.0.0.1', port=8000, debug=False)
