import numpy as np
import pandas as pd
import requests
import os

def get_month_seq(location, month, metric='TAVG', startyear=1900, endyear=2017):
    """Get sequence of climate metrics for the same month in successive years.

    Inputs:
        location    <str> FIPS location id. 5 digits for US county. 2 for state.
        month       <str> month encoded as 2 digit string, e.g. July is '07'.
        metric      <str> NOAA climate metric, e.g. 'TAVG' for average temp.
        startyear   <int> first year of sequence.
        endyear     <int> end year of sequence (imclusive)
    Output:
        Pandas DataFrame indexed by date with values equal to the average
        of the metric across all stations in the location code for that month.
    """
    datasetid = 'GSOM' # Global Summary of Month. Contains monthly averages by station.
    batchlimit = 1000 # Maximum batch size permitted per NOAA CDO API documentation.
    result = pd.DataFrame()
    endpoint = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data?"
    headers = {'token' : os.environ['NOAA_API_KEY']}
    payload = {
        'datasetid': datasetid,
        'locationid': location,
        'offset' : 1,
        'limit' : batchlimit,
        'units' : 'metric'} # If we don't specify a unit, sometimes we get C, sometimes F.

    for year in range(startyear, endyear+1):
        payload['startdate'] = str(year) + '-' + month + '-01'
        payload['enddate'] = payload['startdate']
        offset = 1
        payload['offset'] = offset
        count = batchlimit  # just to get started; first call will tell us how many
        while offset <= count:
            print('Year: ' + str(year) + ' Fetching at offset' + str(offset) + ' Count: ' + str(count))
            response = requests.get(endpoint, headers=headers, params=payload)
            if response.status_code != 200:
                print('Response Code from NOAA is: '+ str(response.status_code)+ ' Aborting this collection.')
                return pd.DataFrame()
            if len(response.json()) == 0:
                print('Response body empty. Aborting this collection.')
                return pd.DataFrame()
            count = response.json()['metadata']['resultset']['count'] # true count
            batch = pd.DataFrame.from_records(response.json()['results'])
            batch = batch[batch['datatype'] == metric]
            batch = batch.drop(columns=['attributes','station','datatype'])
            result = result.append(batch)
            offset = offset + batchlimit
    return result.groupby('date').mean()

def write_month_seq(place_code, month, metric='TAVG', startyear=1900, endyear=2017):
    """Get sequence of temps for a place for a given month in each year between
    startyear and endyear (inclusive).

    Inputs:
        place_code: integer FIPS place code for a US county. 4 or 5 digits.
        month:      string representation of month, e.g. '07' for July
        metric:     string e.g 'TAVG', 'TMIN', 'TMAX'
        startyear:  integer
        endyear:    integer
    returns:
        None (but does write a file)
    """
    if place_code < 10000:
        code = 'FIPS:0' + str(place_code)
    else:
        code = 'FIPS:' + str(place_code)
    print('\nFetching sequence for: ' + code)
    filename = '../data/results/' + metric + '_' + str(place_code) + '_' + month + '_' +str(startyear) + '_' + str(endyear) + '.csv'
    if os.path.isfile(filename):
        print('Output file ' + filename + ' already exists. Skipping collection.')
        return
    result = get_month_seq(code, month, metric=metric, startyear=startyear, endyear=endyear)
    if result.shape[0] > 0:
        result.to_csv(filename)
    else:
        print('Collection failed. No output file generated.')

# Note prep_data works but I have abandoned it because the NOAA site gets
# overloaded and then starts throwing either an empty json response body,
# which is the common case, or sometimes a 503 (server busy) HTTP error.
def prep_data(places, month, metric='TAVG', startyear=1900, endyear=2017):
    """ For a list of places, compile a temperature sequence for the same
    month in successive years.
    """
    first = True
    for place_name, place_code in places.items():
        if place_code < 10000:
            code = 'FIPS:0' + str(place_code)
        else:
            code = 'FIPS:' + str(place_code)
        seq = get_month_seq(code, month, metric, startyear, endyear)
        if seq.shape[0] == 0:
            continue
        label = str(place_code)
        print('Generated sequence for: ' + label)
        seq.rename(columns = {'value': label}, inplace = True)
        if first:
            result = seq
            first = False
        else:
            result = result.merge(seq, left_index=True, right_index=True, how='outer')
    return result

# This code also works but has been abandoned because NOAA freezes up before
# it can complete.
def get_1_per_state():
    """ Return a cosolidated dataframe with a teperature sequence for one
    county from each state
    """
    places = dict()
    for state in counties.usps.unique():
        name = counties[counties.usps == state].iloc[0].name
        fips = counties[counties.usps == state].iloc[0].geoid
        places[name] = fips
    return prep_data(places, '07', startyear=1900, endyear=2017)

if __name__ == "__main__":
    counties = pd.read_csv('../data/US_counties.csv')
    places = []
    for state in counties.usps.unique():
        fips = counties[counties.usps == state].iloc[0].geoid
        places.append(fips)
    for place in places:
        write_month_seq(place,'07',startyear=1900,endyear=2017)
