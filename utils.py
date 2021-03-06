from pandas_datareader import data as pdr
import yfinance as yf
import ta
import pandas as pd
import concurrent.futures
from rprint import print_l
from typing import List, Dict, Tuple
from constants import *
from config import *


def exp_smooth(series: pd.Series, alpha: float = 0.1) -> None:
    series_cpy = pd.Series.copy(series)
    size = len(series_cpy)
    if size < 1:
        return series_cpy
    carry = None
    for i in range(0, size - 1):
        if pd.isna(series_cpy[i + 1]):
            continue
        if carry is not None:
            series_cpy[i + 1] = series[i] * alpha + (1 - alpha) * carry
        carry = series_cpy[i + 1]
    return series_cpy


def update_tickers(fname: str, start: int = 1, end: int = 1000) -> None:
    l = []
    INTERVAL = 100

    tickers = [f'{str(i).zfill(4)}.HK' for i in range(start, end + 1)]
    
    for i in range(0, len(tickers), INTERVAL):
        tickers_subset = tickers[i:i + INTERVAL]
        data = pdr.get_data_yahoo(tickers_subset, start=START_DATE)
        data = data[CLOSE]
        if len(tickers_subset) > 1:
            for ticker in tickers_subset:
                if not data[ticker].isnull().all():
                    l.append(ticker)
        else:
            if not data.isnull().all():
                l.append(ticker)

    with open(fname, "w") as f:
        f.write(str(l))


def get_number_of_matches(close: pd.Series, high: pd.Series, 
                          low: pd.Series, volume: pd.Series, n_prev_days: int) -> (int, pd.Series):
    ticker_data = pd.DataFrame()
    ticker_data[CLOSE] = close
    ticker_data[HIGH] = high
    ticker_data[LOW] = low
    ticker_data[VOLUME] = volume
    ticker_data[RSI] = exp_smooth(rsi_wrapper(close))
    ticker_data[WILLIAM_R] = exp_smooth(william_wrapper(high, low, close))
    ticker_data[ADX_POS], ticker_data[ADX_NEG] = adx_wrapper(high, low, close)
    ticker_data[MACD], ticker_data[EMA] = macd_wrapper(close)
    ticker_data[CHAIKIN] = chaikin_wrapper(high, low, close, volume)
    rules = make_rules(ticker_data)
    rules = rules.iloc[-n_prev_days:]
    return rules.sum(), ticker_data


def make_rules(data: pd.DataFrame):
    rules = data[RSI] >= THRESHOLD_CONFIG[RSI]
    rules &= data[WILLIAM_R] >= THRESHOLD_CONFIG[WILLIAM_R] 
    rules &= data[ADX_POS] > data[ADX_NEG]
    rules &= data[MACD] > data[EMA]
    rules &= data[CHAIKIN] > 0
    rules &= data[VOLUME] >= 30_000_000
    max_90_close_price = max(data[CLOSE][-90:])
    rules &= data[CLOSE] >= max_90_close_price
    rules &= data[RSI].diff() > 0
    rules &= data[WILLIAM_R].diff() > 0
    return rules


def rsi_wrapper(close: pd.Series) -> pd.Series:
    rsi_series = ta.momentum.RSIIndicator(close, 
                                          RSI_CONFIG['window'], 
                                          RSI_CONFIG['fill_na'])
    return rsi_series.rsi()


def william_wrapper(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    w_series = ta.momentum.WilliamsRIndicator(high, 
                                              low, 
                                              close,
                                              WILLIAM_R_CONFIG['look_back_period'],
                                              WILLIAM_R_CONFIG['fill_na'])
    return w_series.williams_r()


def adx_wrapper(high: pd.Series, low: pd.Series, close: pd.Series) -> (pd.Series, pd.Series):
    adx_series = ta.trend.ADXIndicator(high, low, close)
    return adx_series.adx_pos(), adx_series.adx_neg()


def macd_wrapper(close: pd.Series) -> (pd.Series, pd.Series):
    macd_series = ta.trend.MACD(close)
    return macd_series.macd(), macd_series.macd_signal()


def chaikin_wrapper(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series):
    chaikin_series = ta.volume.ChaikinMoneyFlowIndicator(high, low, close, volume)
    return chaikin_series.chaikin_money_flow()


def market_cap_filter(tickers: List[str], threshold: int = 5_000_000_000) -> List[str]:
    res = []
    for ticker in tickers:
        if yf.Ticker(ticker).info['marketCap'] >= threshold:
            res.append(ticker)
    return res


def market_cap_filter_threaded(tickers: List[str], threshold: int = 5_000_000_000, n_threads: int = 50) -> List[str]:
    res = []

    def check_market_cap(ticker: str):
        print_l("market_cap_filter: checking ", ticker)
        try:
            if yf.Ticker(ticker).info['marketCap'] >= threshold:
                res.append(ticker)
        except:
            return

    with concurrent.futures.ThreadPoolExecutor(max_workers = n_threads) as executor:
        executor.map(check_market_cap, tickers)
    return res


def get_ticker_info(tickers: List[str]) -> List[Tuple[str, Dict[str, float]]]:
    res = []
    info_keys = TICKER_INFO

    def collect_info(ticker: str):
        info = yf.Ticker(ticker).info
        res.append((ticker, {key: info[key] for key in info_keys}))
    
    for ticker in tickers:
        collect_info(ticker)

    return res


def get_ticker_info_threaded(tickers: List[str], n_threads: int = 50) -> List[Tuple[str, Dict[str, int]]]:
    res = []
    info_keys = TICKER_INFO

    def collect_info(ticker: str):
        info = yf.Ticker(ticker).info
        res.append((ticker, {key: info[key] for key in info_keys}))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers = n_threads) as executor:
        executor.map(collect_info, tickers)
    return res


def make_result_dataframe(ticker_info: List[Tuple[str, Dict[str, float]]], 
                          ticker_to_indicators: Dict[str, pd.DataFrame]):
    assert len(ticker_info) > 0
    sample_name, sample_dict = ticker_info[0][0], ticker_info[0][1]
    static_keys = sample_dict.keys()
    indicators = ticker_to_indicators[sample_name].columns
    data = [[] for i in range(len(ticker_info))]

    for i, (ticker, info) in zip(range(len(ticker_info)), ticker_info):
        data[i].append(ticker)
        for key in static_keys:
            data[i].append(info[key])
        
        for indicator in indicators:
            data[i].append(ticker_to_indicators[ticker][indicator].iloc[-1])
    
    return pd.DataFrame(data,
                        columns = ['name', *list(static_keys), *list(indicators)])


def append_n_day_average_volume(info: List[Tuple[str, Dict[str, float]]], 
                                ticker_to_df: Dict[str, pd.DataFrame], n_day: int):
    for ticker, info_dict in info:
        info_dict[f'{n_day}_day_average'] = get_n_day_average_volume(ticker_to_df[ticker]['Volume'], n_day)
    

def get_n_day_average_volume(volume: pd.Series, n_day: int) -> float:
    return float(volume[-n_day:].mean())
