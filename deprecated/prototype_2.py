#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 11 14:56:42 2018

Prototype 2 - Interactive Brokers

@author: hendrawahyu
"""

from ib.ext.Order import Order
from ib.opt import Connection, message, ibConnection
from ib.ext.EClientSocket import EClientSocket
from IBWrapper import IBWrapper, contract
import time

numId = 0

if __name__ == '__main__':
    cid = 10        # clientId: can be any number. It will show on IBGateway as folder/different user 
    orderId = 1     # orderId
    accountId = 'DU594416'
    symbolId = '???'       # contract identifier id or asset id?
    port = 4002
    
    # =============================================================================
    # ESTABLISH CONNECTION
    # =============================================================================
    # instantiate data in IBWrapper, still need to use this as EWrapper 
    # is an abstract object
    data = IBWrapper()
    tws = EClientSocket(data)
    tws.eConnect('localhost' , port, cid) 
    
    # Initiate attributes to receive data (REQUIRED) 
    data.initiate_variables()
    # =============================================================================
    # =============================================================================
    
    '''
    # =============================================================================     
    # UPDATE YOUR PORTFOLIO WITH 2 ALTERNATIVES FUNCTION
    # =============================================================================
    # 1. update account:    reqAccountUpdates(subscribe, accountId)
    #     subscribe:    0 - update Acc Time, 1 - update Acc Val, 2 - update Portfolio
    tws.reqAccountUpdates(2, accountId)
    # time (1 sec) is REQUIRED to get data, otherwise empty list
    time.sleep(1)          
    
    # Information listed on list. Check 'ESM8' for more info in:
    #           https://www.interactivebrokers.com/en/index.php?f=463
    #
    # contract_id, currency used, expiry_date, includeExpired (False/True), localSymbol, 
    # multiplier, primaryExchange, right, security Type, strike, contract symbol, 
    # contract tradingClass, position, market Price, marketValue, averageCost, 
    # unrealizedPnL, realizedPnL,accountName
    portfolio = data.update_Portfolio
    position =  portfolio[12]
    print(portfolio)        
    
    # 2. alternatively, you can use this function to output similar above
    tws.reqPositions()
    time.sleep(1)
    print(data.update_Position)
    # =============================================================================
    # =============================================================================
    
    
    # =============================================================================
    # CREATE CONTRACT
    # =============================================================================
    # create a contract first
    cont = contract()
    # =============================================================================
    # =============================================================================
    
    # note: specify time of closing (incomplete)
    # =============================================================================
    # CHECKING INDICES TO BUILD OUR RATIO DURING MARKET CLOSE
    # =============================================================================
    # CBOE Volatility Index (Type: Futures)
    tws.reqIds(1)   # Need to request next valid order Id
    time.sleep(1)   # change this if next Id is empty
    order_id = data.next_ValidId
    contract = cont.create_contract('VIX', 'IND', 'SMART', 'SMART', 'USD')
    tws.reqMarketDataType(1)        # request tick price                            
    time.sleep(1)
    cprice_vix = data.tickPrice
    
    # CBOE S&P500 3-month Volatility Index
    tws.reqIds(1)   # Need to request next valid order Id
    time.sleep(1)   # change this if next Id is empty
    order_id = data.next_ValidId
    contract  = cont.create_contract('VIX3M', 'IND', 'SMART', 'SMART', 'USD')
    tws.reqMarketDataType(1)        # request tick price                            
    time.sleep(1)
    cprice_vix3 = data.tickPrice    # closing price
    
    # Stock 1
    tws.reqIds(1)   # Need to request next valid order Id
    time.sleep(1)   # change this if next Id is empty
    order_id = data.next_ValidId
    contract  = cont.create_contract('TVIX', 'STK', 'SMART', 'SMART', 'USD')
    tws.reqMarketDataType(1)        # request tick price                            
    time.sleep(1)
    cprice_tvix = data.tickPrice    # closing price
    
    # Stock 2
    tws.reqIds(1)   # Need to request next valid order Id
    time.sleep(1)   # change this if next Id is empty
    order_id = data.next_ValidId
    contract  = cont.create_contract('UVXY', 'STK', 'SMART', 'SMART', 'USD')
    tws.reqMarketDataType(1)        # request tick price                            
    time.sleep(1)
    cprice_uvxy = data.tickPrice    # closing price
    # =============================================================================
    # =============================================================================
    
    
    # =============================================================================
    # RATIO
    # =============================================================================
    ratio = cprice_vix / cprice_vix3
    # =============================================================================
    # =============================================================================
    
    
    # =============================================================================
    # ORDER DURING MARKET OPEN
    # =============================================================================
    #if ratio is greater than 1.01 and position is not 0
    if position != 0: 
        if ratio > 1.01:
            print('higher than ratio')
            tws.cancelOrder(order_id)   # preventing double transaction
            
            # STOCK 1
            tws.reqIds(1)   # Need to request next valid order Id
            time.sleep(1)   # change this if next Id is empty
            order_id = data.next_ValidId
            contract  = cont.create_contract('TVIX', 'STK', 'SMART', 'SMART', 'USD')
            tws.reqMarketDataType(1)        # request tick price                            
            time.sleep(1)
            oprice_tvix = data.tickPrice    # closing price

            if (oprice_tvix/cprice_tvix < -0.15):
                order = cont.create_order(accountId, 'LOO', position, 'BUY' )
                tws.placeOrder(order_id, contract, order)
            elif (oprice_tvix/cprice_tvix < -0.05):  
                order = cont.create_order(accountId, 'LOO', position, 'SELL' )
                tws.placeOrder(order_id, contract, order)
            
            # STOCK 2
            tws.cancelOrder(order_id)   # preventing double transaction
            
            tws.reqIds(1)   # Need to request next valid order Id
            time.sleep(1)   # change this if next Id is empty
            order_id = data.next_ValidId
            contract  = cont.create_contract('UVXY', 'STK', 'SMART', 'SMART', 'USD')
            tws.reqMarketDataType(1)        # request tick price                            
            time.sleep(1)
            oprice_tvix = data.tickPrice    # closing price
            
            if (oprice_tvix/cprice_tvix < -0.15):
                order = cont.create_order(accountId, 'LOO', position, 'BUY' )
                tws.placeOrder(order_id, contract, order)
            elif (oprice_tvix/cprice_tvix < -0.05):  
                order = cont.create_order(accountId, 'LOO', position, 'SELL' )
                tws.placeOrder(order_id, contract, order)
            
        elif ratio >= 1.0 and ratio <= 1.01:
            print('still within ratio')
        else:
            print('low than ratio')
            tws.cancelOrder(order_id)   # preventing double transaction
            
            tws.reqIds(1)   # Need to request next valid order Id
            time.sleep(1)   # change this if next Id is empty
            order_id = data.next_ValidId
            
            contract  = cont.create_contract('TVIX', 'STK', 'SMART', 'SMART', 'USD')
            order = cont.create_order(accountId, 'STP', position, 'SELL' )
            tws.placeOrder(order_id, contract, order)
            
            tws.reqIds(1)   # Need to request next valid order Id
            time.sleep(1)   # change this if next Id is empty
            order_id = data.next_ValidId
            
            contract  = cont.create_contract('UVXY', 'STK', 'SMART', 'SMART', 'USD')
            order = cont.create_order(accountId, 'STP', position, 'SELL' )
            tws.placeOrder(order_id, contract, order)
    '''
    time.sleep(2)
    if(tws.isConnected()):
        tws.eDisconnect() 
    
'''
Message:
while loop??
tws.isConnected() outside while loop, so it disconnect when certain cond satisfied?
scheduler to reconnect and disconnect (set up crontab on unix)
'''

