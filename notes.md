final github structure
  data
  src
  tests
  notebooks
  images
  readme.md

General topics for readme:
  question trying to answer
  data source
  eda
  feature engineering
  modeling
  results
  future work
  references


# Plan of Attack
* Get data
  - API key
  - explore in NOAA
* write function to get sequence of temps for a location
    ``` get_temp_seq(
          city_or_county,
          month,
          start = <first_avail>,
          end = <latest_avail>
      )
    ```
* hypothesis test: is temp higher at end of seq than beginnning?
  - first decade versus last decade in sequence
  ``` prob_temp(temp_seq)
  ```
  returns p value
* Can we predict avg temp in next decade?
  - try fitting various regression models to the temp sequence
  - how good is the fit
