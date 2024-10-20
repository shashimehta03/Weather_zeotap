import matplotlib.pyplot as plt
import seaborn as sns

def plot_daily_weather_summary(data):
    """
    Plots the daily weather summary showing the average temperature.

    Args:
        data (DataFrame): The DataFrame containing daily weather data.

    Saves:
        daily_weather_summary.png in the static directory.
    """
    # Calculate daily summary statistics
    daily_summary = get_daily_weather_summary(data)

    # Create a line plot for daily weather summary
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=daily_summary, x='date', y='temperature', label='Avg Temperature', marker='o')
    plt.title('Daily Weather Summary')  # Title of the plot
    plt.xlabel('Date')  # X-axis label
    plt.ylabel('Temperature (°C)')  # Y-axis label
    plt.xticks(rotation=45)  # Rotate date labels for better visibility
    plt.tight_layout()  # Adjust layout to prevent clipping
    plt.savefig('static/daily_weather_summary.png')  # Save plot as PNG
    plt.close()  # Close the plot to free memory

def plot_historical_trends(data):
    """
    Plots the historical weather trends showing temperature over time.

    Args:
        data (DataFrame): The DataFrame containing historical weather data.

    Saves:
        historical_trends.png in the static directory.
    """
    # Create a line plot for historical weather trends
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=data, x='date', y='temperature', label='Temperature Trend', marker='o')
    plt.title('Historical Weather Trends')  # Title of the plot
    plt.xlabel('Date')  # X-axis label
    plt.ylabel('Temperature (°C)')  # Y-axis label
    plt.xticks(rotation=45)  # Rotate date labels for better visibility
    plt.tight_layout()  # Adjust layout
    plt.savefig('static/historical_trends.png')  # Save plot as PNG
    plt.close()  # Close the plot to free memory

def plot_triggered_alerts(data):
    """
    Plots the count of triggered weather alerts.

    Args:
        data (DataFrame): The DataFrame containing alert data.

    Saves:
        triggered_alerts.png in the static directory.
    """
    # Get triggered alerts from the data
    triggered_alerts = get_triggered_alerts(data)

    # Create a count plot for triggered alerts
    plt.figure(figsize=(10, 5))
    sns.countplot(data=triggered_alerts, x='alert_type')  # Replace 'alert_type' with the appropriate column
    plt.title('Triggered Alerts Count')  # Title of the plot
    plt.xlabel('Alert Type')  # X-axis label
    plt.ylabel('Count')  # Y-axis label
    plt.tight_layout()  # Adjust layout
    plt.savefig('static/triggered_alerts.png')  # Save plot as PNG
    plt.close()  # Close the plot to free memory
