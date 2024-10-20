import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def get_daily_weather_summary(data):
    daily_summary = data.groupby('date').agg({'temperature': 'mean'}).reset_index()
    return daily_summary

def get_triggered_alerts(data):
    triggered_alerts = data[data['alert_triggered'] == True]  # Adjust to your actual data structure
    return triggered_alerts

def plot_daily_weather_summary(data):
    daily_summary = get_daily_weather_summary(data)

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=daily_summary, x='date', y='temperature', label='Avg Temperature', marker='o')
    plt.title('Daily Weather Summary')
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/daily_weather_summary.png')
    plt.close()

def plot_historical_trends(data):
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=data, x='date', y='temperature', label='Temperature Trend', marker='o')
    plt.title('Historical Weather Trends')
    plt.xlabel('Date')
    plt.ylabel('Temperature (°C)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/historical_trends.png')
    plt.close()

def plot_triggered_alerts(weather_data):
    triggered_alerts = weather_data[weather_data['alert_triggered'] == True]  # Use the correct column name
    if triggered_alerts.empty:
        print("No triggered alerts found.")
        return

    # Example of plotting
    plt.figure(figsize=(10, 6))
    plt.plot(triggered_alerts['date'], triggered_alerts['temperature'], marker='o', label='Triggered Alerts')
    plt.title('Triggered Alerts Over Time')
    plt.xlabel('Date')
    plt.ylabel('Temperature')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
