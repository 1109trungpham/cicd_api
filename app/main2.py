import pandas as pd
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, Response
import xarray as xr
import time
import bz2
import json
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

@app.post("/weather")
async def get_weather(
    file: UploadFile = File(..., description="CSV file with lon,lat columns"),
    start_year: int = Query(..., description="Start year"),
    end_year: int = Query(..., description="End year"),
    output_format: str = Query("json", description="Output format: json or bz2")
):
    start_time = time.time()

    # Đọc file CSV
    df_coords = pd.read_csv(file.file)
    if not {"lon", "lat"}.issubset(df_coords.columns):
        return JSONResponse(
            status_code=400,
            content={"error": "CSV must contain 'lon' and 'lat' columns"}
        )

    filepath = 'https://nasa-power.s3.amazonaws.com/merra2/temporal/power_merra2_daily_temporal_lst.zarr'
    ds = xr.open_zarr(filepath, consolidated=True)

    variables = ['T2M_MAX', 'T2M_MIN', 'PRECTOTCORR']
    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-01-31"

    responses = []

    for _, row in df_coords.iterrows():
        lon, lat = row["lon"], row["lat"]

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
    result = WeatherMultiResponse(duration=round(duration, 2), data=responses)

    # Xuất kết quả theo định dạng
    if output_format == "bz2":
        compressed = bz2.compress(json.dumps(result.dict()).encode("utf-8"))
        return Response(content=compressed, media_type="application/x-bzip2")
    else:
        return JSONResponse(content=result.dict())
