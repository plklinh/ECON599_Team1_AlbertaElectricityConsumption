"""
- This script demonstrates how a prefit prophet model can be refitted with additional data i.e. data left out for training.

- True out-of-sample predictions require predicted values for the regressors, which is unfortunately out of the scope of our abilities.
"""

import pandas as pd
import pickle
import holidays
from fbprophet import Prophet
from normalize_2020_predictions import make_prophet_df, make_future_df
from statsmodels.tsa.forecasting.stl import STLForecast
from statsmodels.tsa.arima.model import ARIMA


def stan_init(model):
    """
    Retrieve parameters from a trained model in the format
    used to initialize a new Stan model.
    ----------
    Input
        - model: A trained model of the Prophet class.

    Returns
        - A Dictionary containing retrieved parameters of model.
    """
    res = {}
    for pname in ['k', 'm', 'sigma_obs']:
        res[pname] = model.params[pname][0][0]
    for pname in ['delta', 'beta', 'trend']:
        res[pname] = model.params[pname][0]
    return res


def make_out_of_sample_df(past_data, model, periods=24*30):
    """
    Sample function to create a dataframe with predicted values for the regressors using STL and ARIMA
    Likely does not run very efficiently.
    Reference: https://www.statsmodels.org/stable/examples/notebooks/generated/stl_decomposition.html#Forecasting-with-STL
    ----------
    Input
        - past_data: data used ing training Prophet model
        - model: trained model of the Prophet class.

    Returns
        - A panda dataframe with predicted values for regressors to use for forecasting
    """
    future_time_df = model.make_future_dataframe(
        periods=periods, freq="H", include_history=False)
    # Creating dummy for working days
    canada_holidays = holidays.CA()
    future_time_df["holiday"] = [
        1 if i.date() in canada_holidays else 0 for i in future_time_df["ds"]]
    future_time_df["workingday"] = future_time_df.apply(
        lambda row: 0 if row["holiday"] == 1 or row["ds"].weekday in ['Saturday', 'Sunday'] else 1, axis=1)

    future_time_df.drop(columns=["holiday"], inplace=True)

    # Create predictions for future values of continuous regressors
    non_binary_regressors = ["Calgary_temp.1_hour_lag", "Edmonton_temp.1_hour_lag", "FortMM_temp.1_hour_lag",
                             "Lethbridge_temp.1_hour_lag", "future 1", "WTI spot"]
    past_data_copy = past_data.drop(columns=["y"]).set_index("ds")
    past_data_copy.index.freq = "H"
    for var in non_binary_regressors:
        var_forecast = STLForecast(past_data_copy[var], ARIMA, model_kwargs=dict(
            order=(1, 1, 0), trend="t")).fit()
        future_time_df[var] = var_forecast.forecast(periods)
    future_time_df.reset_index(inplace=True)
    return future_time_df


if __name__ == "__main__":
    # Code to load pretrained model with pickle
    with open("pickled_model", "rb") as f:
        model = pickle.load(f)

    # Reading in data
    data = pd.read_csv("msa_merged_data.csv")
    data["BEGIN_DATE_GMT"] = pd.to_datetime(data["BEGIN_DATE_GMT"])

    # Making Lags
    # Choose Regressors
    data["Calgary_temp.1_hour_lag"] = data["Calgary_temp"].shift(1)
    data["Edmonton_temp.1_hour_lag"] = data["Edmonton_temp"].shift(1)
    data["FortMM_temp.1_hour_lag"] = data["FortMM_Temp"].shift(1)
    data["Lethbridge_temp.1_hour_lag"] = data["Lethbridge_temp"].shift(1)
    regressors = ["Calgary_temp.1_hour_lag", "Edmonton_temp.1_hour_lag", "FortMM_temp.1_hour_lag",
                  "Lethbridge_temp.1_hour_lag", "future 1", "WTI spot", "workingday"]

    # Make Prophet dataset
    prophet_data = make_prophet_df(
        data.drop(columns=["AIL_DEMAND"]), data["AIL_DEMAND"], regressors).dropna()

    # Initalize a new prophet model with the exact same specifications as original model
    model_2 = Prophet(growth='linear', interval_width=0.95,
                      yearly_seasonality=True,
                      weekly_seasonality='auto',
                      daily_seasonality='auto',
                      seasonality_mode='additive')
    model_2.add_regressor(regressors[0],
                          mode='additive'
                          )
    model_2.add_regressor(regressors[1],
                          mode='additive'
                          )
    model_2.add_regressor(regressors[2],
                          mode='additive'
                          )
    model_2.add_regressor(regressors[3],
                          mode='additive'
                          )
    model_2.add_regressor(regressors[4],
                          mode='additive'
                          )
    model_2.add_regressor(regressors[5],
                          mode='additive'
                          )

    # Binary vars
    model_2.add_regressor(regressors[6],
                          # prior_scale=10,
                          mode='additive',
                          standardize='auto')

    # Warm start re-fitting the model to include 2020
    model_2.fit(prophet_data, init=stan_init(model))
