import logging
import datetime
import statistics
from time import sleep
from alice_blue import *
import datetime as dw
from datetime import timezone
import xlwings as xw
import threading
import json

# Config
f = open('user.json')
data = json.load(f)

username=data['username']
password=data['password']
api_secret=data['api_secret']
twoFA=data['twoFA']

logging.basicConfig(level=logging.DEBUG)        # Optional for getting debug messages.
# Config

#Variables Declaration


stock_list={
    "RELIANCE" :1.00,	
    "HDFCBANK":0.59,
    "TCS":0.32
    }
ltp = 0
socket_opened = False
alice = None
high=0
low=0

token=''
timestamp=0
inst_tup=()
stack=[]
trade_dict={}
tuple_list=[]



def event_handler_quote_update(message):
    global ltp
    global high
    global low
    global token
    global timestamp
    
    ltp = message['ltp']
    high=message['high']
    low=message['low']
    token=message['token']
    #timestamp=message['exchange_time_stamp']
    #print(ltp,high,low,token)
    stack.append({message['token']:message['ltp']})
    #print(stack.pop())
    sleep(0.35)
   
	

def open_callback():
    global socket_opened
    socket_opened = True

    
def tuple_list_generator():
    #global trade_dict
    #global tuple_list
    for i in stock_list:
        inst_tuple=alice.get_instrument_by_symbol('NSE', i)
        tuple_list.append(inst_tuple)
        #print("TUPLE KA TYPE", type(inst_tuple))
        #trade_dict[inst_tuple[2]]={"token":inst_tuple[1]}
        trade_dict[str(inst_tuple[1])]={"symbol":inst_tuple[2]}
        print(trade_dict)
    print(tuple_list)


def sort_watchlist():
    global stock_list
    stock_list = sorted(stock_list.items(), key=lambda x: x[1], reverse=False)

def buy_signal(ins_scrip): #,buy_price,stop_loss
        global alice
        alice.place_order(transaction_type = TransactionType.Buy,
                         instrument = ins_scrip,
                         quantity = 1,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)

def sell_signal(ins_scrip): #,sell_price,stop_loss

    global alice
    alice.place_order(transaction_type = TransactionType.Sell,
                         instrument = ins_scrip,
                         quantity = 1,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)
 
    
def main():
    global socket_opened
    global alice
    global username
    global password
    global twoFA
    global api_secret
    global EMA_CROSS_SCRIP
    global stock_list
    global tuple_list
    global row_no
    global low
    global high
    global token
    global ltp
    global inst_tup
    global stack
    global trade_dict
    count=0
    trade_count=0
    trade_dict={}
    high_stream = []
    low_stream = []
    minute_close = []
    lock = threading.Lock()
    temp={}
  
   
    #Getting access token & Alice Object by passing username and password
    access_token =  AliceBlue.login_and_get_access_token(username=username, password=password, twoFA=twoFA,  api_secret=api_secret)
    alice = AliceBlue(username=username, password=password, access_token=access_token, master_contracts_to_download=['NSE'])

    stock_list = sorted(stock_list.items(), key=lambda x: x[1], reverse=False)
    for i in stock_list:
        inst_tuple=alice.get_instrument_by_symbol('NSE', i[0])
        print("TUPLE KA TYPE", type(inst_tuple))
        #trade_dict[inst_tuple[2]]={"token":inst_tuple[1]}
        trade_dict[str(inst_tuple[1])]={"symbol":inst_tuple[2]}
        tuple_list.append(inst_tuple)
    print(tuple_list)
    print("-----------------------------------")
    print(trade_dict)
    #Genearting tuple_list for subscription
    #tuple_list_generator()
    
    #Sort watchlist according to % Increase
    #sort_watchlist()

   

   

        
##    print(alice.get_balance()) # get balance / margin limits
    print(alice.get_profile()) # get profile
##    print(alice.get_daywise_positions()) # get daywise positions
##    print(alice.get_netwise_positions()) # get netwise positions
##    print(alice.get_holding_positions()) # get holding positions
    
    #socket opening
    socket_opened = False
    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                          socket_open_callback=open_callback,
                          run_in_background=True)
    while(socket_opened==False):    # wait till socket open & then subscribe
        pass
    

    #subscribe to feeds
    alice.subscribe(tuple_list, LiveFeedType.MARKET_DATA)
    
   

    #Setting Breakout Timings
    breakout_time=dw.time(22,50)
    time_threshold=dw.time(23,00)

    time=dw.datetime.now().time()
    time_now=dw.time(time.hour,time.minute)


    #breakout_time=dw.time(23,40).strftime("%H:%M")
    #time_threshold=dw.time(23,45).strftime("%H:%M")

    
    #time_now=dw.datetime.now().time().strftime("%H:%M")

    while(time_now < breakout_time ):
           time=dw.datetime.now().time()
           time_now=dw.time(time.hour,time.minute)
           print("Time now",time_now)
           print("Start Time",breakout_time)
           print("waiting")
           sleep(0.5)
           #print(stack)
            
    
    print(type(time_now))
    print(type(breakout_time))
    while(time_now==breakout_time and count<len(stock_list)):
        
        for key in trade_dict:
            print("key",type(key),key)
            print("token",type(token),token)
            if(key==str(token) and 'added' not in trade_dict[key].values() ):
                #print("breakout",token,key)
                trade_dict[key]['low']=low
                trade_dict[key]['high']=high
                trade_dict[key]['ltp']=ltp
                trade_dict[key]['added']='added'
                count=count+1
               
    while( time_now <= time_threshold and trade_count < (len(stock_list)) ):
        for key in trade_dict:
         if(len(stack)>0):
          temp=stack.pop()
          sleep(0.35)
          keyy=int(key)
          if((keyy in temp)  and 'bought' not in trade_dict[key].values() and 'sold' not in trade_dict[key].values()):
                trade_dict[key]['ltp']=temp[keyy]
                print(temp,"temp")
                print("key",keyy)
                if (trade_dict[key]['ltp'] <= trade_dict[key]['low'] and 'sold' not in trade_dict[key].values()) :
                        print("sell triggered for : ",key,trade_dict[key]['symbol'])
                        #Entry Price Calculation
                        low=trade_dict[key]['low']
                        entry_price=low-(low*0.001)
                        entry_price=(round(entry_price*20.0)/20.0)
                        #mod_sl=stop_loss+(stop_loss*0.001)
                        #mod_sl=(round(mod_sl*20.0)/20.0)
                        #Entry Price Calculation
                        
                        for tup in tuple_list:
                             
                             if (tup[1]==int(key)):
                                #inst_tup=tup
                                print("INSTRUMENT TUPLE TYPE",type(tup),tup[2],"==",key,tup[1],"==",key)
                                alice.place_order(transaction_type = TransactionType.Sell,
                                                 instrument = tup,
                                                 quantity = 1,
                                                 order_type = OrderType.StopLossMarket,
                                                 product_type = ProductType.Intraday,
                                                 price =None ,
                                                 trigger_price =entry_price ,
                                                 stop_loss = None,
                                                 square_off = None,
                                                 trailing_sl = None,
                                                 is_amo = False)
                                #sell_signal(tup)
                                #sell_signal(tup, trade_dict[key]['low'],trade_dict[key]['high'])
                                sleep(0.025)
                                trade_dict[key]['status']='sold'
                                trade_count=trade_count+1
                                print("sell complted",key)
                                
                elif ( trade_dict[key]['ltp'] >= trade_dict[key]['high'] and 'bought' not in trade_dict[key].values()) :
                            print("buy triggered for : ",key,trade_dict[key]['symbol'])

                            #Entry Price Calculation
                            high=trade_dict[key]['high']
                            entry_price=high+(high*0.001)
                            entry_price=(round(entry_price*20.0)/20.0)
                            #mod_sl=stop_loss-(stop_loss*0.001)
                            #mod_sl=(round(mod_sl*20.0)/20.0

                            #Entry Price Calculation
                                    
                            for tup in tuple_list:
                              #print(tup[2],trade_dict[key])
                              if (tup[1]==int(key)):
                                alice.place_order(transaction_type = TransactionType.Buy,
                                                 instrument = tup,
                                                 quantity = 1,
                                                 order_type = OrderType.StopLossMarket,
                                                 product_type = ProductType.Intraday,
                                                 price =None,#entry_price ,
                                                 trigger_price =entry_price,#high ,
                                                 stop_loss = None,
                                                 square_off = None,
                                                 trailing_sl = None,
                                                 is_amo = False)
                                #buy_signal(trade_dict[key], trade_dict[key]['high'],trade_dict[key]['low'])

                                sleep(0.025)
                                trade_dict[key]['status']='bought'
                                trade_count=trade_count+1
                                print("buy completed",trade_dict)
                               
                                
        #time=dw.datetime.now().time()
        #time_now=dw.datetime.now().time().strftime("%H:%M")
    time=dw.datetime.now().time()
    time_now=dw.time(time.hour,time.minute)
if(__name__ == '__main__'):
    main()
##[Instrument(exchange='NSE', token=11373, symbol='BIOCON', name='BIOCON LIMITED.', expiry=None, lot_size=None),
## Instrument(exchange='NSE', token=10099, symbol='GODREJCP', name='GODREJ CONSUMER PRODUCTS', expiry=None, lot_size=None),
## Instrument(exchange='NSE', token=13404, symbol='SUNTV', name='SUN TV NETWORK LIMITED', expiry=None, lot_size=None)]
##{'11373': {'symbol': 'BIOCON'},
## '10099': {'symbol': 'GODREJCP'},
## '13404': {'symbol': 'SUNTV'}}
