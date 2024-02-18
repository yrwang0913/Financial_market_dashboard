
from countrygroups import EUROPEAN_UNION
import datetime as dt
import openpyxl
import pandas as pd
from pandas_datareader.fred import FredReader
import pycountry
import requests

# Define the start date for economic data
start_date = "1990-01-01"

# Define the Eurozone countries list for data
eu_countries = EUROPEAN_UNION.names

to_exclude = [
    "Bulgaria", "Czechia", "Cyprus", "Denmark", "Estonia", "Hungary", 
    "Latvia", "Lithuania", "Malta", "Poland", "Slovakia", "Slovenia",
    "Croatia", "Ireland" # Ireland for name code reason, we will include its data separately
    ]

for country in to_exclude:
    eu_countries.remove(country)

ez_short = []   # Get the short codes of the countries in list
for country in eu_countries:
    country_short = dict(pycountry.countries.lookup(country))['alpha_2']
    ez_short.append(country_short)
    
ez = dict(zip(eu_countries, ez_short))


def get_eurtwd_data():
    finmind_url = "https://api.finmindtrade.com/api/v4/data"

    parameter_eur = {
        "dataset": "TaiwanExchangeRate",
        "data_id": "EUR",
        "start_date": start_date,
    }

    eurtwd_data = requests.get(finmind_url, params=parameter_eur).json()
    eurtwd_data = pd.DataFrame(eurtwd_data['data']).set_index('date')
    eurtwd_data.index = pd.DatetimeIndex(eurtwd_data.index)
    
    # Impute missing data (-1) with the previous value
    eurtwd_data = eurtwd_data.replace(-1, method="ffill")
    return eurtwd_data
    
def get_ecb_i_data():
    ecbrate = "ECBMRRFR" # Main Refinancing Operations Rate
    ecb_i_data = FredReader(ecbrate, start=start_date).read()
    ecb_i_data.rename(columns={"ECBMRRFR":"EZ_rate_mro"})
    return ecb_i_data

def get_10YY_data():
    us10yy = "DGS10"
    eu10yy = "IRLTLT01EZM156N"
    us10yy_data = FredReader(us10yy, start=start_date).read()
    eu10yy_data = FredReader(eu10yy, start=start_date).read()
    tenYY_data = pd.concat([us10yy_data, eu10yy_data], axis= 1)
    tenYY_data.rename(columns={"DGS10": "US10YY", "IRLTLT01EZM156N": "EU10YY"}, inplace=True)
    
    return tenYY_data

def get_ez_gdp_data():
    #Greece's EU shortcode is EL, not GR
    ez["Greece"] = "EL"

    gdp_data_list = []
    
    for country, shortname in ez.items():
        gdpticker = f"CPMNACSCAB1GQ{shortname}" 
        gdpdata = FredReader(gdpticker, start=start_date).read()
        gdpdata.rename(columns={gdpticker:'GDP'}, inplace=True)
        gdpdata['Country'] = country
        gdpdata.reset_index(inplace=True)
        gdp_data_list.append(gdpdata)
    
    # Ireland and EZ have different codes, so we'll get them separately
    irgdp = "CPMNACSAB1GQIE"
    ir_gdp_data = FredReader(irgdp, start=start_date).read()
    ir_gdp_data.rename(columns={irgdp:'GDP'}, inplace=True)
    ir_gdp_data['Country'] = 'Ireland'
    ir_gdp_data.reset_index(inplace=True)
    gdp_data_list.append(ir_gdp_data)
    
    ezgdp = "EUNNGDP"
    ez_gdp_data = FredReader(ezgdp, start=start_date).read()
    ez_gdp_data.rename(columns={ezgdp:'GDP'}, inplace=True)
    ez_gdp_data['Country'] = 'Eurozone'
    ez_gdp_data.reset_index(inplace=True)
    gdp_data_list.append(ez_gdp_data)
    
    gdp_data = pd.concat(gdp_data_list, axis=0)
    gdp_data.set_index('DATE')
    return gdp_data
    
def get_eu_inflation_data():    #EU uses harmonised CPI to measure inflation
    # Greece's short code here should be GR
    ez['Greece'] = 'GR'
    del ez['Romania']
    
    hicp_data_list = []
    
    for country, shortname in ez.items():
        hicpticker = f"CPHPTT01{shortname}M659N"
        hicpdata = FredReader(hicpticker, start=start_date).read()
        hicpdata.rename(columns={hicpticker:'HICP'}, inplace=True)
        hicpdata['Country'] = country
        hicpdata.reset_index(inplace=True)
        hicp_data_list.append(hicpdata)
    
    # Ireland, Romania and EZ have different codes, so we'll get them separately
    ir_ro_ez = {"Ireland": "IE", "Romania": "RO", "Eurozone": "EZ19"}
    for country, shortname in ir_ro_ez.items():
        hicpticker = f"CP0000{shortname}M086NEST"
        hicpdata = FredReader(hicpticker, start=start_date).read()
        hicpdata.rename(columns={hicpticker:'HICP'}, inplace=True)
        hicpdata['Country'] = country
        hicpdata.reset_index(inplace=True)
        hicp_data_list.append(hicpdata)
    
    hicp_data = pd.concat(hicp_data_list, axis=0)
    hicp_data.set_index('DATE', inplace=True)
    return hicp_data

if __name__ == "__main__":
    
    print("Ready to get the data ...")
    # Sheet 1
    print("Getting EUR/TWD data ...")
    eurtwd_data = get_eurtwd_data()
    print("Data Get!")
    
    print("Getting ECB rate and Gov Yield data ...")
    ecb_i_data = get_ecb_i_data()
    
    useu_10yy_data = get_10YY_data()
    print("Data Get!")
    
    currency_rate_data = pd.concat([
        eurtwd_data, 
        ecb_i_data, 
        useu_10yy_data
        ], axis=1)
    
    # Sheet 2
    print("Getting GDP data ...")
    ez_gdp_data = get_ez_gdp_data()
    print("Data Get!")
    
    print("Getting CPI data ...")
    ez_hicp_data = get_eu_inflation_data()
    print("Data Get!")

    gdp_hicp_data = ez_gdp_data.merge(ez_hicp_data, how="outer", on=["DATE", "Country"])
    gdp_hicp_data.set_index("DATE", inplace=True)
    
    print("Exporting Data ...")
    
    # Export Excel
    with pd.ExcelWriter("euros_data.xlsx") as writer:
        currency_rate_data.to_excel(writer, sheet_name="Euros and Rates")
        gdp_hicp_data.to_excel(writer, sheet_name="EZ GDP and HICP")
        
    print("Data Exported!")