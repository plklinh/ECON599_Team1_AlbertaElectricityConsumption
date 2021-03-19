# -*- coding: utf-8 -*-
"""
Created on Sun Mar  7 15:00:22 2021

@author: Colton
"""


from sklearn.model_selection import TimeSeriesSplit
import sklearn.model_selection as skl
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.tsa.seasonal as tls
import statsmodels.tsa.stattools as sttls
from statsmodels.tsa.stattools import adfuller
import csv
import matplotlib.pyplot as plt
import datetime
import holidays
# import xgboost as xgb
xls = pd.ExcelFile('original data/AIL and Pool Price (2010-2020)(7183).xls')
ail_data1 = pd.read_excel(xls, "Sheet 1")
ail_data2 = pd.read_excel(xls, "Sheet 2")
temp_data = pd.read_csv('cleaned data/Medium_Weighted Temp 2010-2021.csv')
oilfutures_data = pd.read_csv("cleaned data/Futures Crude 2010-2021 CAD.csv")
oilprices_data = pd.read_csv("cleaned data/Oil Prices 2010-2021 CAD.csv")

# Cleaning the Data
oilfutures_data.rename(columns={"OK_Crude_Future_C1_CAD_per_bbl": "future 1",
                                "OK_Crude_Future_C2_CAD_per_bbl": "future 2",
                                "OK_Crude_Future_C3_CAD_per_bbl": "future 3",
                                "OK_Crude_Future_C4_CAD_per_bbl": "future 4"},
                       inplace=True)
oilfutures_data['future 1'] = oilfutures_data['future 1'].astype(float)
oilfutures_data['future 2'] = oilfutures_data['future 2'].astype(float)
oilfutures_data['future 3'] = oilfutures_data['future 3'].astype(float)
oilfutures_data['future 4'] = oilfutures_data['future 4'].astype(float)
# oilfutures_data = oilfutures_data.drop('Unnamed: 5', axis=1)
oilfutures_data['BEGIN_DATE_GMT'] = pd.to_datetime(oilfutures_data["Date"])
oilfutures_data = oilfutures_data[~(
    oilfutures_data['BEGIN_DATE_GMT'] < '2009-12-31')]
oilfutures_data = oilfutures_data[~(
    oilfutures_data['BEGIN_DATE_GMT'] > '2020-12-31')]
del oilfutures_data['Date']

oilprices_data = oilprices_data.rename(
    columns={"OK_WTI_Spot_CAD_per_bbl": "WTI spot"})
oilprices_data['WTI spot'] = oilprices_data['WTI spot'].astype(float)
oilprices_data['BEGIN_DATE_GMT'] = pd.to_datetime(oilprices_data["Date"])
oilprices_data = oilprices_data[~(
    oilprices_data['BEGIN_DATE_GMT'] < '2009-12-31')]
oilprices_data = oilprices_data[~(
    oilprices_data['BEGIN_DATE_GMT'] > '2020-12-31')]
del oilprices_data['Date']

ail_frames = [ail_data1, ail_data2]
ail_data = pd.concat(ail_frames)
ail_data['AIL_DEMAND'] = ail_data['AIL_DEMAND'].replace(',', '')
ail_data['AIL_DEMAND'] = ail_data['AIL_DEMAND'].astype(int)
ail_data['BEGIN_DATE_GMT'] = pd.to_datetime(ail_data['BEGIN_DATE_GMT'])

del ail_data['DATE']

temp_data.rename(columns={"Avg temp": "Avg_temp",
                          "Weighted Avg Temp": "Weighted_Avg_Temp"}, inplace=True)
temp_datacln = temp_data[['BEGIN_DATE_GMT', 'Avg_temp', 'Weighted_Avg_Temp']]
temp_datacln['Avg_temp'] = temp_data['Avg_temp'].astype(float)
temp_datacln['Weighted_Avg_Temp'] = temp_data['Weighted_Avg_Temp'].astype(
    float)
temp_datacln['BEGIN_DATE_GMT'] = pd.to_datetime(temp_datacln['BEGIN_DATE_GMT'])

# Merging the data
merged_data = ail_data.merge(temp_datacln, how="right", on=['BEGIN_DATE_GMT'])
merged_data = merged_data.merge(
    oilfutures_data, how="outer", on=['BEGIN_DATE_GMT'])
merged_data = merged_data.merge(
    oilprices_data, how="outer", on=['BEGIN_DATE_GMT'])
merged_data.index = merged_data['BEGIN_DATE_GMT']
merged_data = merged_data.sort_index()
merged_data['WTI spot'].fillna(method='ffill', inplace=True)
merged_data['future 1'].fillna(method='ffill', inplace=True)
merged_data['future 2'].fillna(method='ffill', inplace=True)
merged_data['future 3'].fillna(method='ffill', inplace=True)
merged_data['future 4'].fillna(method='ffill', inplace=True)

merged_data['WTI spot'].fillna(method='bfill', inplace=True)
merged_data['future 1'].fillna(method='bfill', inplace=True)
merged_data['future 2'].fillna(method='bfill', inplace=True)
merged_data['future 3'].fillna(method='bfill', inplace=True)
merged_data['future 4'].fillna(method='bfill', inplace=True)

merged_data['BEGIN_DATE_GMT'] = pd.to_datetime(merged_data['BEGIN_DATE_GMT'])
merged_data['dayofweek'] = merged_data['BEGIN_DATE_GMT'].dt.weekday
merged_data['month'] = merged_data['BEGIN_DATE_GMT'].dt.month
merged_data['year'] = merged_data['BEGIN_DATE_GMT'].dt.year

merged_data['POOL_PRICE'] = merged_data['POOL_PRICE'].replace('$', '')
merged_data["POOL_PRICE"] = merged_data["POOL_PRICE"].replace(
    " -   ", np.NaN).replace("[\s,]", "", regex=True)
merged_data["POOL_PRICE"] = pd.to_numeric(merged_data["POOL_PRICE"])

merged_data = merged_data[~(merged_data['BEGIN_DATE_GMT'] >= '2020-12-31')]
merged_data['AIL_DEMAND'] = merged_data['AIL_DEMAND'].astype(float)

# Creating ummies for hour, day, month, year
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

canada_holidays = holidays.CA()
merged_data["holiday"] = [
    1 if i.date() in canada_holidays else 0 for i in merged_data["BEGIN_DATE_GMT"]]
merged_data["workingday"] = merged_data.apply(
    lambda row: 0 if row["holiday"] == 1 or row["dayofweek"] in [5, 6] else 1, axis=1)

merged_data = pd.concat(
    [merged_data, hrdummy, dowdummy, mnthdummy, yrdummy], axis=1)
merged_data[["HE", "POOL_PRICE"	, "AIL_DEMAND", "Avg_temp", "Weighted_Avg_Temp",
             "future 1", "future 2", "future 3", "future 4",
             "WTI spot", "dayofweek", "month", "year", "holiday", "workingday"]].to_csv("msa_merged_data.csv")
