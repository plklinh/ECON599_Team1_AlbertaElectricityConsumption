
import pandas as pd
import numpy as np

STREAM_NAMES_DICT = {"EC - Calgary Temp": 6,
                     "EC - Edmonton Temp": 11,
                     "EC - Fort McMurray Temp": 16,
                     "EC - Lethbridge Temp": 2
                     }
"""
Reference: https://open.alberta.ca/dataset/0b36ef20-f3ca-49a0-8646-35edd2e4624f/resource/9c6bf6e3-0380-42f9-9473-7264825520cf/download/map-overview-alberta-census-subdivisions-census-divisions-economic-regions.pdf
Census division that contains each city
- 2: Lethbridge
- 6: Calgary
- 11: Edmonton
- 16: Fort McMurray
"""

# Cleaning Temperature Data
"""
After Inital data cleaning, the number of missings values for each city is:
- YYC: 44
- Fort McMurray: 40
- Edmonton: 233
- Lethbridge: 233
"""

"""
Return dataframe with all available data across full time range.
The purpose is to find out number of gaps in the data for each location
--------
Parameters:
    - df: raw data frame
"""


def merge_full_time(df):
    full_time = pd.DataFrame(pd.date_range(start='2010-01-01 07:00:00', end='2021-01-05 07:00:00', freq='H'),
                             columns=["FULL_BEGIN_DATE_GMT"])
    return full_time.merge(df, how="left",
                           left_on="FULL_BEGIN_DATE_GMT",
                           right_on="BEGIN_DATE_GMT")


def back_filling_temperatures_pipeline(temp_raw_df):
    """
    Alter full dataframe inplace.  Fill out missing values according to the following rule:
    - If the gap is isolated, use value from previous hour
    - If there are two or more continous gaps, use corresponding seuqence of hours from previous day
    --------
    Parameters:
        - na_df: dataframe with just missing entries
        - full_df: dataframe with all entries
    """
    def bfill_temperature(na_df, full_df):
        """
        Helper function. Returns the number of hours in-between gaps
        ---------
        Inputs:
            - next-gap: gap i + 1
            - current-gap: gap i
            Valus must be of type "datetime64[ns]"
        """
        def time_gap(next_gap, current):
            return (next_gap - current) / pd.Timedelta(hours=1)

        # Generate columns with previous and next gap
        na_df["NEXT_GAP"] = na_df["FULL_BEGIN_DATE_GMT"].shift(-1)
        na_df["PREV_GAP"] = na_df["FULL_BEGIN_DATE_GMT"].shift(
            1)  # Equivalent of lagging variable by 1

        # Make new column to store back-filled values
        full_df["BFILL_TEMP_CELSIUS"] = pd.Series.copy(full_df["TEMP_CELSIUS"])

        # Iterating through each row in the dataframe with only missing values
        for index, row in na_df.iterrows():
            prev_gap = time_gap(row["FULL_BEGIN_DATE_GMT"], row["PREV_GAP"])
            next_gap = time_gap(row["NEXT_GAP"], row["FULL_BEGIN_DATE_GMT"])

            # If the missing row is part of a continous sequence ...
            if prev_gap == 1.0 or next_gap == 1.0:

                # .... use temperature from same time of previous day
                last_day_temp = full_df[full_df["FULL_BEGIN_DATE_GMT"] ==
                                        row["FULL_BEGIN_DATE_GMT"]-pd.Timedelta(days=1)]["BFILL_TEMP_CELSIUS"]
                full_df.at[index, "BFILL_TEMP_CELSIUS"] = last_day_temp
            # If the missing row is isolated...
            else:
                # ... use temperature from last hour
                last_hour_temp = full_df[full_df["FULL_BEGIN_DATE_GMT"] ==
                                         row["FULL_BEGIN_DATE_GMT"]-pd.Timedelta(hours=1)]["BFILL_TEMP_CELSIUS"]
                full_df.at[index, "BFILL_TEMP_CELSIUS"] = last_hour_temp

    # Generate full data frame
    temp_full_df = merge_full_time(temp_raw_df)
    # Filter out missing Values
    temp_na_df = temp_full_df[pd.isna(temp_full_df["TEMP_CELSIUS"])][[
        "FULL_BEGIN_DATE_GMT"]]
    # Back filling missing temperature
    bfill_temperature(temp_na_df, temp_full_df)

    return temp_full_df


"""
Alter data frame in place. 
Fills in missing value for  'NRG_STREAM_NAME' and generate new column with census division code
"""


def fill_aux_data(df, stream_name, region):
    df["BEGIN_DATE_GMT"] = df["FULL_BEGIN_DATE_GMT"]
    df["END_DATE_GMT"] = df["BEGIN_DATE_GMT"] + pd.Timedelta(hours=1)
    df["Region"] = np.repeat(region, df.shape[0])
    final_df = df.fillna(
        {'SOURCE_TIMEZONE': "MST", 'NRG_STREAM_NAME': stream_name})
    return final_df[df.columns.difference(["FULL_BEGIN_DATE_GMT", "SOURCE_DATETIME", "VERSION_BEGIN_LOCAL", "VERSION_END_LOCAL"])]


if __name__ == "__main__":
    # Reading in tempearure data
    # The data is spread across different sheets so they need to concatenated
    temps = pd.read_excel("original data/Temps Data full.xls", sheet_name=None)
    frames = [df for sheet, df in temps.items()]
    temps_raw = pd.concat(frames)

    # Filtering out only necesssary columns
    temps_raw = temps_raw[["BEGIN_DATE_GMT",
                           "END_DATE_GMT", "NRG_STREAM_NAME", "TEMP_CELSIUS"]]

    location_temps = []

    for stream, census_div in STREAM_NAMES_DICT.items():
        # Seperate the dataframe by location
        location_temp_raw = temps_raw[temps_raw["NRG_STREAM_NAME"]
                                      == stream]
        # Consider the outlier in Lethbridge an NA
        if stream == "EC - Lethbridge Temp":
            lb_outlier_index = location_temp_raw[location_temp_raw["TEMP_CELSIUS"] > 40].index[0]
            location_temp_raw.at[lb_outlier_index, "TEMP_CELSIUS"] = None
        # Backfilling the temperature
        location_temp_full = back_filling_temperatures_pipeline(
            location_temp_raw)
        # Filling in additional data
        location_temp_final = fill_aux_data(
            location_temp_full, stream, census_div)
        location_temps.append(location_temp_final)

    temps_final = pd.concat(location_temps)

    # Generate column with values for the year
    temps_final["Year"] = [
        int(begin_time.year) for begin_time in temps_final["BEGIN_DATE_GMT"]]

    # Read in population data
    population_data = pd.read_csv("cleaned data/Population 2010-2046.csv")

    # Weight temperature by population based on the given temperature column
    # Example name of resulting columns: BFILL_weighted_pop_high
    # => temperature data that has been back filled and weighted according to high population estimates

    weighted_temp = temps_final.merge(
        population_data, on=['Year', 'Region'], how='left')

    # temp_col = "BFILL_TEMP_CELSIUS"
    # for pop_col in ["pop_high", "pop_low", "pop_medium"]:
    #     weighted_temp[temp_col.replace("_TEMP_CELSIUS", "") +
    #                   "_weighted_" + pop_col] = weighted_temp[temp_col] * weighted_temp["pct_"+pop_col]
    # weighted_temp.sort_values(["BEGIN_DATE_GMT", "Region"], inplace=True)

    weighted_temp.rename(str.upper, axis='columns', inplace=True)

    # Replacing names for convenience
    weighted_temp.replace({'EC - Calgary Temp': 'CALGARY',
                           "EC - Edmonton Temp": 'EDMONTON',
                           "EC - Fort McMurray Temp": "FORTMM",
                           "EC - Lethbridge Temp": "LETHBRG"}, inplace=True)
    # Dropping unncessary column
    weighted_temp_wide = weighted_temp.drop(
        columns=["YEAR", "REGION"]).reindex()

    # Pivot table to wide format
    weighted_temp_wide = weighted_temp_wide.pivot_table(index='BEGIN_DATE_GMT', columns="NRG_STREAM_NAME",
                                                        margins=False)
    weighted_temp_wide.columns = weighted_temp_wide.columns.map(
        '|'.join).str.strip('|')
    weighted_temp_wide.drop(columns=["UNNAMED: 0|CALGARY",
                                     "UNNAMED: 0|EDMONTON",
                                     "UNNAMED: 0|FORTMM", "UNNAMED: 0|LETHBRG"], inplace=True)
    # Write results to csv
    weighted_temp_wide.to_csv("cleaned data/WF_Weighted Temp 2010-2021.csv")
