import pandas as pd
from file_interpeter import prepare_data, create_quotation_file

pricelist = pd.read_excel('static/2025_CLAAS.xlsx')

def do_claas_quotation(filename, details):
    data = prepare_data(filename,details['brand'])
    for code in data['codes']:
        month_price=pricelist.loc[pricelist["Part"] == float(code), "Monthly"]
        week_price=pricelist.loc[pricelist["Part"] == float(code), "Weekly"]
        data['monthly_prices'].append(month_price.values[0])
        data['weekly_prices'].append(week_price.values[0])
    file_name = create_quotation_file(data,filename)
    return file_name


