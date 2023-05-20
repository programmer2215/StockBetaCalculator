import sqlite3 as sql
from nsepython import *
from datetime import datetime
import datetime as dt
from scipy.stats import  linregress
import csv


DB_DATE_FORMAT = "%Y-%m-%d"
NSE_HOLIDAYS = [x['tradingDate'] for x in nse_holidays()['CBM']] # <--- DD-MM-YYYY

print(NSE_HOLIDAYS)

def connect_to_sqlite(func):

    # Database Connection Decorator

    def connect_to_sqlite_wrapper(*args, **kwargs):
        '''Sqlite Connection Wrapper'''
        if not args or not type(args[0]) == sql.Cursor:
            conn = sql.connect('StocksData.sqlite')
            cur = conn.cursor()
            return_val = func(cur, *args, **kwargs)
            conn.commit()
            conn.close()

        else:
            return_val = func(*args, **kwargs)
        return return_val
    return connect_to_sqlite_wrapper  

def getStockData(stock, start, end, nifty=False):
    if nifty:
        Nifty = index_history(
            stock,
            datetime.strptime(start, '%Y-%m-%d').strftime("%d-%b-%Y"),
            datetime.strptime(end, '%Y-%m-%d').strftime("%d-%b-%Y")
        )
        return Nifty
    stock_data = equity_history(
            stock,
            "EQ",
            datetime.strptime(start, '%Y-%m-%d').strftime("%d-%m-%Y"),
            datetime.strptime(end, '%Y-%m-%d').strftime("%d-%m-%Y")
        )
    return stock_data
        
def get_sector_info():
    sector_data = {}
    with open('ind_nifty50list.csv') as f:
        csvreader = csv.reader(f, delimiter=',')
        for row in csvreader:
            sector_data[row[2]] = row[1]
    return sector_data

        

def valid_date(cur_date, last_date):
    return datetime.strptime(cur_date, DB_DATE_FORMAT) > datetime.strptime(last_date, DB_DATE_FORMAT)


@connect_to_sqlite
def ON_CREATE(cur : sql.Cursor, start, end):
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
            
            
    
    
    SQL = f'''
CREATE TABLE IF NOT EXISTS NIFTY50(
    Date DATE,
    Close FLOAT,
    Open FLOAT
);'''
    cur.execute(SQL)
    
    update_data(end, start_date=start)

@connect_to_sqlite
def get_last_date(cur, stock):
    SQL = f"""SELECT Date FROM "{stock}" ORDER BY Date DESC LIMIT 1;"""
    cur.execute(SQL)
    LAST_DATE = cur.fetchone()
    if not LAST_DATE:
        return None
    
    return str(LAST_DATE[0])

@connect_to_sqlite
def add_record(cur, stock, date, close, open, cycle=False, validate=False, high=None, low=None):
    if validate:
        LAST_DATE = get_last_date(cur, stock)
        if not valid_date(date, LAST_DATE):
            return
    if not high and not low:
        SQL = f"""INSERT INTO "{stock}" (Date, Close, Open) VALUES ('{date}', '{close}', '{open}');"""
    else:
        SQL = f"""INSERT INTO "{stock}" (Date, High, Low, Close, Open) VALUES ('{date}', '{high}', '{low}', '{close}', '{open}');"""
    cur.execute(SQL)
    if cycle:
        SQL = f"""DELETE FROM "{stock}" WHERE Date = (SELECT min(Date) FROM {stock});"""
        cur.execute(SQL)
    


def calculate_beta(nifty_changes, stock_changes):
    m = linregress(nifty_changes, stock_changes)
    return m.slope

@connect_to_sqlite
def get_beta_and_sector(cur, start, end, cpr_date=None):
    SQL = f'SELECT Close, Date FROM NIFTY50 Where Date BETWEEN "{start}" AND "{end}" ORDER BY Date;'
    results = []
    cur.execute(SQL)
    percent_changes_nifty = []
    close_data = cur.fetchall()
    
    print(close_data)
    
    sector_data = get_sector_info()
    for i in range(0, len(close_data) - 1):
        per_change = ((float(close_data[i+1][0]) - float(close_data[i][0]))/float(close_data[i][0])) * 100
        percent_changes_nifty.append(per_change)
    with open("stocks.txt", "r") as f:
        for stock in f:
            percent_changes_stock = []
            stock = stock.strip()
            SQL = f"""SELECT Close, Date FROM "{stock}" Where Date BETWEEN "{start}" AND "{end}" ORDER BY Date;"""
            cur.execute(SQL)
            close_data = cur.fetchall()
            if stock == "HDFC":
                print(close_data)
                print()
            SQL = f"""SELECT High, Low, Close FROM "{stock}" Where Date BETWEEN "{cpr_date}" AND "{cpr_date}";"""
            cur.execute(SQL)
            hlc_data = [float(x) for x in cur.fetchall()[0]]
            
            
            
            pivot = sum(hlc_data) / 3
            cpr_bc = sum(hlc_data[:2]) / 2
            cpr_tc = (pivot - cpr_bc) + pivot
            cpr_range = abs(cpr_tc - pivot)
            cpr_diff_per = round((cpr_range / pivot) * 100, 3)

            for i in range(0, len(close_data)-1):
                per_change = ((float(close_data[i+1][0]) - float(close_data[i][0]))/float(close_data[i][0])) * 100
                percent_changes_stock.append(per_change)

            beta = calculate_beta(percent_changes_nifty, percent_changes_stock)
            results.append({"Symbol":stock, "Sector":sector_data[stock], "Beta": beta, "CPR":cpr_diff_per})
    return results

def date_diff(start, end):
    start = datetime.strptime(start, DB_DATE_FORMAT)
    end = datetime.strptime(end, DB_DATE_FORMAT)
    count = 0
    temp_date = start
    
    while temp_date < end:
        temp_date = temp_date + dt.timedelta(days=1)
        if temp_date.weekday() < 5 and temp_date.strftime('%d-%m-%Y') not in NSE_HOLIDAYS:
            count += 1
    
    return count

@connect_to_sqlite
def update_data(cur, now, start_date=None):
    if not start_date:
        last = get_last_date(cur, "NIFTY50")
        now_date = datetime.strptime(now, DB_DATE_FORMAT)
        if not valid_date(now, last):
            print("Data Up to Date")
            return
        elif date_diff(last, now) == 1 and now_date.hour < 18:
            print("Data yet to be updated in server")
            return
        
    with open("stocks.txt") as f:
        for stock in f:
            stock = stock.strip()
            
            if start_date:
                last = start_date
                validate = False
            else:
                last = get_last_date(cur, stock)
                validate = True
                
            data = getStockData(stock, last, now)
            for j,k,l,m, n in zip(data.mTIMESTAMP, data.CH_TRADE_HIGH_PRICE, data.CH_TRADE_LOW_PRICE, data.CH_CLOSING_PRICE, data.CH_OPENING_PRICE):
                j = datetime.strptime(j.split('T18')[0], "%d-%b-%Y").strftime(DB_DATE_FORMAT)
                add_record(cur, stock, str(j), m, n, validate=validate, high=k, low=l)
            print(f"[{stock}] updated")
    
    index_data = getStockData("NIFTY 50", last, now, nifty=True)
    print(index_data)
    for j,k,l in zip(index_data.HistoricalDate, index_data.CLOSE, index_data.OPEN):
        j = datetime.strptime(j.split('T18')[0], "%d %b %Y").strftime(DB_DATE_FORMAT)
        add_record(cur, "NIFTY50", str(j), k, l, validate=validate)
    print(f"[NIFTY 50] updated")


@connect_to_sqlite
def calculate_preopen(cur, stock, date):
    orig_date = date
    date = datetime.strptime(date, DB_DATE_FORMAT)
    prev_day = date - dt.timedelta(days=1)
    while prev_day.weekday() >= 5 and prev_day.strftime('%d-%m-%Y') in NSE_HOLIDAYS:
        prev_day = prev_day - dt.timedelta(days=1)
    date, prev_day = date.strftime(DB_DATE_FORMAT), prev_day.strftime(DB_DATE_FORMAT)
    SQL = f"""SELECT Close FROM "{stock}" WHERE Date = "{prev_day}";"""
    cur.execute(SQL)
    close = cur.fetchone()[0]

    SQL = f"""SELECT Open FROM "{stock}" WHERE Date = "{date}";"""
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
            preopen = calculate_preopen(stock, date)
            DATA.append((stock, SECTORS[stock], round(preopen, 2)))
        nifty_preopen = calculate_preopen('NIFTY50', date)
    if sort == 'htl':
        DATA = sorted(DATA, key=lambda x:x[2], reverse=True)
    elif sort == 'lth':
        DATA = sorted(DATA, key=lambda x:x[2])
    return DATA, nifty_preopen

if __name__ == "__main__":
    prompt = input("Are you sure you want to reset the data? (y/n): ")
    if prompt == "y":
        start = input("Enter Start Date (Format: YYYY-MM-DD): ")
        end = input("Enter End Date: (Format: YYYY-MM-DD)")
        ON_CREATE(start, end)
        print("Setup Successful!!")
    elif prompt == "n":
        print("[TEST SYSTEM]")
        start = input("Enter Start Date (Format: YYYY-MM-DD): ")
        end = input("Enter End Date: (Format: YYYY-MM-DD)")
        test_result = get_beta_and_sector(start, end)
        print(test_result)
