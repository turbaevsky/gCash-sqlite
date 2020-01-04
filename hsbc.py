#!/usr/bin/python3

import urllib, re, datetime, sys
#pd.core.common.is_list_like = pd.api.types.is_list_like
#import pandas_datareader.data as web
#import matplotlib.pyplot as plt
import logging

from sqlalchemy import create_engine
engine = create_engine('sqlite:///004.sqlite', echo=False)

log = logging.getLogger()
logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-7s ' +
											  '%(threadName)-15s %(message)s', level=logging.DEBUG)


def hsbc(d=0):
	import pandas as pd
	''' return HSBC Adventures fund '''
	url = 'https://www.hl.co.uk/funds/fund-discounts,-prices--and--factsheets/search-results/h/hsbc-world-selection-adventurous-portfolio-c-income/invest'
	user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
	headers = {'User-Agent': user_agent}
	req = urllib.request.Request(url, headers=headers)
	with urllib.request.urlopen(req) as response:
		html = response.read().decode('utf-8')

	#response = urllib.request.urlopen(p)
	#html = response.read().decode('utf-8')
	#print(html)
	price = re.search(r"bid price-divide\D*(\d{3}.\d{2})",html).group(1)
	l = re.search(r"Prices as at\W+(\d{1,2}\W+\w{3,10}\W+\d{4})",html).group(1)
	date = datetime.datetime.strptime(l, "%d %B %Y").strftime("%Y-%m-%d")
	conn = engine.connect()
	last = conn.execute('select * from R72 where Date="{}"'.format(date)).first()
	if last is None:
		conn.execute('insert into R72 (Date, Close) values ("{}",{})'.format(date,price))


if __name__ == '__main__':
	hsbc()
