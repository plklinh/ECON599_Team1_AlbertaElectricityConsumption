
import pandas as pd

# Reading in exchange rates
cad_ex = pd.read_excel("original data/USDCAD BOC Rate.xls")
cad_ex.head()


# Reading in oil prices and oil futures

oil_prices = pd.read_excel("original data/EIA Oil Prices.xls",
                           sheet_name="Data 1", skiprows=[0, 1])
futures_oil = pd.read_excel("original data/EIA NYMEX Futures (Crude Oil).xls",
                            sheet_name="Data 1", skiprows=[0, 1])


# Filtering out date from 2010
oil_prices_2010 = oil_prices.loc[oil_prices["Date"] >= "2010-01-01"]
futures_oil_2010 = futures_oil.loc[futures_oil["Date"] >= "2010-01-01"]


# Merging with exchange rate and Converting to CAD
oil_prices_2010_cad = pd.merge(oil_prices_2010, cad_ex[["SOURCE_DAY_DATE", "RATE", "SOURCE_TIMEZONE"]], how="left",
                               left_on="Date", right_on="SOURCE_DAY_DATE")

oil_prices_2010_cad["OK_WTI_Spot_CAD_per_bbl"] = oil_prices_2010_cad[
    "Cushing, OK WTI Spot Price FOB (Dollars per Barrel)"]*oil_prices_2010_cad["RATE"]

futures_oil_2010_cad = pd.merge(futures_oil_2010, cad_ex[["SOURCE_DAY_DATE", "RATE", "SOURCE_TIMEZONE"]], how="left",
                                left_on="Date", right_on="SOURCE_DAY_DATE")

for i in range(1, 5):
    futures_oil_2010_cad["OK_Crude_Future_C{num}_CAD_per_bbl".format(num=i)] = futures_oil_2010_cad[
        "Cushing, OK Crude Oil Future Contract {num} (Dollars per Barrel)".format(num=i)] * futures_oil_2010_cad["RATE"]


# Saving file to Excel.
# ** I used the excel writer to change the output formatting
# ** I had to drop NA because some exchange rates were missing

writer_1 = pd.ExcelWriter("cleaned data/Oil Prices 2010-2021 CAD.xls",
                          datetime_format='yyyy-mm-dd', date_format='yyyy-mm-dd')

oil_prices_2010_cad[["Date", "SOURCE_TIMEZONE",
                     "OK_WTI_Spot_CAD_per_bbl"]].dropna(axis=0).to_excel(writer_1)

writer_1.close()

writer_2 = pd.ExcelWriter("cleaned data/Futures Crude 2010-2021 CAD.xls",
                          datetime_format='yyyy-mm-dd', date_format='yyyy-mm-dd')

futures_oil_2010_cad[["Date", "SOURCE_TIMEZONE",
                      "OK_Crude_Future_C1_CAD_per_bbl",
                      "OK_Crude_Future_C2_CAD_per_bbl",
                      "OK_Crude_Future_C3_CAD_per_bbl",
                      "OK_Crude_Future_C4_CAD_per_bbl"]].dropna(axis=0).to_excel(writer_2)
writer_2.close()
