import urllib.request
import json
import sys
import os
import inspect
import yaml
from datetime import date
import config

YAML_FILENAME = '\\data\\' + str(date.today()) + '_stock_data.yml'

def requestQuotes(symbols):
    req = urllib.request.Request("https://sandbox.tradier.com/v1/markets/quotes?symbols=%s" % (symbols))
    req.add_header('Accept', 'application/json')
    req.add_header('Authorization', "Bearer %s" % config.TRADIER_API_KEY)
    response = urllib.request.urlopen(req)
    return response.read().decode('utf-8')

def get_script_dir(follow_symlinks=True):
    # from http://stackoverflow.com/questions/3718657/how-to-properly-determine-current-script-directory-in-python/22881871#22881871
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

def writeData(data):
    # based on the file naming, a new file should be used every day
    for q in data['quotes']['quote']:
        with open(get_script_dir() + YAML_FILENAME, 'a') as f:
            yaml.dump(q, f, explicit_start=True, default_flow_style=False);

def parseQuotes(quotes):
    return json.loads(quotes) 

def readYamlResults():
    # used for debugging
    stream = open(get_script_dir() + YAML_FILENAME, "r")
    docs = yaml.load_all(stream)
    for doc in docs:
        for k,v in doc.items():
            if k == 'trade_date' or k == 'ask_date' or k == 'bid_date':
                print(k, "=>", datetime.fromtimestamp(v / 1e3).strftime("%Y-%m-%d %H:%M:%S"))
            else:
                print(k, "->", v)
        print("\n")

def main():
    symbols = 'AAPL,GILD,FB,BRCM,C,CBS,CSCO,CSX,ETFC,GM,GPS,HAL,KO,MRK,MS,NOV,QID,SBUX,USO,VZ,WFM,X,XLNX'
    data = parseQuotes(requestQuotes(symbols))
    writeData(data)

if __name__ == '__main__':
    main()
