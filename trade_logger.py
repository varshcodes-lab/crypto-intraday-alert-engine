import csv
import os
from datetime import datetime

CSV_PATH = "trades.csv"

CSV_HEADERS = [
    "Time_Entry",
    "Time_Exit",
    "Symbol",
    "Trend",
    "Entry",
    "StopLoss",
    "Target",
    "Quantity",
    "Result",
    "PnL"
]


def init_trade_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        print("[CSV] trades.csv created")
    else:
        print("[CSV] trades.csv already exists")


def log_trade_entry(signal):
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),  
            "",                                               
            signal["symbol"],
            signal["trend"],
            signal["trade"]["entry"],
            signal["trade"]["stop_loss"],
            signal["trade"]["target"],
            signal["trade"]["quantity"],
            "",                                              
            ""                                                
        ])
    print(f"[CSV] ENTRY logged for {signal['symbol']}")


def log_trade_exit(symbol, result, pnl):
    rows = []

    with open(CSV_PATH, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    
    for i in range(len(rows) - 1, 0, -1):
        if rows[i][2] == symbol and rows[i][8] == "":
            rows[i][1] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")  
            rows[i][8] = result
            rows[i][9] = round(pnl, 4)
            break

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"[CSV] EXIT logged for {symbol} | {result} | PnL={pnl}")
