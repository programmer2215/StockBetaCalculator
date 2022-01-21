from re import L
import sqlite3 as sql
from nsepy import get_history
from datetime import datetime
from scipy.stats import  linregress
import csv

def connect_to_sqlite(func, *args):
    '''Sqlite Connection Wrapper'''
    conn = sql.connect('StocksData.sqlite')
    cur = conn.cursor()
    return_val = func(cur, *args) # if it even returns something...
    conn.commit()
    conn.close()

    return return_val

def getStockData(stock, start, end):
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

def ON_CREATE(cur, start, end):
    with open("stocks.txt") as f:
        for table_name in f:
            table_name = table_name.strip()
            data = getStockData(table_name, start, end)
            
            SQL = f'''
CREATE TABLE IF NOT EXISTS "{table_name}"(
    Date DATE,
    Open FLOAT,
    High FLOAT,
    Low FLOAT
);'''
            cur.execute(SQL)
            
            for j,k,l,m in zip(data.index, data.Open, data.High, data.Low):
                add_record(cur, table_name, j, k, l, m)
            print(f"[{table_name}] up to date")


def get_last_date(cur, stock):
    SQL = f"""SELECT Date FROM "{stock}" ORDER BY Date DESC LIMIT 1;"""
    cur.execute(SQL)
    LAST_DATE = cur.fetchone()
    return str(LAST_DATE[0])

def add_record(cur, stock, date, open, high, low, cycle=False, validate=False):
    if validate:
        LAST_DATE = get_last_date(cur, stock)
        if not valid(date, LAST_DATE):
            return
    SQL = f"""INSERT INTO "{stock}" (Date, Open, High, Low) VALUES ('{date}', '{open}', '{high}', '{low}');"""
    cur.execute(SQL)
    if cycle:
        SQL = f"""DELETE FROM "{stock}" WHERE Date = (SELECT min(Date) FROM {stock});"""
        cur.execute(SQL)

def get_beta_and_sector(cur, start, end):

    results = []
    with open("stocks.txt", "r") as f:
        sector_data = get_sector_info()
        for stock in f:
            stock = stock.strip()
            SQL = f"""SELECT * FROM "{stock}" Where Date BETWEEN "{start}" AND "{end}";"""
            cur.execute(SQL)
            stock_data = cur.fetchall()
            print(stock)
            diff_vals = []
            for i in range(0, len(stock_data)):
                high_diff = abs(stock_data[i][1] - stock_data[i][2])
                low_diff = abs(float(stock_data[i][1]) - float(stock_data[i][3]))
                diff_vals.append(min([high_diff, low_diff]))
            print(stock, sum(diff_vals), len(diff_vals))
            print(diff_vals)
            beta = sum(diff_vals) / len(diff_vals)
            
            results.append({"Symbol":stock, "Sector":sector_data[stock], "Beta": beta})
    print(results)
    return results

def update_data(cur, now):
    with open("stocks.txt") as f:
        for stock in f:
            stock = stock.strip()
            last = get_last_date(cur, stock)
            data = getStockData(stock, last, now)
            for j,k,l,m in zip(data.index, data.Open, data.High, data.Low):
                add_record(cur, stock, str(j), k, l, m, validate=True)


if __name__ == "__main__":
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
