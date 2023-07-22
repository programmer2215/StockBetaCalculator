import sqlite3 as sql
from tvDatafeed import TvDatafeed, Interval
from datetime import datetime
import numpy as np
from oldDatabase import connect_to_sqlite


def valid(cur_date, last_date):
    return datetime.strptime(cur_date, "%Y-%m-%d") > datetime.strptime(last_date, "%Y-%m-%d")

@connect_to_sqlite
def get_date(cur, stock, start, end):
    SQL = f"""SELECT Date FROM "{stock}" WHERE Date BETWEEN '{start}' AND '{end}';"""
    cur.execute(SQL)

    return cur.fetchall()

@connect_to_sqlite
def get_last_date(cur, stock):
    SQL = f"""SELECT Date FROM "{stock}" ORDER BY Date DESC LIMIT 1;"""
    cur.execute(SQL)
    LAST_DATE = cur.fetchone()
    if LAST_DATE:
        return str(LAST_DATE[0])
    return None

@connect_to_sqlite
def get_data(cur, script, start, end):
    SQL = f'SELECT High, Low FROM "{script}" Where Date BETWEEN "{start}" AND "{end}";'
    cur.execute(SQL)
    return cur.fetchall()



@connect_to_sqlite
def ON_CREATE(cur, start):
    with open("tradingview.txt") as f:
        user_id = f.readline().strip()
        password = f.readline().strip()
    tv = TvDatafeed(user_id, password)
    cur_date = datetime.now()
    start = datetime.strptime(start, "%Y-%m-%d")
    delta = int(np.busday_count(start.date(), cur_date.date()))
    if delta < 1:
        return
    bars = (delta + 1)
    with open("stocks.txt") as f:
        for table_name in f:
            
            table_name = table_name.strip()

            SQL = f'''
CREATE TABLE IF NOT EXISTS "{table_name}"(
    Date DATE,
    High FLOAT,
    Low FLOAT,
    Close FLOAT,
    Open FLOAT
);'''
            cur.execute(SQL)

            data = tv.get_hist(symbol=table_name,exchange='NSE',interval=Interval.in_daily,n_bars=bars)
            for i, row in data.iterrows():
                date = i.strftime("%Y-%m-%d")
                high = float(row.high)
                low = float(row.low)
                close = float(row.close)
                _open = float(row.open)
                add_record(cur, table_name, date, high, low, close, _open, validate=True)
            print(table_name)
    SQL = f'''
CREATE TABLE IF NOT EXISTS "NIFTY50"(
    Date DATE,
    High FLOAT,
    Low Float,
    Close FLOAT,
    Open FLOAT
);'''
    cur.execute(SQL)

    data = tv.get_hist(symbol="NIFTY",exchange='NSE',interval=Interval.in_daily,n_bars=bars)
    for i, row in data.iterrows():
        date = i.strftime("%Y-%m-%d")
        
        high = float(row.high)
        low = float(row.low)
        close = float(row.close)
        _open = float(row.open)
        add_record(cur, "NIFTY50", date, high, low, close, _open, validate=True)
@connect_to_sqlite 
def update_data(cur, date):
    with open("tradingview.txt") as f:
        user_id = f.readline().strip()
        password = f.readline().strip()
    tv = TvDatafeed(user_id, password)
    cur_date = datetime.now()
    date = datetime.strptime(date, "%Y-%m-%d")
    delta = int(np.busday_count(date.date(), cur_date.date()))
    delta_raw = cur_date - date
    if delta < 1:
        if delta_raw.days >= 2:
            delta += 1
        else:
            return
    bars = delta
    with open("stocks.txt") as f:
        for table_name in f:
            table_name = table_name.strip()
            print(type(bars))
            data = tv.get_hist(symbol=table_name,exchange='NSE',interval=Interval.in_daily,n_bars=bars)
            for i, row in data.iterrows():
                date = i.strftime("%Y-%m-%d")
                if table_name == "ADANIPORTS":
                    print(date)
                high = float(row.high)
                low = float(row.low)
                close = float(row.close)
                _open = float(row.open)
                add_record(cur, table_name, date, high, low, close, _open, validate=True)
        data = tv.get_hist(symbol="NIFTY",exchange='NSE',interval=Interval.in_daily,n_bars=bars)
        for i, row in data.iterrows():
                date = i.strftime("%Y-%m-%d")
                high = float(row.high)
                low = float(row.low)
                close = float(row.close)
                _open = float(row.open)
                add_record(cur, "NIFTY50", date, high, low, close, _open, validate=True)

@connect_to_sqlite
def add_record(cur, stock, date, high, low, close, _open,validate=False):
    if validate:
        
        LAST_DATE = get_last_date(cur, stock)
        if not LAST_DATE:
            pass
        elif not valid(date, LAST_DATE):
            return
        
        
    SQL = f"""INSERT INTO "{stock}" (Date, High, Low, Close, Open) VALUES ('{date}', '{high}', '{low}', '{close}', '{_open}');"""
    cur.execute(SQL)

if __name__ == '__main__':
    update_data(get_last_date("NIFTY50"))