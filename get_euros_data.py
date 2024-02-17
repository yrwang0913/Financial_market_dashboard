
import datetime as dt
from functools import reduce
import pandas as pd
from pandas_datareader.fred import FredReader
import requests


start_date = "1990-01-01"

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

# def get_ez_gdp_data():
    

# def get_eu_inflation_data():
#     #EU uses harmonised CPI to measure inflation
    
#     euhicp = "CPHPTT01EZM659N"
#     dehicp = "CPHPTT01DEM659N"
#     frhicp = "CPHPTT01FRM659N"
#     ithicp = "CPHPTT01ITM659N"
    
    
    

if __name__ == "__main__":
    
    eurtwd_data = get_eurtwd_data()
    
    ecb_i_data = get_ecb_i_data()
    
    useu_10yy_data = get_10YY_data()
    
    data = pd.concat([
        eurtwd_data, 
        ecb_i_data, 
        useu_10yy_data
        ], axis=1)
    
    data.to_excel("euros_data.xlsx")