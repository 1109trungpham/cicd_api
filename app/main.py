import pandas as pd
from fastapi import FastAPI, Query
import xarray as xr
import time
from pydantic import BaseModel
from typing import List

class WeatherResponse(BaseModel):
    header: List[str]
    value: List[List[float]]
    location: List[float]

class WeatherMultiResponse(BaseModel):
    duration: float
    data: List[WeatherResponse]

app = FastAPI()

@app.get("/weather", response_model=WeatherMultiResponse)
async def get_weather(
    lons: str = Query(..., description="Comma-separated longitudes"),
    lats: str = Query(..., description="Comma-separated latitudes"),
    start_year: int = Query(..., description="Start year"),
    end_year: int = Query(..., description="End year")
):
    start_time = time.time()
    """ 
    input: batch{csv}
    output:{{location}}
    *.bz2
    """
    lon_list = [float(x.strip()) for x in lons.split(',')]
    lat_list = [float(x.strip()) for x in lats.split(',')]

    if len(lon_list) != len(lat_list):
        raise ValueError("Number of longitudes and latitudes must match")

    filepath = 'https://nasa-power.s3.amazonaws.com/merra2/temporal/power_merra2_daily_temporal_lst.zarr'
    ds = xr.open_zarr(filepath, consolidated=True)

    variables = ['T2M_MAX', 'T2M_MIN', 'PRECTOTCORR']
    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-01-31"

    responses = []

    for lon, lat in zip(lon_list, lat_list):
        df = ds[variables].sel(
            lat=lat,
            lon=lon,
            method="nearest"
        ).sel(time=slice(start_date, end_date)).to_dataframe()

        df = df.reset_index()
        df['day'] = df['time'].dt.day
        df['month'] = df['time'].dt.month
        df['year'] = df['time'].dt.year
        df['day_of_year'] = df['time'].dt.dayofyear

        df = df[['day', 'month', 'year', 'day_of_year', 'T2M_MAX', 'T2M_MIN', 'PRECTOTCORR']]

        values = df.values.tolist()

        responses.append(WeatherResponse(
            header=["day", "month", "year", "day_of_year", "t2m_max", "t2m_min", "precipitation"],
            value=values,
            location=[lon, lat]
        ))

    duration = time.time() - start_time

    return WeatherMultiResponse(duration=round(duration, 2), data=responses)
