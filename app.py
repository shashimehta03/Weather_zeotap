from flask import Flask, render_template, request  # Import Flask and relevant functions for web handling
from visualizations.visualizations import (
    plot_daily_weather_summary,  # Import function to plot daily weather summaries
    plot_historical_trends,      # Import function to plot historical weather trends
    plot_triggered_alerts        # Import function to plot triggered weather alerts
)
from real_time_bonus import get_detailed_weather_data  # Import real-time weather data retrieval function
import os  # For interacting with the operating system
import sys  # For system-specific parameters and functions
import requests  # For sending HTTP requests to external APIs
import sqlite3  # SQLite database for storing weather data
import pandas as pd  # For data manipulation and analysis
import time  # To introduce delays, if needed
import threading  # For running tasks in parallel threads
import logging  # For logging purposes (tracking events during execution)
from datetime import datetime  # To handle date and time operations
import smtplib  # To send email alerts
from email.mime.text import MIMEText  # For composing plain text emails
from email.mime.multipart import MIMEMultipart  # For sending emails with attachments or HTML
import seaborn as sns  # For creating statistical visualizations
import matplotlib.pyplot as plt  # For generating visual plots

# Initialize the Flask web app
app = Flask(__name__)

# API key for accessing weather data (ensure to replace it with your actual key)
API_KEY = '54016b09122721d79e651ea82f0a52fe'

# Add the current script's directory to the system path (for module resolution)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging to track information and errors with timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_historical_weather_data():
    """
    Load historical weather data from a CSV file.

    Returns:
        pandas.DataFrame: The weather data in a DataFrame format.
    """
    return pd.read_csv('data/historical_weather_data.csv')

def get_daily_weather_summary(data):
    """
    Generate a summary of daily weather statistics like average temperature and humidity.

    Args:
        data (pandas.DataFrame): The weather data to summarize.

    Returns:
        pandas.DataFrame: A summary of mean temperature and humidity, grouped by date.
    """
    return data.groupby('date').agg({'temperature': 'mean', 'humidity': 'mean'}).reset_index()

def get_triggered_alerts(data):
    """
    Retrieve rows where alerts were triggered based on weather conditions.

    Args:
        data (pandas.DataFrame): The weather data containing alert flags.

    Returns:
        pandas.DataFrame: Filtered data with alerts that were triggered.
    """
    return data[data['alert_triggered'] == True]

def create_table():
    """
    Create an SQLite database table if it doesn't exist, to store real-time weather data.

    Table structure:
        - id: Auto-incremented primary key.
        - city: City name (TEXT).
        - weather: Weather description (TEXT).
        - temp: Current temperature (REAL).
        - feels_like: Feels-like temperature (REAL).
        - timestamp: Time of record (INTEGER).
    """
    # Establish a connection to the SQLite database
    conn = sqlite3.connect('weather_data.db')
    cursor = conn.cursor()

    # Create a table for weather data with the required schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            weather TEXT,
            temp REAL,
            feels_like REAL,
            timestamp INTEGER
        )
    ''')

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

# Call the function to create the database table when the Flask app starts
create_table()

def get_weather_data(city_name):
    """
    Fetch current weather data for a specific city from the OpenWeather API.

    Args:
        city_name (str): The name of the city to fetch weather data for.

    Returns:
        dict or None: The JSON response from the API if successful, otherwise None.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}"
    response = requests.get(url)
    
    # Check if the response is successful (status code 200)
    if response.status_code == 200:
        return response.json()  # Return the weather data as a JSON object
    else:
        return None  # Return None if the API call fails

def kelvin_to_celsius(temp_kelvin):
    """
    Convert temperature from Kelvin to Celsius.

    Args:
        temp_kelvin (float): Temperature in Kelvin.

    Returns:
        float: Temperature in Celsius.
    """
    return temp_kelvin - 273.15

def process_weather_data(data):
    """
    Extract and process relevant weather data from the API response.

    Args:
        data (dict): The weather data fetched from the API.

    Returns:
        dict or None: Processed data including weather, temperature, feels-like temperature, and timestamp.
    """
    if data:
        # Extract the main weather description and temperatures in Kelvin
        main_weather = data['weather'][0]['main']
        temp_kelvin = data['main']['temp']
        feels_like_kelvin = data['main']['feels_like']
        
        # Convert temperatures to Celsius
        temp_celsius = kelvin_to_celsius(temp_kelvin)
        feels_like_celsius = kelvin_to_celsius(feels_like_kelvin)
        
        # Get the timestamp of the data
        timestamp = data['dt']
        
        # Return the processed data in a structured dictionary
        return {
            'weather': main_weather,
            'temp': round(temp_celsius, 2),
            'feels_like': round(feels_like_celsius, 2),
            'timestamp': timestamp
        }
    return None  # Return None if the data is invalid or not available

def store_weather_data(city, data):
    """
    Store the weather data in the SQLite database.

    Args:
        city (str): The name of the city.
        data (dict): The processed weather data to store.
    """
    conn = sqlite3.connect('weather_data.db')  # Connect to the SQLite database
    c = conn.cursor()
    
    # Use the connection context to insert data into the weather_data table
    with conn:
        c.execute("INSERT INTO weather_data (city, weather, temp, feels_like, timestamp) VALUES (?, ?, ?, ?, ?) ",
                  (city, data['weather'], data['temp'], data['feels_like'], data['timestamp']))
    
    conn.close()  # Close the database connection

def calculate_daily_summary(city):
    """
    Calculate the daily weather summary for a specific city from the database.

    Args:
        city (str): The name of the city to retrieve the summary for.

    Returns:
        dict or None: A dictionary containing average, max, and min temperatures, and dominant weather condition.
    """
    conn = sqlite3.connect('weather_data.db')  # Connect to the SQLite database
    df = pd.read_sql_query(f"SELECT * FROM weather_data WHERE city='{city}'", conn)  # Load data for the specified city
    conn.close()  # Close the connection

    if not df.empty:
        # Calculate summary statistics: average, max, min temperature and the most frequent weather condition
        daily_summary = {
            'avg_temp': round(df['temp'].mean(), 2),
            'max_temp': df['temp'].max(),
            'min_temp': df['temp'].min(),
            'dominant_weather': df['weather'].mode()[0]  # Get the most common weather condition
        }
        return daily_summary
    else:
        return None  # Return None if there is no data for the specified city

def update_weather_data():
    """
    Continuously update the weather data for a list of cities at regular intervals (every 5 minutes).
    """
    while True:
        # List of cities to fetch weather data for
        cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
        
        # Loop through each city and update the database with the latest weather data
        for city in cities:
            data = get_weather_data(city)
            if data:
                processed_data = process_weather_data(data)
                store_weather_data(city, processed_data)
                logging.info(f"Updated weather data for {city}: {processed_data}")
        
        time.sleep(300)  # Pause for 5 minutes before fetching new data

def send_email_alert(email, city, threshold_temp, current_temp):
    """
    Send an email alert when the temperature exceeds a predefined threshold.

    Args:
        email (str): The recipient's email address.
        city (str): The name of the city the alert is for.
        threshold_temp (float): The temperature threshold set by the user.
        current_temp (float): The current temperature in the city.
    """
    my_email = "iiitkottayamcoms@gmail.com"  # Sender's email
    password = "qwyxksuejdmsglin"  # Sender's email password (use a more secure method for handling passwords)

    # Create the email subject and body
    subject = f"Temperature Alert for {city}"
    body = (f"Alert: The temperature in {city} has exceeded your set threshold of {threshold_temp} °C! "
            f"Current temperature: {current_temp} °C.")

    # Create a MIMEMultipart message to hold the email content
    msg = MIMEMultipart()
    msg['From'] = my_email
    msg['To'] = email
    msg['Subject'] = subject

    # Attach the plain text email body to the message
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        # Set up the SMTP connection to send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as connection:
            connection.starttls()  # Start TLS (Transport Layer Security) for secure email sending
            connection.login(user=my_email, password=password)  # Log in to the email account
            connection.sendmail(from_addr=my_email, to_addrs=email, msg=msg.as_string())  # Send the email
            logging.info(f"Alert email sent to {email} for {city}.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")  # Log any errors that occur during email sending



@app.route('/')
def index():
    """
    Route to display the weather dashboard. It fetches and processes weather data 
    for a list of cities and renders it on the index page.
    
    Returns:
        HTML template: Renders the index page with weather data and daily summary.
    """
    cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
    weather_data = []

    # Fetch and process weather data for each city
    for city in cities:
        data = get_weather_data(city)
        if data:
            processed_data = process_weather_data(data)
            store_weather_data(city, processed_data)  # Store data in the database
            weather_data.append({
                'city': city,
                'weather': processed_data['weather'],
                'temp': processed_data['temp'],
                'feels_like': processed_data['feels_like'],
                'timestamp': datetime.utcfromtimestamp(processed_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            })

    # Get daily summary for the city of Delhi
    daily_summary = calculate_daily_summary('Delhi')

    # Get the last update time (current UTC time)
    last_update_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Render the index page with weather data, daily summary, and last update time
    return render_template('index.html', weather_data=weather_data, daily_summary=daily_summary, last_update_time=last_update_time)

@app.route('/latest_weather', methods=['GET'])
def latest_weather():
    """
    Route to return the latest weather data in JSON format.

    Returns:
        JSON: The latest weather data from the SQLite database.
    """
    conn = sqlite3.connect('weather_data.db')
    df = pd.read_sql_query("SELECT * FROM weather_data ORDER BY timestamp DESC LIMIT 1", conn)
    conn.close()
    return df.to_json(orient='records')

def plot_triggered_alerts(weather_data):
    """
    Function to plot triggered weather alerts from the given data.

    Args:
        weather_data (DataFrame): The DataFrame containing weather data.

    Returns:
        None
    """
    # Debug: Print the available columns in weather_data
    print("Available Columns in weather_data:")
    print(weather_data.columns.tolist())

    # Ensure 'alert_triggered' column exists
    if 'alert_triggered' not in weather_data.columns:
        print("Column 'alert_triggered' not found in weather_data.")
        return

    # Filter rows where 'alert_triggered' is True
    triggered_alerts = weather_data[weather_data['alert_triggered'] == True]

    # Debug: Output the triggered alerts
    print("Triggered Alerts DataFrame:")
    print(triggered_alerts)

    if triggered_alerts.empty:
        print("No triggered alerts found.")
        return  # Exit if no alerts were found

    # Plotting the triggered alerts over time
    plt.figure(figsize=(10, 6))
    plt.plot(triggered_alerts['date'], triggered_alerts['alert_triggered'], marker='o', linestyle='-')
    plt.title('Triggered Alerts Over Time')
    plt.xlabel('Date')
    plt.ylabel('Alert Triggered')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def load_weather_data(file_path='data/historical_weather_data.csv'):
    """
    Load historical weather data from a CSV file.

    Args:
        file_path (str): Path to the CSV file containing historical weather data.

    Returns:
        pd.DataFrame: A DataFrame containing the loaded weather data.
    """
    try:
        # Load CSV data into a pandas DataFrame
        weather_data = pd.read_csv(file_path)
        print("Weather data loaded successfully.")
        return weather_data
    except Exception as e:
        print(f"Error loading weather data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame if there's an error

@app.route('/visualizations')
def visualizations():
    """
    Route to display weather visualizations.

    Returns:
        HTML template: Renders the visualizations page.
    """
    # Load the weather data from the CSV file
    weather_data = load_weather_data()

    # Plot triggered alerts using the loaded data
    plot_triggered_alerts(weather_data)

    return render_template('visualizations.html')

@app.route('/alert_registered', methods=['POST'])
def alert_registered():
    """
    Route to handle user registration for weather alerts.

    Returns:
        HTML template: Renders the alert registration page with alert status.
    """
    city = request.form['city']
    threshold_temp = float(request.form['threshold_temp'])
    email = request.form.get('email')  # Get the user's email address

    # Check the latest weather data for the specified city and trigger alerts if necessary
    conn = sqlite3.connect('weather_data.db')
    df = pd.read_sql_query(f"SELECT * FROM weather_data WHERE city='{city}' ORDER BY timestamp DESC", conn)
    conn.close()

    alert_triggered = False
    current_temp = None  # Initialize the current temperature variable

    # If data exists for the specified city, check if the temperature exceeds the threshold
    if not df.empty:
        current_temp = df['temp'].iloc[0]  # Get the latest temperature
        if current_temp > threshold_temp:
            alert_triggered = True
            send_email_alert(email, city, threshold_temp, current_temp)  # Send an email alert

    return render_template('alert_registered.html', alert_triggered=alert_triggered, city=city, threshold_temp=threshold_temp, current_temp=current_temp)

@app.route('/real_time_bonus', methods=['GET', 'POST'])
def real_time_bonus():
    """
    Route to handle real-time bonus weather data retrieval.

    Returns:
        HTML template: Renders the real-time bonus page with weather data.
    """
    weather_data = None  # Initialize weather_data variable
    if request.method == 'POST':
        city = request.form['city']  # Get the city name from the form
        weather_data = get_detailed_weather_data(city)  # Fetch real-time weather data for the specified city

    return render_template('real_time_bonus.html', weather_data=weather_data)

if __name__ == '__main__':
    """
    Entry point for running the Flask app. It also starts the weather data update thread.
    """
    # Start a background thread to update weather data periodically
    update_thread = threading.Thread(target=update_weather_data)
    update_thread.daemon = True  # Ensures the thread will exit when the main program exits
    update_thread.start()

    # Start the Flask web application
    app.run(debug=True)
