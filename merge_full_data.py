# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import holidays

"""
'EC - Calgary Temp': 'CALGARY',
"EC - Edmonton Temp": 'EDMONTON',
"EC - Fort McMurray Temp": "FORTMM",
"EC - Lethbridge Temp": "LETHBRG"
"""

"""
Calculate Average and Weighted Average Temperature based on the given non-messing temperature column and population estimate.
Alter data frame in place

Examples: calc_weighted_temp(temp_data, "BFILL_TEMP_CELSIUS", "POP_MEDIUM")
    => Calculate averages based on back filled temperature data and medium population estimates
---------
Input:
    - temp_data: Pandas Dataframe
    - temp_column: string
    - population_column: string
"""


def calc_weighted_temp(temp_data, temp_column, population_column):
    # Calculate average temperature
    temp_data["Avg temp"] = (temp_data[temp_column + "|CALGARY"]
                             + temp_data[temp_column + "|FORTMM"] +
                             temp_data[temp_column+"|EDMONTON"]
                             + temp_data[temp_column+"|LETHBRG"]) / 4.0
    # Calculate weighted average temperature
    yyc_wt = temp_data[temp_column + "|CALGARY"] * \
        temp_data["PCT_" + population_column+"|CALGARY"]
    edm_wt = temp_data[temp_column + "|EDMONTON"] * \
        temp_data["PCT_" + population_column+"|EDMONTON"]
    lb_wt = temp_data[temp_column + "|LETHBRG"] * \
        temp_data["PCT_" + population_column+"|LETHBRG"]
    fmm_wt = temp_data[temp_column + "|FORTMM"] * \
        temp_data["PCT_" + population_column+"|FORTMM"]
    temp_data["Weighted Avg Temp"] = yyc_wt + edm_wt + lb_wt + fmm_wt


"""
Calculate Number of heating and cooling degree days per hour

---------
Input:
    - temp_data: Pandas Series, Numpy List.. with Temperatures
    - base_temp: Base Temperature to count heating and cooling days
Returns:
    - List
"""


def calc_degree_days(temps, base_temp=18):
    degree_days = []
    for value in temps:
        if (value < base_temp) or (value > base_temp):
            degree_days.append((base_temp - value)*(1/24))
        else:
            degree_days.append(0)
    return degree_days


if __name__ == "__main__":
    # Reading in all the data
    xls = pd.ExcelFile(
        'original data/AIL and Pool Price (2010-2020)(7183).xls')
    ail_data1 = pd.read_excel(xls, "Sheet 1")
    ail_data2 = pd.read_excel(xls, "Sheet 2")
    temp_data = pd.read_csv("cleaned data/WF_Weighted Temp 2010-2021.csv")
    oilfutures_data = pd.read_csv(
        "cleaned data/Futures Crude 2010-2021 CAD.csv")
    oilprices_data = pd.read_csv("cleaned data/Oil Prices 2010-2021 CAD.csv")

    # Cleaning temperature data
    POP_COL = "POP_MEDIUM"
    TEMP_COL = "BFILL_TEMP_CELSIUS"
    calc_weighted_temp(temp_data, TEMP_COL, POP_COL)

    temp_data = temp_data[['BEGIN_DATE_GMT',
                           'Avg temp',
                           'Weighted Avg Temp',
                           "BFILL_TEMP_CELSIUS|CALGARY",
                           "BFILL_TEMP_CELSIUS|EDMONTON",
                           "BFILL_TEMP_CELSIUS|FORTMM",
                           "BFILL_TEMP_CELSIUS|LETHBRG",
                           ]]
    temp_data.rename(columns={"Avg temp": "Avg_temp",
                              "Weighted Avg Temp": "Weighted_Avg_Temp",
                              "BFILL_TEMP_CELSIUS|CALGARY": "Calgary_temp",
                              "BFILL_TEMP_CELSIUS|EDMONTON": "Edmonton_temp",
                              "BFILL_TEMP_CELSIUS|FORTMM": "FortMM_Temp",
                              "BFILL_TEMP_CELSIUS|LETHBRG":  "Lethbridge_temp"}, inplace=True)

    temp_data['Avg_temp'] = temp_data['Avg_temp'].astype(float)
    temp_data['Weighted_Avg_Temp'] = temp_data['Weighted_Avg_Temp'].astype(
        float)
    temp_data['BEGIN_DATE_GMT'] = pd.to_datetime(temp_data['BEGIN_DATE_GMT'])
    temp_data["Degree_days"] = calc_degree_days(
        temp_data['Avg_temp'], base_temp=18)

    # Cleaning Oil Futures data
    oilfutures_data.rename(columns={"OK_Crude_Future_C1_CAD_per_bbl": "future 1",
                                    "OK_Crude_Future_C2_CAD_per_bbl": "future 2",
                                    "OK_Crude_Future_C3_CAD_per_bbl": "future 3",
                                    "OK_Crude_Future_C4_CAD_per_bbl": "future 4"},
                           inplace=True)

    oilfutures_data['BEGIN_DATE_GMT'] = pd.to_datetime(oilfutures_data["Date"])
    oilfutures_data = oilfutures_data[~(
        oilfutures_data['BEGIN_DATE_GMT'] < '2009-12-31')]
    oilfutures_data = oilfutures_data[~(
        oilfutures_data['BEGIN_DATE_GMT'] > '2020-12-31')]
    del oilfutures_data['Date']

    # Cleaning Crude Oil data frame
    oilprices_data = oilprices_data.rename(
        columns={"OK_WTI_Spot_CAD_per_bbl": "WTI spot"})
    oilprices_data['BEGIN_DATE_GMT'] = pd.to_datetime(oilprices_data["Date"])
    oilprices_data = oilprices_data[~(
        oilprices_data['BEGIN_DATE_GMT'] < '2009-12-31')]
    oilprices_data = oilprices_data[~(
        oilprices_data['BEGIN_DATE_GMT'] > '2020-12-31')]
    del oilprices_data['Date']

    # Cleaning AIL demand data
    ail_frames = [ail_data1, ail_data2]
    ail_data = pd.concat(ail_frames)
    ail_data['AIL_DEMAND'] = ail_data['AIL_DEMAND'].replace(',', '')
    ail_data['AIL_DEMAND'] = ail_data['AIL_DEMAND'].astype(int)
    ail_data['BEGIN_DATE_GMT'] = pd.to_datetime(ail_data['BEGIN_DATE_GMT'])
    del ail_data['DATE']

    # Merging the data
    merged_data = ail_data.merge(temp_data, how="right", on=['BEGIN_DATE_GMT'])
    merged_data = merged_data.merge(
        oilfutures_data, how="outer", on=['BEGIN_DATE_GMT'])
    merged_data = merged_data.merge(
        oilprices_data, how="outer", on=['BEGIN_DATE_GMT'])
    merged_data.index = merged_data['BEGIN_DATE_GMT']
    merged_data = merged_data.sort_index()

    # Filling in missing values for oil data
    merged_data['WTI spot'].fillna(method='bfill', inplace=True)
    merged_data['future 1'].fillna(method='bfill', inplace=True)
    merged_data['future 2'].fillna(method='bfill', inplace=True)
    merged_data['future 3'].fillna(method='bfill', inplace=True)
    merged_data['future 4'].fillna(method='bfill', inplace=True)

    merged_data["POOL_PRICE"] = pd.to_numeric(merged_data["POOL_PRICE"])

    merged_data = merged_data[~(merged_data['BEGIN_DATE_GMT'] >= '2020-12-31')]
    merged_data['AIL_DEMAND'] = merged_data['AIL_DEMAND'].astype(float)

    # Creating dummies for hour, day, month, year
    merged_data['BEGIN_DATE_GMT'] = pd.to_datetime(
        merged_data['BEGIN_DATE_GMT'])
    merged_data['dayofweek'] = merged_data['BEGIN_DATE_GMT'].dt.weekday
    merged_data['month'] = merged_data['BEGIN_DATE_GMT'].dt.month
    merged_data['year'] = merged_data['BEGIN_DATE_GMT'].dt.year
    merged_data['hour'] = merged_data['BEGIN_DATE_GMT'].dt.hour

    hrdummy = pd.get_dummies(merged_data['hour'])
    dowdummy = pd.get_dummies(merged_data['dayofweek'])
    dowdummy.columns = ['Monday', 'Tuesday', 'Wednesday',
                        'Thursday', 'Friday', 'Saturday', 'Sunday']
    mnthdummy = pd.get_dummies(merged_data['month'])
    mnthdummy.columns = ['January', 'Feburary', 'March', 'April', 'May',
                         'June', 'July', 'August', 'September', 'October', 'November', 'December']
    yrdummy = pd.get_dummies(merged_data['year'])

    # Creating dummy for working days
    canada_holidays = holidays.CA()
    merged_data["holiday"] = [
        1 if i.date() in canada_holidays else 0 for i in merged_data["BEGIN_DATE_GMT"]]
    merged_data["workingday"] = merged_data.apply(
        lambda row: 0 if row["holiday"] == 1 or row["dayofweek"] in [5, 6] else 1, axis=1)

    merged_data = pd.concat(
        [merged_data, hrdummy, dowdummy, mnthdummy, yrdummy], axis=1)

    # Writing file to csv
    cols = ["HE", "POOL_PRICE", "AIL_DEMAND", "Avg_temp", "Degree_days", "Weighted_Avg_Temp",
            "Calgary_temp", "Edmonton_temp", "FortMM_Temp", "Lethbridge_temp",
            "future 1", "future 2", "future 3", "future 4",
            "WTI spot", "dayofweek", "month", "year", "holiday", "workingday"]
    merged_data[cols].to_csv("msa_merged_data.csv")
