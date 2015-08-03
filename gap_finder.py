import urllib.request
import json
import sys, getopt
from datetime import datetime, timedelta, date
import config
import os

def requestQuotes(symbols):
    req = urllib.request.Request("https://sandbox.tradier.com/v1/markets/quotes?symbols=%s" % (symbols))
    req.add_header('Accept', 'application/json')
    req.add_header('Authorization', "Bearer %s" % config.TRADIER_API_KEY)
    response = urllib.request.urlopen(req)
    return response.read().decode('utf-8')

def writeData(symbols):
    filename = "C:\\Users\\cduggan\\workspace\\stocks\\gaps.stk"

    # if file exists, assume it is yesterday's and move it
    if os.path.isfile(filename):
        yesterday = date.today() - timedelta(days=1)
        os.rename(filename, "C:\\Users\\cduggan\\workspace\\stocks\\data\\" + str(yesterday) + "_gaps.stk")

    target = open(filename, 'w')
    target.truncate()
    target.write(symbols)
    target.close()

def readSymbolsFromFile(filename):
    target = open(filename, 'r')
    data = [line.strip() for line in target]
    return data

def calculateGapPercentage(current, yesterday_close):
    if yesterday_close == 0:
        return 0
    diff = abs(current - yesterday_close)
    percentage = diff / yesterday_close * 100
    return percentage

def parseQuotes(quotes, percentage):
    sb = []
    j = json.loads(quotes)
    for q in j['quotes']['quote']:
        # analyze each quote
        for key, value in q.items():
            if key == 'volume':
                volume = value
            if key == 'symbol':
                symbol = value
            if key == 'bid':
                bid = value
            if key == 'prevclose':
                yesterday_close = value

        # let's skip gaps that don't have significant volume
        if volume > 10000:
            gap_percentage = calculateGapPercentage(bid, yesterday_close)
            if gap_percentage >= percentage:
                print("%s has a %f%% gap \n" % (symbol, gap_percentage))
                sb.append(symbol)
                sb.append("\n")

    writeData(''.join(sb))

def main(argv):
    # default values
    symbols = 'QQQ,SPY'
    percentage = 1
    
    try:
        opts, args = getopt.getopt(argv, "hsp:f:")
    except:
        print('test.py -s <CSV of symbols> -p <gap percentage> -f <stocks filename>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -s <CSV of symbols> -p <gap percentage> -f <stocks filename>')
            sys.exit()
        else:
            if opt in ('-s', '--symbols'):
                symbols = arg
            if opt in ('-p', '--gapPercentage'):
                percentage = float(arg)
            if opt in ('-f', '--stocksFile'):
                symbols = ",".join(readSymbolsFromFile(arg))

    print("%s: Executed gap_finder.py" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    parseQuotes(requestQuotes(symbols), percentage)

if __name__ == '__main__':
    main(sys.argv[1:])


