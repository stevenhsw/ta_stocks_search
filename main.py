from pandas_datareader import data as pdr
import yfinance as yf
import ta
import matplotlib.pyplot as plt
import pandas as pd
from utils import exp_smooth, update_tickers, get_number_of_matches, \
    market_cap_filter, market_cap_filter_threaded, get_ticker_info_threaded, make_result_dataframe
from typing import List, Dict
from constants import *#TICKERS, TARGETS
from config import START_DATE, N_PREVIOUS_DAYS
yf.pdr_override()


def scanner() -> (List[str], Dict[str, pd.DataFrame]):
    res = []
    ticker_to_indicator = {}
    START = 0
    END = 1000#len(TICKERS)
    INTERVAL = 100
    N_PREVIOUS_DAYS = 30

    for i in range(START, END, INTERVAL):
        if i + INTERVAL >= END:
            tickers_subset = TICKERS[i:END]
        else:
            tickers_subset = TICKERS[i:i + INTERVAL]

        data = pdr.get_data_yahoo(tickers_subset, start=START_DATE)
        data = data.dropna(thresh = len(data // 2)).dropna(axis = 1)
        tickers_subset = list(data["Close"].columns)

        if len(tickers_subset) > 1:
            for ticker in tickers_subset:
                try:
                    n, ticker_data = get_number_of_matches(data["Close"][ticker], 
                                                        data["High"][ticker], 
                                                        data["Low"][ticker], 
                                                        N_PREVIOUS_DAYS)
                    if n > 0:
                        res.append(ticker)
                        ticker_to_indicator[ticker] = ticker_data
                except ValueError: pass
        else:
            try:
                n, ticker_data = get_number_of_matches(data["Close"], 
                                                    data["High"], 
                                                    data["Low"], 
                                                    N_PREVIOUS_DAYS)
                ticker = tickers_subset[0]
                if n > 0:
                    res.append(ticker)
                    ticker_to_indicator[ticker] = ticker_data
            except ValueError: pass
    return res, ticker_to_indicator


import time
class Timer():
    def __init__(self):
        self.time = time.time()
    def clock(self):
        t = time.time() - self.time
        self.time = time.time()
        return t


if __name__ == '__main__':
    t = Timer()
    targets, indicators = scanner()
    print("scanner time: ", t.clock())
    print("targets before: ", targets)
    targets = market_cap_filter_threaded(targets)
    print("targets after: ", targets)
    print("market cap filter time: ", t.clock())
    info = get_ticker_info_threaded(targets)
    print("ticker info time: ", t.clock())
    info = sorted(info, key=lambda x: x[0])
    print("sort time: ", t.clock())
    df = make_result_dataframe(info, indicators)
    print("make df time: ", t.clock())
    df.to_csv("./res.csv", index=False)
    pass
