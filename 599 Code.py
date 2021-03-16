# -*- coding: utf-8 -*-
"""
Created on Sun Mar  7 15:00:22 2021

@author: Colton
"""


import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.tsa.seasonal as tls
import statsmodels.tsa.stattools as sttls
from statsmodels.tsa.stattools import adfuller
import csv
import matplotlib.pyplot as plt
import datetime
import xgboost as xgb

ail_data1=pd.read_csv('C:/Users/Colton/Documents/Econ 611 MSA data/AIL and Pool Price (2010-2020).csv')
ail_data2=pd.read_csv('C:/Users/Colton/Documents/Econ 611 MSA data/AIL and Pool Price (2017-2020).csv')
temp_data=pd.read_csv('C:/Users/Colton/Documents/Econ 611 MSA data/Wide Format_Weighted Temp 2010-2021.csv')
oilfutures_data=pd.read_csv(r'C:\Users\Colton\Documents\Econ 611 MSA data\EIA NYMEX Futures (Crude Oil).csv',header=2)
oilprices_data=pd.read_csv(r'C:\Users\Colton\Documents\Econ 611 MSA data\EIA Oil Prices.csv',header=2)

#Cleaning the Data
oilfutures_data=oilfutures_data.rename(columns={"Cushing, OK Crude Oil Future Contract 1 (Dollars per Barrel)":"future 1","Cushing, OK Crude Oil Future Contract 2 (Dollars per Barrel)":"future 2","Cushing, OK Crude Oil Future Contract 3 (Dollars per Barrel)":"future 3","Cushing, OK Crude Oil Future Contract 4 (Dollars per Barrel)":"future 4"})
oilfutures_data['future 1']=oilfutures_data['future 1'].astype(float)
oilfutures_data['future 2']=oilfutures_data['future 2'].astype(float)
oilfutures_data['future 3']=oilfutures_data['future 3'].astype(float)
oilfutures_data['future 4']=oilfutures_data['future 4'].astype(float)
oilfutures_data=oilfutures_data.drop('Unnamed: 5',axis=1)
oilfutures_data['BEGIN_DATE_GMT']=pd.to_datetime(oilfutures_data["Date"])
oilfutures_data=oilfutures_data[~(oilfutures_data['BEGIN_DATE_GMT']<'2009-12-31')]
oilfutures_data=oilfutures_data[~(oilfutures_data['BEGIN_DATE_GMT']>'2020-12-31')]
del oilfutures_data['Date']

oilprices_data=oilprices_data.rename(columns={"Cushing, OK WTI Spot Price FOB (Dollars per Barrel)":"WTI spot"})
oilprices_data['WTI spot']=oilprices_data['WTI spot'].astype(float)
oilprices_data['BEGIN_DATE_GMT']=pd.to_datetime(oilprices_data["Date"])
oilprices_data=oilprices_data[~(oilprices_data['BEGIN_DATE_GMT']<'2009-12-31')]
oilprices_data=oilprices_data[~(oilprices_data['BEGIN_DATE_GMT']>'2020-12-31')]
del oilprices_data['Date']

ail_frames=[ail_data1,ail_data2]
ail_data=pd.concat(ail_frames)
ail_data['AIL_DEMAND']=ail_data['AIL_DEMAND'].str.replace(',','')
ail_data['AIL_DEMAND']=ail_data['AIL_DEMAND'].astype(int)
ail_data['BEGIN_DATE_GMT']=pd.to_datetime(ail_data['BEGIN_DATE'])
del ail_data['BEGIN_DATE']
del ail_data['DATE']

temp_data=temp_data.rename(columns={"Avg temp":"Avg_temp","Weighted Avg Temp":"Weighted_Avg_Temp"})
temp_datacln=temp_data[['BEGIN_DATE_GMT','Avg_temp','Weighted_Avg_Temp']]
temp_datacln['Avg_temp']=temp_datacln['Avg_temp'].astype(float)
temp_datacln['Weighted_Avg_Temp']=temp_datacln['Weighted_Avg_Temp'].astype(float)
temp_datacln['BEGIN_DATE_GMT']=pd.to_datetime(temp_datacln['BEGIN_DATE_GMT'])

#Merging the data
merged_data=ail_data.merge(temp_datacln,how="right",on=['BEGIN_DATE_GMT'])
merged_data=merged_data.merge(oilfutures_data,how="outer",on=['BEGIN_DATE_GMT'])
merged_data=merged_data.merge(oilprices_data,how="outer",on=['BEGIN_DATE_GMT'])
merged_data.index=merged_data['BEGIN_DATE_GMT']
merged_data=merged_data.sort_index()
merged_data['WTI spot'] = merged_data['WTI spot'].fillna(method='ffill')
merged_data['future 1'] = merged_data['future 1'].fillna(method='ffill')
merged_data['future 2'] = merged_data['future 2'].fillna(method='ffill')
merged_data['future 3'] = merged_data['future 3'].fillna(method='ffill')
merged_data['future 4'] = merged_data['future 4'].fillna(method='ffill')
merged_data=merged_data[1:]
merged_data=merged_data[:-1]
merged_data['BEGIN_DATE_GMT']=pd.to_datetime(merged_data['BEGIN_DATE_GMT'])
merged_data['dayofweek']=merged_data['BEGIN_DATE_GMT'].dt.weekday
merged_data['month']=merged_data['BEGIN_DATE_GMT'].dt.month
merged_data['year']=merged_data['BEGIN_DATE_GMT'].dt.year
merged_data['POOL_PRICE']=merged_data['POOL_PRICE'].str.replace('$','')
merge_data["POOL_PRICE"] = merged_data["POOL_PRICE"].replace(" -   ", np.NaN).replace("[\s,]", "", regex=True)
merged_data["POOL_PRICE"] = pd.to_numeric( merged_data["POOL_PRICE"] )
merged_data=merged_data[~(merged_data['BEGIN_DATE_GMT']>='2020-12-31')]
merged_data['AIL_DEMAND']=merged_data['AIL_DEMAND'].astype(float)
del merged_data['BEGIN_DATE_GMT']

#merged_data.to_csv("C:/Users/Colton/Documents/msa_merged_data.csv",index=True)

#Plots
ail_data.plot('BEGIN_DATE_GMT','AIL_DEMAND')
plt.show(ail_data.plot)


temp_datacln.plot('BEGIN_DATE_GMT','Weighted_Avg_Temp')
plt.show(temp_datacln.plot)


oilprices_data.plot('BEGIN_DATE_GMT','WTI spot')
plt.show(oilprices_data.plot)


oilfutures_data.set_index('BEGIN_DATE_GMT').plot()
plt.show(oilfutures_data.plot)

ail=ail_data[['AIL_DEMAND','BEGIN_DATE_GMT']]
ail.index=ail['BEGIN_DATE_GMT']
ail=ail.drop('BEGIN_DATE_GMT',axis=1)
ail['AIL_DEMAND']=ail['AIL_DEMAND'].astype(float)
decomp=tls.seasonal_decompose(ail['AIL_DEMAND'],period=8760)
decomp.plot()

#XGBoost model
#Making the data stationary

merged_data['ail_demand_diff']=merged_data['AIL_DEMAND'].diff(periods=168)
merged_data.dropna(subset=['ail_demand_diff'],inplace=True)
dftest=adfuller(merged_data['ail_demand_diff'])
print(dftest)
merged_data['ail_demand_diff'].plot()
plt.show(merged_data['ail_demand_diff'].plot)

#Time Series Cross Validation 

import sklearn.model_selection as skl
from sklearn.model_selection import TimeSeriesSplit

slic=merged_data.head(336)
X=np.array(slic)
tscv=TimeSeriesSplit()
print(tscv)
for train_index, test_index in tscv.split(X):
    print("TRAIN:", train_index,"TEST:", test_index)
    X_train, X_test= X[train_index], X[test_index]
    








###################################################################################################
# Creating ummies for hour, day, month, year
merged_data['dayofweek']=merged_data['BEGIN_DATE_GMT'].dt.weekday
merged_data['month']=merged_data['BEGIN_DATE_GMT'].dt.month
merged_data['year']=merged_data['BEGIN_DATE_GMT'].dt.year

hrdummy=pd.get_dummies(merged_data['hour'])
dowdummy=pd.get_dummies(merged_data['dayofweek'])
dowdummy.columns=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
mnthdummy=pd.get_dummies(merged_data['month'])
mnthdummy.columns=['January','Feburary','March','April','May','June','July','August','September','October','November','December']
yrdummy=pd.get_dummies(merged_data['year'])

merged_data= pd.concat([merged_data, hrdummy,dowdummy,mnthdummy,yrdummy], axis=1)
del hrdummy
del dowdummy
del mnthdummy
del yrdummy
##################################################################################################
normal_data=merged_data
normal_data=normal_data.drop('HE',axis=1)
normal_data=normal_data.drop('POOL_PRICE',axis=1)
normal_data=normal_data.drop('future 1',axis=1)
normal_data=normal_data.drop('future 2',axis=1)
normal_data=normal_data.drop('future 3',axis=1)
normal_data=normal_data.drop('future 4',axis=1)
normal_data=normal_data.drop('BEGIN_DATE_GMT',axis=1)
normal_data=normal_data.drop('hour',axis=1)
normal_data=normal_data.drop('dayofweek',axis=1)
normal_data=normal_data.drop('month',axis=1)
normal_data=normal_data.drop('year',axis=1)
normal_data=normal_data.drop('WTI spot',axis=1)
                 
normal_data['AIL_DEMAND']=normal_data['AIL_DEMAND'].astype(float)
normal_data['Avg_temp']=normal_data['Avg_temp'].astype(float)
normal_data['Weighted_Avg_Temp']=normal_data['Weighted_Avg_Temp'].astype(float)
y=normal_data['AIL_DEMAND']
x=normal_data['Avg_temp']
dum=
weather_relnrg=smf.ols("
print(weather_relnrg.summary().tables[1])


