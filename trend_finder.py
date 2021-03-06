import urllib.request
import urllib.error
import json
import sys, getopt
from datetime import datetime, timedelta, date
import time
import config
import os
import pandas as pd
# BDay is business day, not birthday
from pandas.tseries.offsets import BDay
from pandas.tseries.holiday import USFederalHolidayCalendar

FILENAME = "trend.stk"
FILE_DIR = "C:\\Users\\cduggan\\workspace\\stocks\\data\\" + str(date.today())
UPTREND = "up"
DOWNTREND = "down"

def getStartDate():
    # get 200 business days since yesterday but leave room in case this is run on weekend
    yesterday = date.today() - timedelta(days=1)
    start_date = yesterday - BDay(202)

    # find the number of holidays between yesterday and 200 days ago and subtract that to get real start date
    calendar = USFederalHolidayCalendar()
    holidays = calendar.holidays(start_date, yesterday)

    start_date = start_date - BDay(len(holidays.tolist()))

    s = pd.Series(start_date)
    return s.map(pd.Timestamp.date)[0]

def requestHistory(symbol, start_date):
    req = urllib.request.Request("https://sandbox.tradier.com/v1/markets/history?symbol=%s&start=%s" % (symbol, start_date))
    req.add_header('Accept', 'application/json')
    req.add_header('Authorization', "Bearer %s" % config.TRADIER_API_KEY)
    response = urllib.request.urlopen(req)
    return response.read().decode('utf-8')

def writeData(symbols, trend):
    filename = FILE_DIR + '_' + trend + '_' + FILENAME

    target = open(filename, 'w')
    target.truncate()
    target.write(symbols)
    target.write("\n")
    target.close()

def determineTrend(symbol, twenty_ma, forty_ma, two_hundred_ma):
    # TODO get weekly and only if in up/down trend on both add to list?
    # uptrend
    if twenty_ma > forty_ma > two_hundred_ma:
        print("%s is uptrending" % symbol)
        return dict(UPTREND=symbol)
    elif two_hundred_ma > forty_ma > twenty_ma:
        print("%s is downtrending" % symbol)
        return dict(DOWNTREND=symbol)

def parseHistory(history, symbol):
    j = json.loads(history)
    if j['history'] == None:
        print("%s: cannot get data so skipping" % (symbol))
        return

    twenty_ma = 0
    forty_ma = 0
    two_hundred_ma = 0
    total_price = 0
    i = 0

    # sort so newest date is processed first, for calculating moving averages
    j['history']['day'].reverse()

    for h in j['history']['day']:
        # analyze each day's data
        for key, value in h.items():

            # get price (for calculations)
            if key == 'close':
                total_price += value

                # increment counter (of number of dates we've processed)
                i += 1

                if i == 20:
                    twenty_ma = total_price / i
                if i == 40:
                    forty_ma = total_price / i
                if i == 200:
                    two_hundred_ma = total_price / i

    # check if we have the 200 period moving average and if not, use whatever values we have to calculate as close to it as possible
    if two_hundred_ma == 0:
        print("%s: do not have 200 prices so using what we have, which is %d prices" % (symbol, i))
        two_hundred_ma = total_price / i

    return determineTrend(symbol, twenty_ma, forty_ma, two_hundred_ma)

def readSymbolsFromFile(filename):
    target = open(filename, 'r')
    data = [line.strip() for line in target]
    return data

def main(argv):
    # default values
    symbols = 'QQQ,SPY'
    
    try:
        opts, args = getopt.getopt(argv, "hs:f:")
    except:
        print('trend_finder.py -s <CSV of symbols> -f <stocks filename>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('trend_finder.py -s <CSV of symbols> -f <stocks filename>')
            sys.exit()
        else:
            if opt in ('-s', '--symbols'):
                symbols = arg
            if opt in ('-f', '--stocksFile'):
                symbols = ",".join(readSymbolsFromFile(arg))
    symbols = symbols.split(',')

    print("%s: Executed trend_finder.py" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    start_date = getStartDate()
    uptrend_symbols = []
    downtrend_symbols = []
    for symbol in symbols:
        # if we fail, try up to 2 more times
        for attempt in range(2):
            try:
                trend = parseHistory(requestHistory(symbol, start_date), symbol)
                if trend is not None:
                    t = list(trend.keys())[0]
                    s = list(trend.values())[0]
                    if t == 'DOWNTREND':
                        downtrend_symbols.append(s)
                    if t == 'UPTREND':
                        uptrend_symbols.append(s)
            except (urllib.error.HTTPError):
                print('Rate limit hit; sleeping for 1 minute')
                time.sleep(60)
            else:
                break

    
    if uptrend_symbols != []:
        writeData("\n".join(uptrend_symbols), UPTREND)
    if downtrend_symbols != []:
        writeData("\n".join(downtrend_symbols), DOWNTREND)

if __name__ == '__main__':
    main(sys.argv[1:])


