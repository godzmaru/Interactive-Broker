#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 16:00:31 2018

@author: hendrawahyu
"""


from ibapi import client
from ibapi import wrapper
from ibapi.contract import Contract, ContractDetails
from ibapi.ticktype import TickType, TickTypeEnum
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.common import TickerId, OrderId, TickAttrib, BarData
from ibapi.execution import Execution
from ibapi.commission_report import CommissionReport

#import time
import datetime
import logging
import pandas as pd

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
Id = 9002
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
        # Market Data
        setattr(self, 'tick_Price', [])
        setattr(self, 'tick_Size', [])   
        setattr(self, 'tick_Generic', [])        
        setattr(self, 'tick_String', []) 
        setattr(self, 'tick_EFP', [])
        # Market Scanner
        setattr(self, 'scanner_Data',[])
        # Market Depth
        setattr(self, 'update_MktDepth', [])
        setattr(self, 'update_MktDepthL2', [])
        # Execution Detail
        setattr(self, 'exec_Details', [])
        # RealTimeBar / Fundamental / Historical
        setattr(self, 'real_timeBar',[])
        setattr(self, 'historical_Data', [])
    
        ### Variables ###
        self.nKeybInt = 0
        self.permId2ord = {}
        self.nextValidOrderId = None
        self.simplePlaceOid = None
        self.account_value = 0
        self.unrealizedpnl = 0          # unrealized Profit and Loss
        
        ### Flags ###
        self.started = False
        self.flag_iserror = False
        self.accountDownloadEnd_flag = False
        self.account_SummaryEnd_flag = False
        self.globalCancelOnly = False
        self.positionEnd_flag = False
        self.openOrderEnd_flag = True
        self.debug = False
        self.tickSnapshotEnd_flag = False
        self.contract_Details_flag = False
        self.ExecDetailsEnd_flag = False
        self.ScannerDataEnd_flag = False
        self.historicalDataEnd_flag = False
        
    ################### UTILS ###################
    # callback signifying successfull connection to IBGateway
    def connectAck(self):
        if self.async:
            self.startApi()
            print('\nStarting the IB API')
    
    # error handling
    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        ERRORS_TO_TRIGGER = [103, 162, 200, 201, 399, 420, 478, 502, 504, 509, 1100, 2105]
        if errorCode in ERRORS_TO_TRIGGER:
            self.flag_iserror = True
            print('\nError:')
            print('\nId: {} - Code: {} - Message: {}'.format(reqId, errorCode, errorString))
    
    ################### ORDER ID ###################
    # receive next valid order ID
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        print("\nNext Valid Order Id: ", orderId)
        self.nextValidOrderId = orderId
        
        if self.started:
            return
        self.started = True
          
    # automatically increment order Id by 1, this MUST be used in every transaction
    # like ordering, require market update etc
    def nextOrderId(self):
        order_id = self.nextValidOrderId
        self.nextValidOrderId += 1
        return order_id
        
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
        #self.reqAccountUpdates(False, self.account)
        self.cancelAccountSummary(Id)
        self.cancelPositions()
        # cancel order
        if self.simplePlaceOid is not None:
            self.cancelOrder(self.simplePlaceOid)
            
        # cancel market data subscription
        self.cancelMktData(1101)               # require tickedId
        self.cancelMktData(1102)               # require tickedId
        #self.cancelMktDepth(1101)              # require tickerId
        #self.cancelRealTimeBars(1101)          # require tickerId
        #self.cancelHistoricalData(1101)        # require tickerId
        #self.cancelScannerSubscription(1101)    # require tickerId
        
        print("Executing cancels ... finished")
        self.disconnect()
    
    ################### ACCOUNT SUMMARY ###################    
    # similar function as reqAccountUpdates where it updates TWS Account. However,
    # it is commonly used with MULTIPLE-account structures. It will also update
    # every 3 minutes.
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency:str):
        account_Summary = self.account_Summary
        account_Summary.append({'reqId': reqId, 'account':account, 'tag':tag, 
                                'value': value, 'currency':currency}) 
    
    # called once accountSummary ends
    def accountSummaryEnd(self, reqId: int):
        print('\nAccount Summary End for ReqId: ', reqId)
        self.account_SummaryEnd_flag = True
    
    
    ############## UPDATE: ALL THESE CALLED BY reqAccountUpdates ############# 
    # automatically called up when reqAccountUpdates is activated. It ONLY receives
    # a specific SINGLE account along with a subscription flag, unlike accountSummary
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
    
    ## PORTFOLIO ##
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
    
    def updateAccountTime(self, timeStamp: str):
        self.update_AccountTime = timeStamp
        print("\nUpdateAccountTime. Time:", timeStamp)
        
    # Called after updateAccountValue() and updatePortfolio() is sent
    def accountDownloadEnd(self, accountName: str):
        super().accountDownloadEnd(accountName)
        print("\nAccount download finished:", accountName)
        self.reqAccountUpdates(False, acctCode = acc_code)
        
    ################### POSITION ###################
    # return all OPEN position in real-time of your account
    def position(self, account: str, contract: Contract, position: float,
                 avgCost: float):
        update_Position = self.update_Position
        update_Position.append({'Account': account, 'Symbol':contract.symbol, 
                                'SecType':contract.secType, 'Currency': contract.currency, 
                                'Position': position, 'Avg Cost': avgCost
                                })
    
    # This is called once all position data for a given request are
    # received and functions as an end marker for the position() data
    def positionEnd(self):
        super().positionEnd()
        self.positionEnd_flag = True
        print("\nPositionEnd")
    
    ################### ORDER ###################
    # this event is called whenever the status of your order changes. This is
    # fired automatically when user has open order status
    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        order_Status = self.order_Status
        order_Status.append({"OrderId": orderId, "Status": status, "Filled": filled,
                  "Remaining": remaining, "AvgFillPrice": avgFillPrice,
                  "PermId": permId, "ParentId": parentId, "LastFillPrice":lastFillPrice, 
                  "ClientId": clientId, "WhyHeld":whyHeld, "MktCapPrice": mktCapPrice})
        
    # this function automatically called to feed in order status method
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order,
                  orderState: OrderState):
        open_Order = self.open_Order
        open_Order.append({"OrderID": orderId, "Cont_Symb":contract.symbol, 
                       "secType":contract.secType, "EXCH": contract.exchange, 
                       "Ord_Act": order.action, "Ord_Type":order.orderType,
                       "Ord_Qtty": order.totalQuantity, "Ord_State": orderState.status})
        order.contract = contract
        self.permId2ord[order.permId] = order
    
    def openOrderEnd(self):
        if self.openOrderEnd_flag == False:
            return
        super().openOrderEnd()
        self.openOrderEnd_flag = True
        print("OpenOrderEnd")
    
    ################### MARKET DATA ###################
    # This returns 4 market data types (real-time, frozen, delayed, delayed-frozen)
    # when TWS switches from real-time to frozen or from delayed to delayed-frozen
    # refer to class above we will only use delayed version of market data type
    def marketDataType(self, reqId: TickerId, marketDataType: int):
        super().marketDataType(reqId, marketDataType)
        print("MarketDataType. ", reqId, "Type:", marketDataType)
    
    # Market data tick price callback. Handles all price related ticks. Every tickPrice
    # callback is followed by tickSize callback. value of -1 or 0 indicates no data
    # whereas positive tickPrice with positive tickSize indicates active quote
    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float,
                  attrib: TickAttrib):
        super().tickPrice(reqId, tickType, price, attrib)
        tick_Price = self.tick_Price
        tick_Price.append({"TickId": reqId, "tickType": tickType,
              "Price": price, "CanAutoExecute:": attrib.canAutoExecute,
              "PastLimit": attrib.pastLimit})
        if tickType == TickTypeEnum.BID or tickType == TickTypeEnum.ASK:
            print("PreOpen:", attrib.preOpen)
        else:
            print()
    
    # Market data tick size callback. Handles all size-related ticks
    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        super().tickSize(reqId, tickType, size)
        tick_Size = self.tick_Size
        tick_Size.append({"TickId:":reqId, "tickType":tickType, "Size": size})
    
    # market data callback
    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        super().tickGeneric(reqId, tickType, value)
        tick_Generic = self.tick_Generic
        tick_Generic.append({"TickId": reqId, "tickType": tickType, "Value": value})
        
    # market data callback to wrap independent tickSize callbacks anytime the tickSize
    # changes, and so there will be duplicate tickSize message following tickPrice
    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        super().tickString(reqId, tickType, value)
        tick_String = self.tick_String
        tick_String.append({"TickId": reqId, "Type": tickType, "Value": value})
    
    # callback for Exchange for Physicals, an off market trading mechanism that
    # enables customers to swap futures and options exposure for an offsetting
    # physical position.
    def tickEFP(self, reqId:TickerId, tickType:TickType, basisPoints:float,
                formattedBasisPoints:str, totalDividends:float,
                holdDays:int, futureLastTradeDate:str, dividendImpact:float,
                dividendsToLastTradeDate:float):
        super().tickEFP(reqId, tickType, basisPoints, formattedBasisPoints, totalDividends,
                        holdDays, futureLastTradeDate, dividendImpact, dividendsToLastTradeDate)
        tick_EFP = self.tick_EFP
        tick_EFP.append({"TickId": reqId, "Type": tickType, "basisPt": basisPoints,
                         "formattedBP":formattedBasisPoints ,"totalDividents": totalDividends,
                         "holdDays": holdDays, "futureLastTradeDate": futureLastTradeDate,
                         "dividendImpact":dividendImpact, "dividendsToLastTradeDate": dividendsToLastTradeDate})    
    
    def tickSnapshotEnd(self, reqId: int):
        super().tickSnapshotEnd(reqId)
        self.tickSnapshotEnd_flag = True
        print("\nTickSnapshotEnd:", reqId)
        
    ################### MARKET SCANNERS ###################
    # Provide a quick scan of relevant markets and return the top financial
    # instruments based on defined filtering criteria
    def scannerParameters(self, xml: str):
        super().scannerParameters(xml)
        open('log/scanner.xml', 'w').write(xml)
    
    def scannerData(self, reqId: int, rank: int, contractDetails: ContractDetails,
                    distance: str, benchmark: str, projection: str, legsStr: str):
        super().scannerData(reqId, rank, contractDetails, distance, benchmark,
                            projection, legsStr)
        scanner_Data = self.scanner_Data
        scanner_Data.append({"ReqId": reqId, "Rank": rank, "Symbol": contractDetails.summary.symbol,
              "SecType": contractDetails.summary.secType, "Currency": contractDetails.summary.currency,
              "Distance": distance, "Benchmark": benchmark,
              "Projection": projection, "Legs String": legsStr})
    
    def scannerDataEnd(self, reqId: int):
        super().scannerDataEnd(reqId)
        self.ScannerDataEnd_flag = True
        print("ScannerDataEnd. ", reqId)
    
    ################### MARKET DEPTH ###################
    # Market Depth is a property of the orders that are contained in the limit
    # order book at a given time OR in other words, the amount that will be
    # traded for a limit order with a given price by given size. This request
    # must be direct-routed to an exchange
    def updateMktDepth(self, reqId: TickerId, position: int, operation: int,
                       side: int, price: float, size: int):
        super().updateMktDepth(reqId, position, operation, side, price, size)
        update_MktDepth = self.update_MktDepth
        update_MktDepth.append({"TickId": reqId, "Position": position, 
                               "Operation": operation, "Side": side, "Price": price, 
                               "Size": size})
    
    def updateMktDepthL2(self, reqId: TickerId, position: int, marketMaker: str,
                         operation: int, side: int, price: float, size: int):
        super().updateMktDepthL2(reqId, position, marketMaker, operation, side,
                                 price, size)
        update_MktDepthL2 = self.update_MktDepthL2
        update_MktDepthL2.append({"TickId": reqId, "Position": position, 
                                  "Operation":operation, "Side": side, "Price": price, 
                                  "Size": size})
    
    ################### CONTRACT DETAIL ###################
    # Full contract's definition
    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        super().contractDetails(reqId, contractDetails)
        attrs = vars(contractDetails.summary)
        print(', '.join("%s: %s" % item for item in attrs.items()))
    
    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        self.contract_Details_flag = True
        print("ContractDetailsEnd. ", reqId, "\n")
   
    ################### EXECUTION DETAIL ###################
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        super().execDetails(reqId, contract, execution)
        exec_Details = self.exec_Details
        exec_Details.append({"reqId": reqId, "symbol":contract.symbol, "secType":contract.secType, 
                             "curr":contract.currency, "execId":execution.execId, 
                             "execOrderId":execution.orderId, "execShares":execution.shares, 
                             "execLastLiquidity":execution.lastLiquidity})
    
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        self.ExecDetailsEnd_flag = True
        print("ExecDetailsEnd. ", reqId)
    
    def commissionReport(self, commissionReport: CommissionReport):
        super().commissionReport(commissionReport)
        print("CommissionReport. ", commissionReport.execId, commissionReport.commission,
              commissionReport.currency, commissionReport.realizedPNL)
    
    ################### FUNDAMENTAL / REALTIMEBAR / HISTORICAL ###################
    def fundamentalData(self, reqId: TickerId, data: str):
        super().fundamentalData(reqId, data)
        self.fundamental_Data_data = data
        print("FundamentalData. ", reqId, data)
    
    def realtimeBar(self, reqId:TickerId, time:int, open:float, high:float,
                    low:float, close:float, volume:int, wap:float, count:int):
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        real_timeBar = self.real_timeBar
        real_timeBar.append({"ReqId": reqId, "time": time, "open": open,
              "high": high, "low": low, "close": close, "volume": volume,
              "wap": wap, "count": count})
    
    def historicalData(self, reqId:int, bar: BarData):
        super().historicalData(reqId, bar)
        historical_Data = self.historical_Data
        historical_Data.append({"ReqId": reqId, "Date": bar.date, "Open": bar.open,
              "High": bar.high, "Low": bar.low, "Close": bar.close, "Volume": bar.volume,
              "Count": bar.barCount, "WAP": bar.average})
    
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        self.historicalDataEnd_flag = True
        print("HistoricalDataEnd ", reqId, "from", start, "to", end)
    
################################## END CLASS clientApp ################################## 
    

    
        
         
    
    
    
    
    