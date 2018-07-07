import numpy as np
import pandas as pd
import scipy.stats as scs
import matplotlib.pyplot as plt
import os
import math
import folium

def load(pathname, metric):
  """Load the individual time series of csv files from the results dir given
  in pathname for the metric given in metric (e.g. 'TAVG')

  Inputs:
    pathname    string  pathname of results directory holding csv files
    metrics     string  metric for time series CSV files, e.g. 'TAVG'
  Output:
    a dictionary whose keys are FIPS place codes and whose values are another
    dict with keys for 'sequence' containing dataframe for its metric seq,
    'name' for its county name, 'state' for its USPS state abbreviation, 'lat' for
    its latitude, 'long' for its longitude, 'month' for the month of the year
    the sequence covers, startyear of the sequence, and endyear of the
    sequence.
  """
  counties = pd.read_csv('../data/US_counties.csv')

  seqs = dict()
  filenames = os.listdir(pathname)
  for filename in filenames:
      parts = filename.split('_')
      if parts[0] != metric:
          continue
      seq = pd.read_csv(pathname+filename)
      seq = seq.set_index('date')
      geocode = parts[1]
      month = parts[2]
      startyear = parts[3]
      endyear = parts[4]
      seqs[geocode] = {
        'sequence' : seq,
        'name' : counties[counties.geoid == int(geocode)].iloc[0]['name'],
        'state' : counties[counties.geoid == int(geocode)].iloc[0]['usps'],
        'lat' : counties[counties.geoid == int(geocode)].iloc[0]['lat'],
        'long' : counties[counties.geoid == int(geocode)].iloc[0]['long'],
        'month' : month,
        'start' : startyear,
        'end' : endyear
      }
  return seqs

def analyze(places,window=30):
    """For each place in places dict, compare first and last periods of its
    time series. The length of each period is given by window.

    Inputs:
        places  dict    key is a FIPS place code, value is another dict
                        containing the place's
    """
    for property_list in places.values():
        seq = property_list['sequence']
        if seq.shape[0] < (2*window):
            continue
        tresult = scs.ttest_ind(seq[-window:], seq[:window])
        property_list['TTest2'] = tresult
        tstat = tresult.statistic[0]
        pval = tresult.pvalue[0]
        # So, the real question in people's minds is whether it is warming up,
        # which calls for a one-sided T Test. The scipy.stats ttest_ind func
        # performs a two sided test. For a one-sided end period warmer than
        # initial period test, we need to verify that the t statistic is > 0
        # (it is not for some counties, e.g. Boulder CO) and then if we want
        # a one sided 1% test, we need to double p since we don't care about the
        # other tail. Also, since some counties like Boulder are cooler now, we
        # may as well perform the other one-tailed test to see if the climate
        # is cooling.
        if tstat >= 0: # warmer
            if pval <= 0.02: # for a 1% one sided test
                indicator = 'H'
            elif pval <= 0.2: # for a 10% one sided test
                indicator = 'W'
            else:
                indicator = 'N' # neutral
        else: # tstat < 0 so we may as well do a one sided test on global cooling
            if pval <= 0.02:
                indicator = "F" # frigid
            elif pval <= 0.2:
                indicator = "C" # cooler
            else:
                indicator = "N" # neutral
        property_list['indicator'] = indicator

    return places # updated with T Test results

def map_it(places):

    # There are two objects of interest, the Map and its Markers.
    # You instantiate a Map around some lat, long. By default
    # you only get the immediate area, but you can override this
    # with the optional zoom_start parameter. In this case, we
    # want to see the entire USA.
    geo_center_of_US = [40.0, -100.0]
    map = folium.Map(location=geo_center_of_US,zoom_start=4,tiles='Stamen Terrain')

    ind_to_color = {
        'H' : 'red',
        'W' : 'pink',
        'N' : 'green',
        'C' : 'light blue',
        'F' : 'blue'
        }
    for plist in places.values():
        lat = float(plist['lat'])
        long = float(plist['long'])
        ind = plist['indicator']
        color = ind_to_color[ind]
        name = plist['name']+ ', ' + plist['state']
        marker = folium.Marker(
            location=[lat,long],
            popup=name,
            icon=folium.Icon(color=color,icon='cloud')
            )
        marker.add_to(map)
    return map

if __name__ == '__main__':
    seqs = load('../data/results/','TAVG')
    seqs = analyze(seqs)
    map = map_it(seqs)
    map.save('../images/results.html')
