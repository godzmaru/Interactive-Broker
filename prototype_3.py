#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 30 22:52:49 2018

Interactive Brokers: Client App

@author: hendrawahyu
"""

from clientApp import ClientApp
from ibapi.contract import Contract
from ibapi.order import Order

import time
import datetime
import logging
import pandas as pd

HOST = '127.0.0.1'
PORT = 4002
cid = 10
acc_code = 'DU594416'
user = 'faker251'
passwd = 'akinad76'


### METHODS ###
def basic_contract(symbol, sec_type, exch, prim_exch, curr):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exch
    contract.primaryExchange = exch
    contract.currency = curr
    
    return contract


# An auction order is entered into the electronic trading system during the pre-market opening period for execution at the 
# Calculated Opening Price (COP). If your order is not filled on the open, the order is re-submitted as a limit order with 
# the limit price set to the COP or the best bid/ask after the market opens.
# Products: FUT, STK
def create_order(action, quantity, price, order_type= 'MTL', tif='AUC'):
    order = Order()
    order.action = action
    order.tif = tif
    order.orderType = order_type
    order.totalQuantity = quantity
    order.lmtPrice = price
    
    return order


################################## MAIN ##################################
if __name__ == '__main__':
    try:
        tws = ClientApp()
        tws.connect(HOST, PORT, clientId = cid)
        print('Server Version:%s Connection Time: %s'% (tws.serverVersion(), tws.twsConnectionTime()))
        tws.run()
    
        ### Account Summary ###
        my_account = pd.DataFrame(tws.account_Summary)
        print('### MY ACCOUNT SUMMARY ###')
        print(my_account)
        print('-'* 50)
    except KeyboardInterrupt:
        raise tws.keyboardInterrupt
        time.sleep(2)
        tws.disconnect