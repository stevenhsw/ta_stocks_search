from pandas_datareader import data as pdr
import yfinance as yf
import ta
import matplotlib.pyplot as plt
import pandas as pd
from utils import *
from constants import *
from config import *
yf.pdr_override()

stock = "0148.HK"
draw = False

data = pdr.get_data_yahoo(stock, start=START_DATE)
close, high, low = data["Close"], data["High"], data["Low"]
data[RSI] = rsi_wrapper(close)
data[WILLIAM_R] = william_wrapper(high, low, close)
data[ADX_POS], data[ADX_NEG] = adx_wrapper(high, low, close)
data[MACD], data[EMA] = macd_wrapper(close)

print(data[WILLIAM_R].iloc[-1])

if draw:
    # close price
    plt.figure(figsize=(15,5))
    plt.plot(close, color='green')
    plt.show()

    # RSI
    plt.figure(figsize=(15,5))
    plt.ylim((0, 100))
    plt.title('RSI')
    plt.plot(data[RSI], color='blue')
    plt.axhline(30, color='black', linestyle='--', alpha=0.3)
    plt.axhline(50, color='black', linestyle='--', alpha=0.5)
    plt.axhline(70, color='black', linestyle='--', alpha=0.5)
    plt.show()

    # William %R
    plt.figure(figsize=(15,5))
    plt.ylim((-100, 0))
    plt.title('william')
    plt.plot(data[WILLIAM_R], color='red')
    plt.axhline(-20, color='black', linestyle='--', alpha=0.3)
    plt.axhline(-40, color='black', linestyle='--', alpha=0.5)
    plt.axhline(-60, color='black', linestyle='--', alpha=0.5)
    plt.axhline(-80, color='black', linestyle='--', alpha=0.3)
    plt.show()

    # ADX
    plt.figure(figsize=(15,5))
    plt.title('ADX')
    plt.plot(data[ADX_POS], color='red')
    plt.plot(data[ADX_NEG], color='green')
    plt.show()

    # MACD
    plt.figure(figsize=(15,5))
    plt.title('MACD')
    plt.plot(data[MACD], color='red')
    plt.plot(data[EMA], color='green')
    plt.show()