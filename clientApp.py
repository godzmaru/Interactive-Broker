#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 16:00:31 2018

@author: hendrawahyu
"""


from ibapi import client
from ibapi import wrapper
from ibapi.utils import iswrapper, current_fn_name
from ibapi.contract import Contract
from ibapi.ticktype import TickType
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.common import TickerId, OrderId, TickAttrib

import time
import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

### FILE HANDLER ###
#file_handler = logging.FileHandler('../Interactive Brokers/log/out.log')
#file_handler.setLevel(logging.ERROR)       # only capture an error only
#file_handler.setFormatter(formatter)
#logger.addHandler(file_handler)

### STREAM HANDLER ###
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

#logger.info
#logger.exception('message here')   # will also invoke traceback call

HOST = '127.0.0.1'
PORT = 4002
cid = 10
acc_code = 'DU594416'
user = 'faker251'
passwd = 'akinad76'

# wrapping data
class ClientApp(wrapper.EWrapper, client.EClient):
    def __init__(self):
        wrapper.EWrapper.__init__(self)
        client.EClient.__init__(self, wrapper = self)
    
        ### INSTANTIATE ALL VARIABLES ###
        # Account and Portfolio
        setattr(self, 'account_Summary', [])
        setattr(self, "update_AccountTime", None)
        setattr(self, "update_AccountValue", [])
        setattr(self, "update_Portfolio", [])
        setattr(self, 'update_Position', [])
        # Orders
        setattr(self, 'order_Status', [])
        setattr(self, 'open_Order', [])
        
        # Misc
        self.nKeybInt = 0
        self.permId2ord = {}
        self.nextValidOrderId = None
        self.simplePlaceOid = None
        self.account_value = 0
        self.unrealizedpnl = 0          # unrealized Profit and Loss
        
        # Flags and other variables
        self.started = False
        self.accountDownloadEnd_flag = False
        self.account_SummaryEnd_flag = False
        self.globalCancelOnly = False
        self.positionEnd_flag = False
        self.openOrderEnd_flag = True
        self.debug = False
        
        
    ################### UTILS ###################
    @iswrapper
    # callback signifying successfull connection to IBGateway
    def connectAck(self):
        if self.async:
            self.startApi()
            print('\nStarting the IB API')
    
    @iswrapper
    # invoke ClientApp.managedAccount([' list_of_all_account_ID '])
    def managedAccounts(self, accountsList: str):
        super().managedAccounts(accountsList)
        print("\nAccount list: ", accountsList)
        self.account = accountsList.split(",")[0]
    
    @iswrapper
    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        print('\nError:')
        print('\nId: {} - Code: {} - Message: {}'.format(reqId, errorCode, errorString))
    
    @iswrapper
    def updateAccountTime(self, timeStamp: str):
        self.update_AccountTime = timeStamp
        print("\nUpdateAccountTime. Time:", timeStamp)
    
    
    ################### ORDER ID ###################
    @iswrapper
    # receive next valid order ID
    def nextValidId(self, orderId: int):
        print("\nNext Valid Order Id: %d", orderId)
        self.nextValidOrderId = orderId
        
        if self.started:
            return
        self.started = True
        
        if self.globalCancelOnly:
            print("Executing GlobalCancel only")
            self.reqGlobalCancel()
        else:
            print('\nExecuting Request:')
            self.reqManagedAccts()      #
            self.reqAccountSummary(9002, "All", "$LEDGER:USD")  # $LEDGER:USD, $LEDGER:ALL
            self.reqAccountUpdates(True, acctCode = self.account)
            self.reqPositions()         # request all position in account
            ## CONTRACT / ORDER ##
            #self.contractOperations_req()
            #self.orderOperations_req()
            
            ## MARKET DATA ## 1.LIVE - 2.FROZEN - 3.DELAYED - 4.DELAYED FROZEN
            #self.reqMarketDataType(1)
            #self.marketDepthOperations_req() 
            #self.realTimeBars_req()
            #self.historicalDataRequests_req()
            #self.marketRuleOperations()
            #self.historicalTicksRequests_req()
            #self.tickByTickOperations()
            print("Executing requests ... finished")
    
    # automatically increment order Id by 1, this MUST be used in every transaction
    # like ordering, require market update etc
    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid
        
    
    ################### CANCELLATION / OPERATIONS / KEYBOARD ###################
    def keyboardInterrupt(self):
        self.nKeybInt += 1
        # any keypress
        if self.nKeybInt == 1:
            self.stop()
        else:
            print('Finish')
            self.done = True
    
    # cancel all operation
    def stop(self):
        print("Executing cancels")
        # account operation cancellation
        self.reqAccountUpdates(False, self.account)
        self.cancelAccountSummary(9002)
        self.cancelPositions()
        # cancel order
        if self.simplePlaceOid is not None:
            self.cancelOrder(self.simplePlaceOid)
            
        # cancel market data subscription
        #self.cancelMktData(1101)               # require tickedId
        #self.cancelMktDepth(1101)              # require tickerId
        #self.cancelRealTimeBars(1101)          # require tickerId
        #self.cancelHistoricalData(1101)        # require tickerId
        #self.cancelScannerSubscription(1101)    # require tickerId
        
        print("Executing cancels ... finished")
    
    
    ################### UPDATE ###################    
    @iswrapper
    # Called after updateAccountValue() and updatePortfolio() is sent
    def accountDownloadEnd(self, accountName: str):
        super().accountDownloadEnd(accountName)
        print("\nAccount download finished:", accountName)
    
    @iswrapper
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency:str):
        account_Summary = self.account_Summary
        account_Summary.append({'reqId': reqId, 'account':account, 'tag':tag, 
                                'value':value, 'currency': currency}) 
        if(self.debug):
            print("Acct Summary. ReqId:", reqId, "Acct:", account,
              "Tag: ", tag, "Value:", value, "Currency:", currency)
    
    @iswrapper
    def accountSummaryEnd(self, reqId: int):
        if self.account_SummaryEnd_flag:
            return
        print('\nAccount Summary End')
        print('\nReqId:', reqId)
        self.accountSummaryEnd_reqId = reqId
        self.account_SummaryEnd_flag = True
    
    @iswrapper
    # automatically called up when reqAccountUpdates is activated
    def updateAccountValue(self, key:str, val:str, currency:str,
                            accountName:str):
        update_AccountValue = self.update_AccountValue
        update_AccountValue.append({'key': key, 'val': val, 'currency':currency, 
                                    'accountName':accountName })
        if key == 'UnrealizedPnL' and currency== 'USD':
            self.unrealizedpnl = val
            print('\nALERT: Unrealized PnL', val)
        if key == 'NetLiquidationByCurrency' and currency == 'USD':
            self.account_value = val
            print('\nALERT: Net Liquidation Value', val)
        if(self.debug):
            print("UpdateAccountValue. Key:", key, "Value:", val,
                  "Currency:", currency, "AccountName:", accountName)

    ## PORTFOLIO ##
    @iswrapper
    # automatically called up when reqAccountUpdates is activated
    def updatePortfolio(self, contract:Contract, position:float,
                        marketPrice:float, marketValue:float,
                        averageCost:float, unrealizedPNL:float,
                        realizedPNL:float, accountName:str):
        update_Portfolio = self.update_Portfolio
        update_Portfolio.append({'Ctr_sym': contract.symbol, 'Ctr_secType':contract.secType,
                                 'Ctr_curr': contract.currency,'Ctr_exch': contract.exchange,
                                 'Ctr_prim': contract.primaryExchange, 'Position': position,
                                 'Mkt_price': marketPrice, 'Mkt_value': marketValue,
                                 'averageCost': averageCost, 'unreal_PnL': unrealizedPNL,
                                 'real_PnL': realizedPNL, 'account_name': accountName
                                 })
    
    ## POSITION ##
    @iswrapper
    # return all position in real-time of your account
    def position(self, account: str, contract: Contract, position: float,
                 avgCost: float):
        update_Position = self.update_Position
        update_Position.append({'Account': account, 'Symbol':contract.symbol, 
                                'SecType':contract.secType, 'Currency': contract.currency, 
                                'Position': position, 'Avg Cost': avgCost
                                })
        if(self.debug):    
            print("Position.", account, "Symbol:", contract.symbol, "SecType:",
                  contract.secType, "Currency:", contract.currency,
                  "Position:", position, "Avg cost:", avgCost)
    
    @iswrapper
    # This is called once all position data for a given request are
    # received and functions as an end marker for the position() data
    def positionEnd(self):
        if self.positionEnd_flag:
            return
        super().positionEnd()
        self.positionEnd_flag = True
        print("\nPositionEnd")
    
    ## ORDER ##
    @iswrapper
    # this event is called whenever the status of your order changes. This is
    # fired automatically when user has open order status
    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        order_Status = self.order_Status
        order_Status = [{"OrderId": orderId, "Status": status, "Filled": filled,
                  "Remaining": remaining, "AvgFillPrice": avgFillPrice,
                  "PermId": permId, "ParentId": parentId, "LastFillPrice":lastFillPrice, 
                  "ClientId": clientId, "WhyHeld":whyHeld, "MktCapPrice": mktCapPrice}]
        if(self.debug):
            print("OrderStatus. Id: ", orderId, ", Status: ", status, ", Filled: ", filled,
                  ", Remaining: ", remaining, ", AvgFillPrice: ", avgFillPrice,
                  ", PermId: ", permId, ", ParentId: ", parentId, ", LastFillPrice: ",
                  lastFillPrice, ", ClientId: ", clientId, ", WhyHeld: ",
                  whyHeld, ", MktCapPrice: ", mktCapPrice)
        
    @iswrapper
    # this function automatically called to feed in order status method
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order,
                  orderState: OrderState):
        open_Order = self.open_Order
        open_Order = [{"OrderID": orderId, "Cont_Symb":contract.symbol, 
                       "secType":contract.secType, "EXCH": contract.exchange, 
                       "Ord_Act": order.action, "Ord_Type":order.orderType,
                       "Ord_Qtty": order.totalQuantity, "Ord_State": orderState.status
                       }]
        if(self.debug):
            print("OpenOrder. ID:", orderId, contract.symbol, contract.secType,
                  "@", contract.exchange, ":", order.action, order.orderType,
                  order.totalQuantity, orderState.status)

        order.contract = contract
        self.permId2ord[order.permId] = order
    
    @iswrapper
    def openOrderEnd(self):
        if self.openOrderEnd_flag == False:
            return
        super().openOrderEnd()
        self.openOrderEnd_flag = True
        print("OpenOrderEnd")
    
    ################### MARKET DATA ###################
    
    
   
################################## END CLASS ################################## 
    

        
         
    
    
    
    
    