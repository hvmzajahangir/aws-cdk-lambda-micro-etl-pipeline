import requests
import pandas as pd
import boto3
import os
import io
from datetime import date, timedelta


def filter_last_week(df):
    """
    Filter dataframe to only include last week's daily stock data
    """
    tmp_df = df.copy()
    today = date.today()
    last_week_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    last_week_end = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    is_last_week = (tmp_df["timestamp"] >= last_week_start) & (tmp_df["timestamp"] <= last_week_end)
    tmp_df = tmp_df[is_last_week]
    return tmp_df


def add_aggregate_weekly_statistics(df):
    """
    Add columns for average, median, min and max close / volume to the dataframe
    """
    tmp_df = df.copy()
    tmp_df["avg_weekly_close"] = tmp_df["close"].mean()
    tmp_df["median_weekly_close"] = tmp_df["close"].median()
    tmp_df["min_weekly_close"] = tmp_df["close"].min()
    tmp_df["max_weekly_close"] = tmp_df["close"].max()

    tmp_df["avg_weekly_volume"] = tmp_df["volume"].mean()
    tmp_df["median_weekly_volume"] = tmp_df["volume"].median()
    tmp_df["min_weekly_volume"] = tmp_df["volume"].min()
    tmp_df["max_weekly_volume"] = tmp_df["volume"].max()
    return tmp_df


def handler(event, context):
    BUCKET_NAME = os.environ["bucket_name"]
    API_KEY = os.environ["api_key"]

    # Create empty dataframe
    columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "symbol",
        "avg_weekly_close",
        "median_weekly_close",
        "min_weekly_close",
        "max_weekly_close",
        "avg_weekly_volume",
        "median_weekly_volume",
        "min_weekly_volume",
        "max_weekly_volume",
    ]
    df = pd.DataFrame(columns=columns)

    # Stock symbols: CloudFlare, Twilio, PayPal and TransferWise
    symbols = ["net", "twlo", "pypl", "wise.lon"]

    # Retrieve daily data for each symbol, filter for last week rows,
    # add columns for aggregate stats and populate df dataframe
    for symbol in symbols:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&datatype=csv&apikey={API_KEY}"
        res = requests.get(url)
        tmp_df = pd.read_csv(
            io.StringIO(res.content.decode("utf-8")), engine="python", on_bad_lines="skip", names=columns, skiprows=1
        )
        tmp_df["symbol"] = symbol
        tmp_df = filter_last_week(tmp_df)
        tmp_df = add_aggregate_weekly_statistics(tmp_df)
        df = pd.concat([df, tmp_df])

    # Dataframe is empty, raise error
    if len(df.index) == 0:
        raise ValueError("Dataframe is empty")

    # Store csv in Lambda's temporary storage
    df.to_csv("/tmp/daily.csv")

    last_week_start = date.today() - timedelta(days=7)
    year = last_week_start.year
    week_number = last_week_start.isocalendar()[1]
    filename = f"{year}/{week_number}/daily.csv"

    # Save to S3
    s3 = boto3.resource("s3")
    res = s3.Object(BUCKET_NAME, filename).upload_file("/tmp/daily.csv")

    return res
