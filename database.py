import sqlite3 as sql
from nsepy import get_history
from datetime import datetime
import datetime as dt
from scipy.stats import  linregress
import csv

def connect_to_sqlite(func, *args):
    '''Sqlite Connection Wrapper...'''
    conn = sql.connect('StocksData.sqlite')
    cur = conn.cursor()
    return_val = func(cur, *args) # if it even returns something...
    conn.commit()
    conn.close()

    return return_val   

def getStockData(stock, start, end, nifty=False):
    if nifty:
        Nifty = get_history(
            symbol=stock,
            start=datetime.strptime(start, '%Y-%m-%d').date(),
            end=datetime.strptime(end, '%Y-%m-%d').date(),
            index=True
        )
        return Nifty
    stock_data = get_history(
            symbol=stock,
            start=datetime.strptime(start, '%Y-%m-%d').date(),
            end=datetime.strptime(end, '%Y-%m-%d').date()
        )
    return stock_data
        
def get_sector_info():
    sector_data = {}
    with open('ind_nifty50list.csv') as f:
        csvreader = csv.reader(f, delimiter=',')
        for row in csvreader:
            sector_data[row[2]] = row[1]
    return sector_data

        

def valid(cur_date, last_date):
    return datetime.strptime(cur_date, "%Y-%m-%d") > datetime.strptime(last_date, "%Y-%m-%d")

def ON_CREATE(cur : sql.Cursor, start, end):
    with open("stocks.txt") as f:
        for table_name in f:
            table_name = table_name.strip()
            data = getStockData(table_name, start, end)
            
            SQL = f'''
CREATE TABLE IF NOT EXISTS "{table_name}"(
    Date DATE,
    Close FLOAT,
    Open FLOAT
);'''
            cur.execute(SQL)
            
            for j,k,l in zip(data.index, data.Close, data.Open):
                add_record(cur, table_name, j, k, l)
            print(f"[{table_name}] up to date")

    index_data = getStockData("NIFTY 50", start, end, nifty=True)
    SQL = f'''
CREATE TABLE IF NOT EXISTS NIFTY50(
    Date DATE,
    Close FLOAT,
    Open FLOAT
);'''
    cur.execute(SQL)
    
    for j,k,l in zip(index_data.index, index_data.Close, index_data.Open):
        add_record(cur, "NIFTY50", j, k, l)
    print("[NIFTY50] up to date")

def get_last_date(cur, stock):
    SQL = f"""SELECT Date FROM "{stock}" ORDER BY Date DESC LIMIT 1;"""
    cur.execute(SQL)
    LAST_DATE = cur.fetchone()
    return str(LAST_DATE[0])

def add_record(cur, stock, date, close, open, cycle=False, validate=False):
    if validate:
        LAST_DATE = get_last_date(cur, stock)
        if not valid(date, LAST_DATE):
            return
        print("valid")
    SQL = f"""INSERT INTO "{stock}" (Date, Close, Open) VALUES ('{date}', '{close}', '{open}');"""
    cur.execute(SQL)
    if cycle:
        SQL = f"""DELETE FROM "{stock}" WHERE Date = (SELECT min(Date) FROM {stock});"""
        cur.execute(SQL)
    


def calculate_beta(nifty_changes, stock_changes):
    m = linregress(nifty_changes, stock_changes)
    return m.slope

def get_beta_and_sector(cur, start, end):
    SQL = f'SELECT Close, Date FROM NIFTY50 Where Date BETWEEN "{start}" AND "{end}";'
    results = []
    cur.execute(SQL)
    percent_changes_nifty = []
    close_data = cur.fetchall()
    
    sector_data = get_sector_info()
    for i in range(0, len(close_data) - 1):
        per_change = ((float(close_data[i+1][0]) - float(close_data[i][0]))/float(close_data[i][0])) * 100
        percent_changes_nifty.append(per_change)
    with open("stocks.txt", "r") as f:
        for stock in f:
            percent_changes_stock = []
            stock = stock.strip()
            SQL = f"""SELECT Close, Date FROM "{stock}" Where Date BETWEEN "{start}" AND "{end}";"""
            cur.execute(SQL)
            close_data = cur.fetchall()

            for i in range(0, len(close_data)-1):
                per_change = ((float(close_data[i+1][0]) - float(close_data[i][0]))/float(close_data[i][0])) * 100
                percent_changes_stock.append(per_change)

            beta = calculate_beta(percent_changes_nifty, percent_changes_stock)
            results.append({"Symbol":stock, "Sector":sector_data[stock], "Beta": beta})
    return results

def update_data(cur, now):
    with open("stocks.txt") as f:
        for stock in f:
            stock = stock.strip()
            last = get_last_date(cur, stock)
            data = getStockData(stock, last, now)
            for j,k,l in zip(data.index, data.Close, data.Open):
                add_record(cur, stock, str(j), k, l, validate=True)
    index_data = getStockData("NIFTY 50", last, now, nifty=True)
    for j,k,l in zip(index_data.index, index_data.Close, index_data.Open):
        add_record(cur, "NIFTY50", str(j), k, l, validate=True)


def calculate_preopen(cur, stock, date):
    date = datetime.strptime(date, "%Y-%m-%d")
    prev_day = date - dt.timedelta(days=1)
    while prev_day.weekday() >= 5:
        prev_day = prev_day - dt.timedelta(days=1)
    date, prev_day = date.strftime("%Y-%m-%d"), prev_day.strftime("%Y-%m-%d")
    SQL = f"""SELECT Close FROM "{stock}" WHERE Date = "{date}";"""
    cur.execute(SQL)
    close = cur.fetchone()[0]

    SQL = f"""SELECT Open FROM "{stock}" WHERE Date = "{prev_day}";"""
    cur.execute(SQL)
    _open= cur.fetchone()[0]

    return ((_open - close) / close) * 100

def fetch_preopen(date, sort='htl'):
    SECTORS = get_sector_info()
    DATA = []
    print(sort)
    with open('stocks.txt') as f:
        for stock in f:
            stock = stock.strip()
            preopen = connect_to_sqlite(calculate_preopen, stock, date)
            DATA.append((stock, SECTORS[stock], round(preopen, 2)))
    if sort == 'htl':
        DATA = sorted(DATA, key=lambda x:x[2], reverse=True)
    elif sort == 'lth':
        DATA = sorted(DATA, key=lambda x:x[2])
    return DATA

if __name__ == "__main__":
    print(fetch_preopen("2023-03-17"))
    prompt = input("Are you sure you want to reset the data? (y/n): ")
    if prompt == "y":
        start = input("Enter Start Date (Format: YYYY-MM-DD): ")
        end = input("Enter End Date: (Format: YYYY-MM-DD)")
        connect_to_sqlite(ON_CREATE, start, end)
        print("Setup Successful!!")
    elif prompt == "n":
        print("[TEST SYSTEM]")
        start = input("Enter Start Date (Format: YYYY-MM-DD): ")
        end = input("Enter End Date: (Format: YYYY-MM-DD)")
        test_result = connect_to_sqlite(get_beta_and_sector, start, end)
        print(test_result)
