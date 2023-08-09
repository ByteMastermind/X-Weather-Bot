# Twitter API
import requests
import tweepy

# Keys defined in keys.py file (define yourself)
import keys

# Program setup
import setup

# Plot generating library
import matplotlib.pyplot as plt

import schedule
import time
import os
import logging
from datetime import datetime

graph_filename = 'graph.png'


def get_twitter_auth_v1() -> tweepy.API:
    """Get twitter conn 1.1"""

    auth = tweepy.OAuth1UserHandler(keys.api_key, keys.api_secret)
    auth.set_access_token(
        keys.access_token,
        keys.access_token_secret,
    )
    return tweepy.API(auth)

def get_twitter_auth_v2() -> tweepy.Client:
    """Get twitter conn 2.0"""

    client = tweepy.Client(
        consumer_key=keys.api_key,
        consumer_secret=keys.api_secret,
        access_token=keys.access_token,
        access_token_secret=keys.access_token_secret,
    )

    return client


def get_weather_info(latitude, longitude):
    """Get Weather info from API of open-meteo"""

    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,rain,surface_pressure,uv_index",
        "timezone": "Europe/Berlin",
        "forecast_days": 1
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        weather_data = response.json()

        # Extracting relevant weather information for the first hourly forecast
        forecast = weather_data["hourly"]

        return forecast

    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        return None


def generate_graph(forecast, new_graph_filename):
    """Generete a graph from API data"""

    temperature = forecast["temperature_2m"]
    rain = forecast["rain"]
    pressure = forecast["surface_pressure"]
    uv_index = forecast["uv_index"]

    # Generate the graph using matplotlib
    plt.figure(figsize=(8, 6))
    plt.plot(temperature, label='Temperature (°C)', color=setup.temperature_line_color, linewidth=setup.temperature_line_width)
    plt.plot(rain, label='Rain Accumulation (mm)', color=setup.rain_line_color, linewidth=setup.rain_line_width)
    plt.xlabel('Time (h)')
    plt.ylabel('Values')
    plt.title('Temperature and Rain Accumulation')
    plt.grid(which='major')
    plt.grid(which='minor', alpha=setup.grid_alpha)
    plt.minorticks_on()
    plt.legend()

    # Save the graph as a PNG image
    plt.savefig(new_graph_filename)

    # Close the plot to avoid displaying it in the console
    plt.close()


def create_post_tweet():
    """Create and post the tweet on twitter"""

    # Getting authorized clients to X API
    client_v1 = get_twitter_auth_v1()
    client_v2 = get_twitter_auth_v2()

    # Getting the content of the tweet ready
    tweet_media = client_v1.simple_upload(filename=graph_filename)
    tweet_text = 'Weather in Prague today'

    # Create and post the tweet with given content
    client_v2.create_tweet(text=tweet_text, media_ids=[tweet_media.media_id])

    logging.info("Successfuly tweeted")


def init_env():
    """Initaliaze the enviroment"""

    # Create log folder if it does not exist
    if not os.path.exists('log'):
        os.mkdir('log')

def create_sub_folder():
    """Create a subfolder for the given tweet"""

    now = datetime.now()

    formatted_date = now.strftime('%d_%m_%Y')
    formatted_time = now.strftime('%H_%M')

    folder_name = f'tweet_{formatted_date}__{formatted_time}'
    folder_path = 'log/' + folder_name
    os.mkdir(folder_path)

    return folder_path


def tweet_job():
    """A job that takes cares of everything (downloading weather data, creating graph, tweeting)"""

    folder_path = create_sub_folder()
    logging.basicConfig(filename=folder_path+'/log.log', format='%(asctime)s - %(levelname)s - %(message)s')

    forecast = get_weather_info(setup.latitude, setup.longitude)
    new_graph_filename = folder_path + '/' + graph_filename
    generate_graph(forecast, new_graph_filename)

    create_post_tweet()


if __name__ == "__main__":
    init_env()

    # Tweet every day at 06:00 am
    schedule.every().day.at('06:00').do(tweet_job)

    while True:
        schedule.run_pending()
        time.sleep(60)
