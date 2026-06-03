# Build Airspace Data Sources

June 3, 2026 - Build Airspace documentation MVP version 1.0



## **DAHminimap.html** - documenting data structures & sources

* ca_asp  
* ca_apt 

get these GeoJSON files. 

Data sources: **OpenAIP** 

1. ca_asp.geojson
2. ca_apt.geojson



Output file target name: **dah_gold_airspace.geojson**

Destination folder  for repo: **Drone_SOP/data/airspace**

Our code has fallback lookup to ca_apt.geojson







## Canada Airspace, Airports retrieval

[OpenAIP - Data Exports](https://www.openaip.net/data/exports?page=1&limit=50&sortBy=createdAt&sortDesc=true&format=geojson&contentType=airspace%2Cairport&country=CA&failed=false) 

```
https://www.openaip.net/data/exports?page=1&limit=50&sortBy=createdAt&sortDesc=true&format=geojson&contentType=airspace%2Cairport&country=CA&failed=false
```

Canada Airspace, Airports retrieval


Canadian Airspace - OpenAir (https://airspace.canadarasp.com)

https://airspace.canadarasp.com/OpenAirFiles/canadian_airspace.air 



### Scripts (build_canadian_airspace_geojson.py)

- `scripts/build_canadian_airspace_geojson.py`

The builder accepts:

- local GeoJSON, OpenAIP object-array JSON, ND-GeoJSON, remote `http/https` URLs

call with: 
"python scripts/build_canadian_airspace_geojson.py --input ca_asp.geojson --output data/canadian_airspace.geojson --classes B,C,D,E,F "



## Refresh Airspace data sources

C:/Program Files/Python312/python.exe" scripts/refresh_airspace_data.py --help 



canadian_airspace.air

