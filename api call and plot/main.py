import tkinter as tk
from tkinter import ttk
from datetime import datetime, date
import requests
import matplotlib.pyplot as plt
import random

apiKey = "RL2CXG7L4NCOSSE3"

# a list of years, months, and days
stocks = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "FB", "TSLA", "BRK.B", "JPM", "JNJ", "V",
    "WMT", "PG", "NVDA", "DIS", "MA", "PYPL", "HD", "UNH", "BAC", "INTC",
    "CMCSA", "VZ", "ADBE", "CSCO", "PEP", "XOM", "TMO", "CVX", "ORCL", "MRK",
    "CRM", "NFLX", "ABBV", "COST", "AVGO", "QCOM", "MCD", "T", "NEE", "TXN",
    "PFE", "SBUX", "TGT", "LLY", "ASML", "NKE", "NVS", "PM", "ABT"
]

stock = random.choice(stocks)

years = [str(year) for year in range(2005, date.today().year + 1)]
months = [str(month).zfill(2) for month in range(1, 13)]
days = [str(day).zfill(2) for day in range(1, 32)]

def plot_stock_prices(json_data, start_date, end_date):
    time_series = json_data.get("Time Series (Daily)", {})

    timestamps = []
    closing_prices = []

    for date, data in time_series.items():
        curr_date = datetime.strptime(date, "%Y-%m-%d")

        # Check if the current date is within the specified date range
        if (start_date is None or curr_date >= start_date) and (end_date is None or curr_date <= end_date):
            timestamps.append(curr_date)
            closing_prices.append(float(data["4. close"]))

    # Create a plot
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, closing_prices, label="Closing Price", color='b')
    plt.title(f"Stock Prices for {stock}")
    plt.xlabel("Date")
    plt.ylabel("Closing Price ($)")
    plt.grid(True)
    plt.legend()

    # Format x-axis labels to display year-month
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    # Add dollar sign to y-axis labels
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.2f}'))

    plt.tight_layout()
    plt.show()

def generate_plot():
    start_year = year_start_var.get()
    start_month = month_start_var.get()
    start_day = day_start_var.get()
    end_year = year_end_var.get()
    end_month = month_end_var.get()
    end_day = day_end_var.get()

    if not start_year or not start_month or not start_day or not end_year or not end_month or not end_day:
        return  # Do not generate plot if any date part is missing

    start_date = datetime(int(start_year), int(start_month), int(start_day))
    end_date = datetime(int(end_year), int(end_month), int(end_day))

    # Call the Alpha Vantage API to fetch data
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock}&outputsize=full&apikey={apiKey}'
    r = requests.get(url)
    data = r.json()

    # Generate the plot with the specified date range
    plot_stock_prices(data, start_date, end_date)

# Create a larger Tkinter GUI
root = tk.Tk()
root.title("Stock Price Plot Generator")
root.geometry("1000x350")


frame = ttk.Frame(root, padding="10")
frame.grid(column=0, row=0, padx=60, pady=130, sticky=(tk.W, tk.E, tk.N, tk.S))

# Labels for start date
start_label = ttk.Label(frame, text="Start Date:")
start_label.grid(column=0, row=0, sticky=tk.W)

# Dropdowns for start date
year_start_var = tk.StringVar()
year_start_var.set("2023")
year_start_combo = ttk.Combobox(frame, textvariable=year_start_var, values=years)
year_start_label = ttk.Label(frame, text="Year:")
year_start_combo.grid(column=2, row=0, sticky=(tk.W, tk.E))
year_start_label.grid(column=1, row=0, sticky=(tk.W, tk.E))

month_start_var = tk.StringVar()
month_start_var.set("1")
month_start_combo = ttk.Combobox(frame, textvariable=month_start_var, values=months)
month_start_label = ttk.Label(frame, text="Month:")
month_start_label.grid(column=3, row=0, sticky=(tk.W, tk.E))
month_start_combo.grid(column=4, row=0, sticky=(tk.W, tk.E))

day_start_var = tk.StringVar()
day_start_var.set("1")
day_start_combo = ttk.Combobox(frame, textvariable=day_start_var, values=days)
day_start_label = ttk.Label(frame, text="Day:")
day_start_label.grid(column=5, row=0, sticky=(tk.W, tk.E))
day_start_combo.grid(column=6, row=0, sticky=(tk.W, tk.E))

# Labels for end date
end_label = ttk.Label(frame, text="End Date:")
end_label.grid(column=0, row=1, sticky=tk.W)

# Dropdowns for end date
year_end_var = tk.StringVar()
year_end_var.set("2023")
year_end_combo = ttk.Combobox(frame, textvariable=year_end_var, values=years)
year_end_label = ttk.Label(frame, text="Year:")
year_end_label.grid(column=1, row=1, sticky=(tk.W, tk.E))
year_end_combo.grid(column=2, row=1, sticky=(tk.W, tk.E))

month_end_var = tk.StringVar()
month_end_var.set("11")
month_end_combo = ttk.Combobox(frame, textvariable=month_end_var, values=months)
month_end_label = ttk.Label(frame, text="Month:")
month_end_label.grid(column=3, row=1, sticky=(tk.W, tk.E))
month_end_combo.grid(column=4, row=1, sticky=(tk.W, tk.E))

day_end_var = tk.StringVar()
day_end_var.set("9")
day_end_combo = ttk.Combobox(frame, textvariable=day_end_var, values=days)  # Adjust width
day_end_label = ttk.Label(frame, text="Day:")
day_end_label.grid(column=5, row=1, sticky=(tk.W, tk.E))
day_end_combo.grid(column=6, row=1, sticky=(tk.W, tk.E))

# Button to generate the plot
generate_button = ttk.Button(frame, text="Generate Plot", command=generate_plot)
generate_button.grid(column=0, row=3, columnspan=15)


day_end_combo = ttk.Label(frame, text=f"Selected stock: {stock}")
day_end_combo.grid(column=0, row=5, columnspan=15)

root.mainloop()
