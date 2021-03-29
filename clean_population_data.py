import pandas as pd
import numpy as np

CENSUS_DIVISION = ["2", "6", "11", "16"]

"""
Return population data from 2010 onwards for all sexes ("Sex" == 3)and all ages ("Age" == Total).
Also generate a column with census division code
------------
Input:
    -  df: Pandas DataFrame
        population data frame with columns ["Year" , "Sex", "Total", etc... ]
Returns:
    - Pandas Dataframe
    
"""


def base_filter(df):
    period = (df["Year"] >= 2010)
    in_4_metros = df["Region"].apply(lambda x: x in CENSUS_DIVISION)
    conditions = period & in_4_metros & (
        df["Sex"] == "3") & (df["Age"] == "Total")

    return df[conditions][df.columns.difference(["Sex", "Age"])]


"""
Return new population dataframe with percentages based on givenpopulation estimates 
------------
Input:
    -  pop_df: Pandas DataFrame
        filtered population data frame
    - pop_col: String
        name of population column to calculate percentages
Returns:
    - Pandas Dataframe
"""


def gen_pop_pct(pop_df, pop_col):
    # Calculate total populations for each year
    pop_by_year = pop_df.groupby(['Year', 'Region']).agg({pop_col: 'sum'})
    # Calcualte Percentages
    pop_pct = pop_by_year.groupby(level=0).apply(lambda x: x / float(x.sum()))
    return pop_pct.reset_index()


if __name__ == "__main__":
    # Reading in population data
    pop_low_growth = pd.read_csv("original data/2020-2046-05-census-divisions-population-projections-low.csv",
                                 dtype={'Year': int, 'Region': str, 'Sex': str, 'Age': str, 'Pop': int})

    pop_med_growth = pd.read_csv("original data/2020-2046-07-census-divisions-population-projections-medium.csv",
                                 dtype={'Year': int, 'Region': str, 'Sex': str, 'Age': str, 'Pop': int})

    pop_high_growth = pd.read_csv("original data/2020-2046-09-census-divisions-population-projections-high.csv",
                                  dtype={'Year': int, 'Region': str, 'Sex': str, 'Age': str, 'Pop': int})

    # Combining the sperate projections into one data frame
    pop_full = pd.DataFrame(data={"Year": pop_low_growth["Year"],
                                  "Region": pop_low_growth["Region"],
                                  "Sex": pop_low_growth["Sex"],
                                  "Age": pop_low_growth["Age"],
                                  "pop_low": pop_low_growth["Pop"],
                                  "pop_medium": pop_med_growth["Pop"],
                                  "pop_high": pop_high_growth["Pop"]
                                  })
    pop_metros = base_filter(pop_full)
    pop_metros_sorted = pop_metros.sort_values(["Year", "Region"])

    # Generating population percentages based on each estimate
    for pop_col in ["pop_high", "pop_low", "pop_medium"]:
        pop_pct = gen_pop_pct(pop_metros_sorted, pop_col).sort_values(
            ["Year", "Region"])
        pop_metros_sorted["pct_" +
                          pop_col] = [pct for pct in pd.Series.copy(pop_pct[pop_col])]
    pop_metros_sorted.reset_index(inplace=True, drop=True)
    # Writing final data frame to csv
    pop_metros_sorted.to_csv(
        "cleaned data/Population 2010-2046.csv")
