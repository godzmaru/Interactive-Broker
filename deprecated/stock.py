#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  7 17:45:34 2018

@author: hendrawahyu
"""

import pandas as pd
import pandas_datareader.data as web
import datetime
import matplotlib.pyplot as plt

#%matplotlib inline         #only to appear in jupyter notebook
#%pylab inline              #only jupyter notebook, to control size of figures
#pylab.rcParams['figure.figsize'] = (15, 9)

#CANDLESTICK PLOT FOR OPEN, HIGH, LOW, CLOSE VARIABLES
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, date2num, MONDAY
from matplotlib.finance import candlestick_ohlc
import numpy as np 

def pandas_candlestick_ohlc(dat, stick = "day", otherseries = None):
    """
    :param dat: pandas DataFrame object with datetime64 index, and float columns "Open", "High", "Low", and "Close"
    :param stick: A string or number indicating the period of time covered by a single candlestick. Valid string 
                  inputs include "day", "week", "month", and "year", ("day" default), 
                  and any numeric input indicates the number of trading days included in a period
    :param otherseries: An iterable that will be coerced into a list, containing the columns of dat that hold other 
                        series to be plotted as lines
    This will show a Japanese candlestick plot for stock data stored in dat, also plotting other series if passed.
    """
    mondays = WeekdayLocator(MONDAY)        # major ticks on the mondays
    alldays = DayLocator()                  # minor ticks on the days
    #dayFormatter = DateFormatter('%d')      # e.g., 12
 
    # Create a new DataFrame which includes OHLC data for each period specified by stick input
    # loc[row, columns] is to get item from DataFrame
    transdat = dat.loc[:,["Open", "High", "Low", "Close"]]
    if (type(stick) == str):
        if stick == "day":
            plotdat = transdat
            stick = 1                   # Used for plotting
        elif stick in ["week", "month", "year"]:
            if stick == "week":
                #create a new field 'week' into dataframe, transdata
                transdat["week"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[1]) # Identify weeks
            elif stick == "month":
                #create a new field 'month' into dataframe, transdata
                transdat["month"] = pd.to_datetime(transdat.index).map(lambda x: x.month)           # Identify months
            #create a new field 'year' into dataframe, transdata
            transdat["year"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[0])     # Identify years
            # Group by year and other appropriate variable
            grouped = transdat.groupby(list(set(["year",stick]))) 
            # Create empty data frame containing what will be plotted
            plotdat = pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []}) 
            for name, group in grouped:
                #selecting data from group using iloc[row, column] by row_number
                plotdat = plotdat.append(pd.DataFrame({"Open": group.iloc[0,0],
                                            "High": max(group.High),
                                            "Low": min(group.Low),
                                            "Close": group.iloc[-1,3]},
                                           index = [group.index[0]]))
            if stick == "week": stick = 5
            elif stick == "month": stick = 30
            elif stick == "year": stick = 365
    
    # if stick is an integer
    elif (type(stick) == int and stick >= 1):
        transdat["stick"] = [np.floor(i / stick) for i in range(len(transdat.index))]
        grouped = transdat.groupby("stick")
        plotdat = pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []}) # Create empty data frame containing what will be plotted
        for name, group in grouped:
            plotdat = plotdat.append(pd.DataFrame({"Open": group.iloc[0,0],
                                        "High": max(group.High),
                                        "Low": min(group.Low),
                                        "Close": group.iloc[-1,3]},
                                       index = [group.index[0]]))
 
    else:
        raise ValueError('Valid inputs to argument "stick" include the strings "day", "week", "month", "year", or a positive integer')
 
    #print('plotdat\n', plotdat, type(plotdat))
    # Set plot parameters, including the axis object ax used for plotting
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    if plotdat.index[-1] - plotdat.index[0] < pd.Timedelta('730 days'):
        weekFormatter = DateFormatter('%b %d')  # e.g., Jan 12
        ax.xaxis.set_major_locator(mondays)
        ax.xaxis.set_minor_locator(alldays)
    else:
        weekFormatter = DateFormatter('%b %d, %Y')
    ax.xaxis.set_major_formatter(weekFormatter)
 
    ax.grid(True)
 
    # Create the candelstick chart
    # closing price higher than open -> black, otherwise red, wick indicate high and low
    candlestick_ohlc(ax, list(zip(list(date2num(plotdat.index.tolist())), plotdat["Open"].tolist(), plotdat["High"].tolist(),
                      plotdat["Low"].tolist(), plotdat["Close"].tolist())),
                      colorup = "black", colordown = "red", width = stick * .4)
 
    # Plot other series (such as moving averages) as lines
    if otherseries != None:
        if type(otherseries) != list:
            otherseries = [otherseries]
        dat.loc[:,otherseries].plot(ax = ax, lw = 1.3, grid = True)
 
    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
 
    plt.show()
 
    
#initiate start and end date
start = datetime.datetime(2018,1,1)
end = datetime.date.today()

#get apple stock data - stock, market source provider, start_date, end_date
apple = web.DataReader('WIKI/AAPL','quandl', start, end)
#print(type(apple))     #pandas.core.frame.DataFrame
apple["AdjClose"].plot(grid=True)

pandas_candlestick_ohlc(apple)


#get microsoft data
microsoft = web.DataReader('MSFT', 'quandl', start, end)
google = web.DataReader('GOOG', 'quandl', start, end)

stocks = pd.DataFrame({'WIKI/AAPL': apple['AdjClose'],
                       'MSFT': microsoft['AdjClose'],
                       'GOOG': google['AdjClose']})

# shows the first 5 data, opposite of tail()               
#print(stocks.head())
                
# shows columns header
#print(stocks.columns.values)

# plot absolute price where literal values are plotted and pitted against others
#stocks.plot(grid = True)

# plot relative change of an asset using 2 different scales; 
# 1. apple & microsoft
# 2. google
stocks.plot(secondary_y = ['WIKI/AAPL', 'MSFT'], grid = True)


# calculating the stocks return: return = xt / x0 (IMPORTANT)
stock_return = stocks.apply(lambda x: x / x[0])
#print(stock_return.head())
stock_return.plot(grid= True).axhline(y = 1, color = "black", lw = 2)


# calculating growth change, growth,t = (price,t+1 + price,t)/ price,t
# preferably using log differences, changes,t = log(price,t) - log(price,t-1) -> %change
stock_growth = stocks.apply(lambda x: np.log(x) - np.log(x.shift(1)))   #shift dates by 1
#print(stock_growth.head())
stock_growth.plot(grid= True).axhline(y = 0, color = "black", lw = 2)


# calculating moving averages -> smooth a series to identify trends from noise. Larger q
# less responsive moving average to short term fluctuations. Thus, fast MA has small q
# slow MA has large q
# creating 20-day (1 month), 50-day, 200-day moving average for Apple
start1 = datetime.datetime(2010,1,1)
apple1 = web.DataReader('WIKI/AAPL', 'quandl', start1, end)
ma_20 = np.round(pd.rolling_mean(apple1, window = 20), 2)
ma_50 = np.round(pd.rolling_mean(apple1, window = 50), 2)
ma_200= np.round(pd.rolling_mean(apple1, window = 50), 2)
apple1["20d"] = np.round(apple1["Close"].rolling(window = 20, center = False).mean(), 2)
apple1["50d"] = np.round(apple1["Close"].rolling(window = 50, center = False).mean(), 2)
apple1["200d"]= np.round(apple1["Close"].rolling(window = 200, center = False).mean(), 2)

# plotting 20-MA, 50-MA, 200-MA alongside stock - ERROR
#pandas_candlestick_ohlc(apple1.loc['2016-01-04':'2016-08-07',:], otherseries = ['20d','50d', '200d'])