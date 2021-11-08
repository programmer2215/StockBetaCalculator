import yfinance as yf
import numpy as np
from sklearn.linear_model import LinearRegression

def calculate_beta(stock, start, end):
    symbols = [stock+".NS", '^NSEI']
    data = yf.download(symbols, start=start, end=end)['Close']
    print(data)

calculate_beta("WIPRO", "2021-11-08", "2021-11-08")
'''from nsepy import get_history
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

def getStockData(stock, start, end, nifty=False):
    if nifty:
        Nifty = get_history(
            symbol=stock,
            start=datetime.strptime(start, '%Y-%m-%d').date(),
            end=datetime.strptime(end, '%Y-%m-%d').date(),
            index=True
        )
        print(Nifty.head())
        return Nifty
    stock_data = get_history(
            symbol=stock,
            start=datetime.strptime(start, '%Y-%m-%d').date(),
            end=datetime.strptime(end, '%Y-%m-%d').date()
        )
    return stock_data

def calculate_beta(stock, start, end):
    stockdf = getStockData(stock, start, end).Close
    niftydf = getStockData("NIFTY 50", start, end, nifty=True).Close
    price_change_stock = stockdf.pct_change()
    stockdf = price_change_stock.drop(price_change_stock.index[0])
    price_change_nifty = niftydf.pct_change()
    niftydf = price_change_nifty.drop(price_change_nifty.index[0])
    x = np.array(stockdf).reshape((-1,1))
    y = np.array(niftydf)
    model = LinearRegression().fit(x, y)
    print('Beta: ', model.coef_)

calculate_beta("WIPRO", "2021-10-08", "2021-11-07")'''


