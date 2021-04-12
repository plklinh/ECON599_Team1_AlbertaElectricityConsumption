# Alberta Internal Load Estimation

This is a Python project to estimate Alberta's Electricity Consumption based on temperature and other relevant variables

## Preparation

We recommend making a new python environment before doing intalling requirements, but it is not required. See [pip documentations](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) for how to do this using pip, or [anaconda documentations](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment) for conda.

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```

## Data

The AIL, pool price, temperature and oil prices data in **original data** was provided to us by the MSA. Population estimations were downloaded from [Alberta Open Data portal](https://open.alberta.ca/opendata/alberta-population-projections-2020-2046-alberta-census-divisions-and-economic-regions-data-tables).

## Usage

Please note **msa_merged_data.csv** contains already cleaned data. The cleaning scripts do not have be reran, but you can change specifications in the script to alter this final csv file.

Python scripts (.py files) can be run from command line

```bash
python file_name.py
```

Jupyter Notebooks (.ipynb) files require Jupyter, Visual Studio Code (with Jupyter extension) or similar development software.

### 1. Data Cleaning:

- **clean_oil_data.py**, **clean_population_data.py**, **clean_temperature_script.py** can be run any order. Afterwards, run **merge_full_data.py**

- **clean_oil_data.py** compile the spot and future prices into one data frame and converts them to CAD. Output to **cleaned data/Oil Prices 2010-2021 CAD.csv**

- **clean_population_data.py** filters out population data for Calgary, Edmonton, Fort McMurray and Lethbridge and calculate their relative weights. Output to **cleaned data/Population 2010-2046.csv**

- **clean_temperature_script.py** backfills missing temperature values. Output to **cleaned data/WF_Weighted Temp 2010-2021.csv**

- **merge_full_data.py** merges previously cleaned data files, generates additional dummy variables and calculates new temperature-related variables (average temperature, population weighted average temperature and per-hour heating/cooling degree days). Output to **msa_merged_data.csv**

### 2. Modelling:

- All the following files require **msa_merged_data.csv**

- Estimations were done using [Facebook Prophet](https://facebook.github.io/prophet/docs/quick_start.html). Other models using VAR and XGBoost can be found in **other models**

- If fbprophet>=0.7.1 could not be installed, use pickle for saving and loadingfitted models

- **FullModel_FB_Prophet.ipynb** contains code to fit a prediction model using 2010-2019 data as the training set and 2020 data as test. Output trained models to **pickled_model** and **serialized_model.json**.

- **normalize_2020_predictions.py** produces various AIL forecasts for 2020. Output to **forecasted_2020_data.csv**

- **refit_model.py** has code to demonstrate how to refit a new model using more data and parameters from a pretrained model

- **CrossValidate_FB_Prophet.ipynb** has older version of some functions and model specifications. This file is to illustrate how cross validation can be done using FBProphet. It is not necessary to run this.

### 3. Visualizations

- Visualizations were made using [Plotly](https://facebook.github.io/prophet/docs/quick_start.html) and [Dash](https://plotly.com/dash/)

- **viz_exploratory_data.py** uses **msa_merged_data.csv**. Produces dashboard with graph exploring data from 2010 to 2020.

- **viz_summary_2020.py** uses both **msa_merged_data.csv** and **forecasted_2020_data.csv**. Produces dashboard with graphs summarizing mainly 2020.

- After running python command, follow the output link to view dashboard. Example command line output after running either file.

```bash
Dash is running on http://127.0.0.1:8000/

 * Serving Flask app "__main__" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:8000/ (Press CTRL+C to quit)
```

- The Server's host and port can be changed from within each script.

- Please remember to press CTRL+C in command line to close server.
