# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 10:45:18 2021

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
import scipy
from scipy import stats
import xgboost as xgb
import sklearn.model_selection as skl
from sklearn.model_selection import TimeSeriesSplit
from sklearn.model_selection import RandomizedSearchCV
import sklearn.metrics as sklm
from sklearn.metrics import mean_absolute_error
import math
import pmdarima.utils
from pmdarima.utils import diff_inv

merged_data=pd.read_csv("msa_merged_data.csv")

merged_data['BEGIN_DATE_GMT']=pd.to_datetime(merged_data['BEGIN_DATE_GMT'])
merged_data.index=merged_data['BEGIN_DATE_GMT']
del merged_data['BEGIN_DATE_GMT']

#Making the Data Statoinary
merged_data['ail_demand_diff']=merged_data['AIL_DEMAND'].diff(periods=168)
merged_data.dropna(subset=['ail_demand_diff'],inplace=True)
dftest=adfuller(merged_data['ail_demand_diff'])
print(dftest)
merged_data['ail_demand_diff'].plot()
plt.show(merged_data['ail_demand_diff'].plot)

#Defining Measurement Metrics
def MAPE(y_true, y_pred):
    y_true, y_pred=np.array(y_true),np.array(y_pred)
    return np.mean(np.abs((y_true-y_pred)/y_true))*100

def MSE(y_true, y_pred):
    y_true, y_pred=np.array(y_true),np.array(y_pred)
    return np.square(np.subtract(y_true,y_pred)).mean()

def RMSE(y_true, y_pred):
    y_true, y_pred=np.array(y_true),np.array(y_pred)
    return math.sqrt(np.square(np.subtract(y_true,y_pred)).mean())

#Creating Time Series Slpits
merged_data1=merged_data.drop(columns=['AIL_DEMAND'])
X=np.array(merged_data1)
y=np.array(merged_data1['ail_demand_diff'])
tscv=TimeSeriesSplit(n_splits=11)
print(tscv)
for train_index, test_index in tscv.split(X):
    print("TRAIN:", train_index,"TEST:", test_index)
    X_train, X_test= X[train_index], X[test_index]
    y_train, y_test= y[train_index], y[test_index]

#Defining the Model
xgbtuned=xgb.XGBRegressor()
param_grid={
    'max_depth':[3,4,5,6,7,8,9,10],
    'learning_rate':[0.001,0.01,0.1,0.2,0.3],
    'subsample':[0.5,0.6,0.7,0.8,0.9,1.0],
    'colsample_bytree':[0.4,0.5,0.6,0.7,0.8,0.9,1.0],
    'colsample_bylevel':[0.4,0.5,0.6,0.7,0.8,0.9,1.0],
    'min_child_weight':[0.5,1.0,3.0,5.0,7.0,10.0],
    'gamma':[0,0.25,0.5,1.0],
    'n_estimators':[10,31,52,73,94,115,136,157,178,200]}

xgbtunedreg=RandomizedSearchCV(xgbtuned, param_distributions=param_grid,scoring='neg_mean_squared_error',n_iter=20,n_jobs=-1,cv=tscv,verbose=2,random_state=42)

xgbtunedreg.fit(X_train,y_train)
best_score=xgbtunedreg.best_score_
best_param=xgbtunedreg.best_params_
print("best score : {}".format(best_score))
print("best params: ")

preds_boost_tunes=xgbtunedreg.predict(X_test)
#preds_boost_tunes=diff_inv(preds_boost_tunes, lag=)
#y_test_t=diff_inv(y_test,lag=168)

MSE(y_test, preds_boost_tunes)
RMSE(y_test, preds_boost_tunes)

y_train_df=pd.DataFrame(y_train)
y_test_df=pd.DataFrame(y_test)
y_frames=[y_train_df,y_test_df]
train_test_df=pd.concat(y_frames)
train_test_df=train_test_df.rename(columns={0:'ail_demand_diff'})
train_test_df.index=merged_data.index
del y_train_df
del y_test_df

preds_boost_df=pd.DataFrame(preds_boost_tunes)
preds_boost_df=preds_boost_df.rename(columns={0:'ail_demand_diff_pred'})
merged_data2=merged_data[88214:]
preds_boost_df.index=merged_data2.index
plot_data=pd.merge(train_test_df,preds_boost_df,how="outer", left_index=True, right_index=True)

plt.plot(plot_data['ail_demand diff'])
plt.plot(plot_data['ail_demand_diff_pred'])
