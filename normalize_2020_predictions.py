"""
This code is to  demonstrate that a trained fbprophet can saved and reloaded to:
-   Do additional forecasting 
-    Refit the model with addtional Data
-    Do visualizations...

Running this script writes AIL forecasts for 2020 including;
-   the actual values
-   forecasted values using 2020 temperature
-   forecasted values using 2019 temperature 
"""

from os import name
import numpy as np
import pandas as pd
import pickle
from fbprophet import Prophet

# this might give errors if you don't have newer version of fbprophet
# from fbprophet.serialize import model_to_json, model_from_json


# Functions to make FBProphet Datasets


def make_prophet_df(X, y, regressors):
    """
    Make dataframe in format compatible with fbprophet which requires 
    y; Dependent variable
    ds: Date-time variable
    additional regressors if applicable
    ---------------
    Input:
        - X:   Datframe containing all depdent including the date-time columns
        - y:    List or array... containing y variable
        - regressors: name of columns in X to add as additional regressors
    Returns:   Pandas DataFrame
    """
    data = pd.DataFrame()
    data["y"] = y
    data['ds'] = X["BEGIN_DATE_GMT"]
    for i in regressors:
        data[i] = X[i]
    return data


def make_future_df(prophet_model, df_train, df_test, include_history=True):
    """
    Make dataframe in format compatible with fbprophet for forecasting perposes
    ---------------
    Input:
        - prophet_model:    Fitted prophet model
        - df_train:     pandas dataframe used for training
        - df_test:     pandas dataframe used for testing
        - include_history;  if True, the dtaframe will include data from test set as well as training set

    Returns:   Pandas DataFrame
    """
    # Creating the dataframe with datetime values to predict on (making predictions on train as well as the test set)
    future_dates = prophet_model.make_future_dataframe(
        periods=len(df_test), freq='H', include_history=include_history)
    # Adding regressors
    if include_history:
        future_dates = pd.merge(
            future_dates, (df_train.append(df_test)).drop('y', axis=1), on='ds')
    else:
        future_dates = pd.merge(
            future_dates, df_test.drop('y', axis=1), on='ds')

    return future_dates


if __name__ == "__main__":

    # Code to load pretrained model with pickle
    with open("pickled_model", "rb") as f:
        model = pickle.load(f)

    # Code to load model with fb prophet serialize if that works
    # with open('serialized_model.json', 'r') as fin:
    #     model = model_from_json(json.load(fin))  # Load model

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
        data.drop(columns=["AIL_DEMAND"]), data["AIL_DEMAND"], regressors)

    # Split train and test set
    split_index = prophet_data[prophet_data["ds"]
                               == "2020-01-01 00:00:00"].index[0]
    train_df, test_df = prophet_data[:split_index], prophet_data[split_index:]
    train_df = train_df.dropna().reindex()

    # Make future dataframe
    future_df = make_future_df(
        model,  train_df, test_df, include_history=False)

    # Make future dataframe with 2019 temperatures
    future_temp_norm_df = future_df.copy(deep=True)
    temperature_columns = ["Calgary_temp.1_hour_lag", "Edmonton_temp.1_hour_lag",
                           "FortMM_temp.1_hour_lag", "Lethbridge_temp.1_hour_lag"]
    index_2019 = len(train_df) - len(future_df)
    for temp_col in temperature_columns:
        future_temp_norm_df[temp_col] = [
            i for i in train_df[temp_col][index_2019:]]

    # Forecast AIL
    forecast_2020 = model.predict(future_df)
    forecast_temp_norm_2020 = model.predict(future_temp_norm_df)

    # Filter out Necessary Columns

    data_2020 = pd.DataFrame()
    data_2020["BEGIN_DATE_GMT"] = [i for i in test_df["ds"]]
    data_2020["Actual_Load"] = [i for i in test_df["y"]]
    data_2020["Predicted_Load"] = [i for i in forecast_2020["yhat"]]
    data_2020["Predicted_Load_lower"] = [
        i for i in forecast_2020["yhat_lower"]]
    data_2020["Predicted_Load_upper"] = [
        i for i in forecast_2020["yhat_upper"]]
    data_2020["Temperature_Norm_Load"] = [
        i for i in forecast_temp_norm_2020["yhat"]]
    data_2020["Temperature_Norm_lower"] = [
        i for i in forecast_temp_norm_2020["yhat_lower"]]
    data_2020["Temperature_Norm_upper"] = [
        i for i in forecast_temp_norm_2020["yhat_upper"]]
    data_2020.set_index("BEGIN_DATE_GMT", drop=True, inplace=True)

    # Save final dataframe to csv files
    data_2020.to_csv("forecasted_2020_data.csv")
