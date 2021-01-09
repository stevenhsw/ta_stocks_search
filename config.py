from constants import RSI, WILLIAM_R

START_DATE = "2020-01-06"
N_PREVIOUS_DAYS = 30

RSI_CONFIG = {
    'window': 14,
    'fill_na': False  
}

WILLIAM_R_CONFIG = {
    'look_back_period': 14,
    'fill_na': False 
}

THRESHOLD_CONFIG = {
    RSI: 50,
    WILLIAM_R: -50,
    'market_cap': 1_000_000_000
}

TICKER_INFO = [
    'volume',
    'marketCap'
]
