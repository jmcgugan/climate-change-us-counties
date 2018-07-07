# Analytics Capstone: *Prove Climate Change Yourself*

>## Problem Statement
>Long observational records of high-resolution weather data, constitute over time, the basis of our understanding of the global climate. Climate is the signal, weather is the noise.
>
>National weather services and climate information centers such as the U.S. National Oceanic and Atmospheric Administration (NOAA), Britain’s Met Office, and India’s Institute for Tropical Meteorology (IITM), collect, curate, analyze and publish meteorological data from thousands of weather stations globally. NOAA’s National Climatic Data Center (NCDC) is the world’s largest archive of weather data.
>
>NOAA scientists offer a wealth of meteorological/climatological information through the NCDC data portal. The data is available three-ways:
>(1) [Online Climate Data Directory website](https://www.ncdc.noaa.gov/cdo-web/), for high-level exploration.
>(2) [FTP](ftp://ftp.ncdc.noaa.gov/pub/data/noaa/) for bulk downloads.
>(3) >[API](https://www.ncdc.noaa.gov/cdo-web/webservices) for flexible queries, which is the method we will use here.
>
>### How to use the NOAA API
>Request an API token here: https://www.ncdc.noaa.gov/cdo-web/token
Add your token to your `~/.bash_profile` or `~/.bash_rc`:
```
export NOAA_API_KEY='<your token here>'
```
>
>Use API token as authentication in get request (below):
```
api_key = os.environ['NOAA_API_KEY']
headers = {'token': api_key}
```
>
>Consult API documentation on how to make requests:
https://www.ncdc.noaa.gov/cdo-web/webservices/v2
>
>### Sample queries
Fetch data about all available datasets  
`query = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets"`
>
>Fetch all information about the GSOY dataset specifically  
`query = "https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets/GSOY"`
>
>Fetch data from the GSOM dataset (Global Summary of the Month) for GHCND station USC00010008, for May of 2010  
`query = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GSOM&stationid=GHCND:USC00010008&&startdate=2010-05-01&enddate=2010-05-31"`
>
>### Make a request
```
response = requests.get(query, headers = headers)
response = response.json()
pprint(response)
```
>
>### Generalize
>Break query into consituent parts: endpoint + parameters.
>Specify parameters with a dictionary (easier to read and reproduce):
```
endpoint = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data?"
payload = {
    'datasetid': 'GSOM',
    'stationid': 'GHCND:USC00010008',
    'startdate': '2010-05-01',
    'enddate': '2010-05-31'
}
response = requests.get(endpoint, headers=headers, params=payload)
response = response.json()
pprint(response)
```

# Rubbish! None of the above works!!!

## Part 1: The EDA

## Three Days on the API

1. The doc claims you can ask for a sequence over multiple years. Not so! You get a 400 HTTP error if you ask for more than a few years, but where it occurs is variable. I found the only reliable method is to ask for data within a single year and then sew it together myself.

2. The doc claims you can ask for only specified data items. Not so! You get everything—dew point, precipation, snowfall…—even if you only ask for temperatures. You have to filter the list yourself.

3. The doc claims you can fetch in batches starting from item 0, but the indexing actually starts from item 1. However if you ask for a batch starting from item 0, it silently gives you a batch starting from item 1, which throws off your count for future batches.

4. The doc claims if there is no data for a requested time period, it will still give you a json metadata item with a count of 0. Nope. You get a completely empty json response.

5. Once you get through all these problems, though, you hit the real problem: if the server is busy, it just gives you back an empty json response. Note that it also gives you an empty json if there is really no data for that collection period. You cannot distinguish the two cases.

## The Resolution

I had originally written a straight-through processing pipeline that collected the data on 52 US counties for 118 years and compared the beginning of the period with the end.

Given the flakiness of the NOAA server, I had to rearchitect. I broke it into two parts:

1. A process that "shops" for data. It tries to iterate through a list of US counties and collect a complete sequence for them. If it cannot (empty json), it moves on to the next. One pass through a list of 52 counties yields about six to eight successes. The shopping process writes each successful collection to a csv file. Gradually I hope to complete a set of US counties but it will require many attempts.

2. There is now a separate analysis process that reads the available county temperature sequences off of disk, compares the first 30 years of the sequence with the last and concludes (T Test) whether the later period is the same, hotter, or cooler than the earlier period. This is implemented with a pair of one tailed T Tests.


## Part 2: The Analysis

>### From the Problem Statement…
>
>#### Collect data to answer your research question
>* what data do you need? Temperature? Precipitation? Cloud Cover?
>* when do you need data for? Last ten years? 100 years?
>* where do you need data for? Global land surfaces? Sea surface? Specific continent? Single weather station?
>* what level of aggregation / preprocessing do you want? Hourly? Daily? Monthly? Annual? Station-level? Gridded? Raw? Standardized?
>* Think strategically about the questions above, write out what you want on paper, then figure out the get request that will (hopefully) return that information.
>* Can you get it all in one-shot with a single get request? Or will you have to make many requests?
>* Consider how "big" your data will be. How will you handle it as it comes in and once it's time to analyze.
>
>#### Create a hypothesis and test it against your data
>* Write down your research question in English.
>* Translate your research into a formal hypothesis.
>* State your null and alternate.
>* Determine the appropriate test-statistic and correction factor (if required).
>* Run your experiment.
>* Interpret results.
>
>Consider both Frequentist and Bayesian framings of the same research question.
For example:
>* Has the distribution of global mean surface temperatures changed between two sample periods (e.g. frequentist t-test of 1900-1950 compared to 1950-2016)
>* Was there a switchpoint (or two?) in global mean surface temperatures in the period 1900-2016? If so, when? (e.g. Bayesian switchpoint analysis).


### Plan of Attack

1. Collect July average temperatures for multiple US counties from 1900 to 2017.

2. Compare the first 30 years against the last 30. The Null Hypothesis is that the climate is not getting warmer. The Alternate Hypothesis is that it is.

I initially performed a two-sided test, but later did a one-sided test, i.e. is the climate warmer? But there was one tricky county (Boulder, CO) which is actually cooler. In the end, I did a pair of one-sided tests, one for warmer and one for cooler.

### Results

The map is color coded as follows:
* Red means a one-sided p-value for a warmer climate < 1%
* Pink means a one-sided p-value for a warmer climate < 10%
* Green means neutral
* Light blue means a one-sided p-value for a cooler climate < 10%
* Blue means a one-sided p-value for a cooler climate < 1%

[Results Map](images/results.html)
