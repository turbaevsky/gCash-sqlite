from . import db
from .models import *
from app import app
from datetime import date, timedelta, datetime
from flask_appbuilder.api import BaseApi, expose
from . import appbuilder
from flask_appbuilder.security.decorators import * #protect
import time 		 # TODO load only neccesary libs

from flask import Flask, render_template
from sqlalchemy import create_engine

import plotly.io as pio
import json


class reportApi(BaseApi):
	@expose('/info/showAll')
	@protect(allow_browser_login=True)
	def gnucash(self):
		''' get sum for accounts '''
		# TODO add monitored accounts and their description to the DB
		gbp = getSum([0,1,2,3,4,5,17])
		debit = getSum([0])
		future = getSum([0], True)
		credit = getSum([1])
		Lena = getSum([2])
		cash = getSum([3])
		saving = getSum([4, 17])
		depo = getSum([6])
		pFunds = getSum([14,15])
		pShares = getSum([16])
		usd = getSum([10])
		eur = getSum([11])
		uah = getSum([12, 13])
		############# TODO: check the next two calculations #################
		shares, sharesBalance = balance()
		funds, fundBalance = balance(True)
		passv = depo + pFunds + pShares + shares + funds
		################# currencies ###################
		try: usdr, eurr, uahr , state = getEx()
		except: usdr, eurr, uahr, state = 1/1.2, 1/1.1, 1/30, 'offline'
		gusd, usdr = int(usd * usdr), round(1/usdr,2)
		geur, eurr = int(eur * eurr), round(1/eurr,2)
		guah, uahr = int(uah * uahr), round(1/uahr,2)
		allGBP = gbp + depo + pFunds + pShares	
		allTogether = gbp + passv + gusd + geur + guah


		#return self.response(200, message=locals())
		return {'gbp':gbp, 'debit':debit, 'future':future, 'Lena':Lena, 'credit':credit, 'cash':cash, 'saving':saving,
		'depo':depo, 'pFunds':pFunds, 'pShares':pShares, 'usd':usd, 'eur':eur, 'uah_cash':getSum([12]), 
		'uah_Kiev':getSum([13]), 'allGBP':allGBP, 'allTogether': allTogether}


def getSum(aList=[], future=False):
	''' get sum of any account(s) '''
	s = db.session()
	acc = ['36ca6c050017fb0411f0429072eb94f9','bf57f831079e04fdfffaaa77b5c6c50b',
		   '6cdb149b59eb612e1093e57710e2292a','4f514a136423e51d60d91de4215a6263',
		   '433df83f394a96a406c7824429ca9422','5a6b5626fcd145f8e37efe00482b43ad',
		   '3f101daa9afd65b888534b9d832671ba','755326ea42e00480468aece5300017b0',
		   '2d5a4b2698328d8f1386edf955646f3e','799c694356c5f11fc7219506575ebb22',
		   'ff453952aea2803d07cd50652929f2fa','a57ee8ea5270893bbf52d55c919c57c7',
		   '89b203dca0e73bb654a0cab45216e88b','3e1f4f3a4291b35f426b91a174d4b62a',
		   '0dfbe6dde9babb418c3c513041ebb9a0','853c793bc370b269116a6f61a230e4fb',
		   'cb1848385cc178de78ee9d021fb7db5a','fb6f3fc8c958d602fe22e00337eba9bd']

	if not future:
		cur_date = date.today().strftime('%Y-%m-%d')+" 23:59:59"
	else:
		cur_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')+" 23:59:59"

	tx = s.query('guid FROM transactions WHERE post_date<="{}"'.format(cur_date)).all()
	t = [a[0] for a in tx]
	a_list = [acc[a] for a in aList]
	sm = s.query('SUM(quantity_num)/100').filter(splits.account_guid.in_(a_list)).filter(splits.tx_guid.in_(t)).all()[0][0]
	return sm


def balance(fund=False):
	''' calculate active stocks and fund balance '''
	session = db.session()
	if not fund: 
		arr = session.query(stocks.symbol).filter(stocks.isActive==1).all()
	else: 
		arr = session.query(funds.name).filter(funds.isActive==1).all()
	try:
		shares, sharesBalance = 0, 0
		for sym in arr:
			try: 
				s, b = gain(sym) if not fund else gain(sym, True)
				shares += int(s)
				sharesBalance += int(b)
			except Exception as e:
				# TODO fix fund taxation
				if not fund:
					shares = session.query('sum(amount*price - tax) from stocks where symbol="{}"'.format(sym)).one()[0]
				else:
					shares = session.query('sum(amount*price - tax) from funds where symbol="{}"'.format(sym)).one()[0]
				sharesBalance = e
	except Exception as e:
		shares, sharesBalance = 0, e
	return shares, sharesBalance


def gain(sym, fund=False):
	''' calculate gain for symbol '''
	session = db.session()
	current = cur(sym)['price']
	if not fund and sym[0]!='^':
		#try:
		df = session.query(stocks).filter(stocks.isActive==1).all()
		buy = df[0]['amount']*df[0]['price']
		sell = df[0]['amount']*current*0.01 - df[0]['tax']*2 - (buy * df[0]['fee'])
		gain = (int(sell-buy))
			#print('buy {} sell {} gain {}'.format(buy,sell,gain))
		#except Exception as e:
		#	gain = e,buy,sell,gain
	elif fund:
		df = session.query(funds.name).filter(funds.isActive==1).all()
		buy = df[0]['amount']*df[0]['long']
		tax = df[0]['tax']
		date = df[0]['date']
		#diff = (pd.to_datetime('today') - pd.to_datetime(date)).days
		# TODO: implement dimedelta calculation
		tax = df[0]['amount']*current*tax*0.01/365*diff
		sell = df[0]['amount']*current - tax
		gain = (int(sell-buy))
	else:
		gain=0
	return int(sell), gain


def cur(sym):
	''' read current quote from yahoo NO PANDAS'''
	import urllib.request, json 
	url = 'https://query1.finance.yahoo.com/v7/finance/quote?symbols='+sym
	with urllib.request.urlopen(url) as url:
		r = json.loads(url.read().decode())
		r = r['quoteResponse']['result'][0]
	return {'price':r['regularMarketPrice'], 
			'change': round(r['regularMarketChangePercent'],2),
			'low': r['regularMarketDayLow'], 
			'high': r['regularMarketDayHigh'], 
			'state': r['marketState'], 
			'symbol': r['symbol'], 
			'time': time.strftime("%B %d %H:%M", time.localtime(int(r['regularMarketTime'])))}


def getEx():
	''' return currency exchange rates '''
	rate=[]
	for c in ['USDGBP=X','EURGBP=X','UAHGBP=X']:
		rate.append(cur(c)['price'])
		
	try:
		usdr = rate[0]
		eurr = rate[1]
		uahr = rate[2]
		state = 'Act'
	except Exception as er:
		usdr = 0.81
		eurr = 0.89
		uahr = 0.033
		state = 'Saved'

	return usdr, eurr, uahr, state


### next will be 'Last transaction'


class monthreportApi(BaseApi):

	@expose('/info/prescan')
	@protect(allow_browser_login=True)
	def findStock(self):
		engine = create_engine('sqlite:///004.sqlite')
		conn = engine.connect()

		lst = conn.execute('select code from ftse100', as_dict=True)
		scanned = prescan(lst)

		conn.close()

		return dict(scanned=scanned)


	@expose('/info/monthly')
	@protect(allow_browser_login=True)
	def monthReport(self):

		import plotly.express as px

		engine = create_engine('sqlite:///004.sqlite')
		conn = engine.connect()

		cons_dict = {"date":[], "sum":[], "type":[]}
		inc_dict = {"date":[], "sum":[], "type":[]}

		#session = db.session()

		acc = ['"36ca6c050017fb0411f0429072eb94f9"','"bf57f831079e04fdfffaaa77b5c6c50b"',
			   '"6cdb149b59eb612e1093e57710e2292a"','"4f514a136423e51d60d91de4215a6263"']

		expences = dict()
		today = datetime.today()

		#dates = pd.date_range(end='2021-01-31', periods=16, freq='1M').strftime("%Y-%m-%d").values
		dates = ['2019-10-31', '2019-11-30', '2019-12-31', '2020-01-31',
	   '2020-02-29', '2020-03-31', '2020-04-30', '2020-05-31',
	   '2020-06-30', '2020-07-31', '2020-08-31', '2020-09-30',
	   '2020-10-31', '2020-11-30', '2020-12-31', '2021-01-31']
		# TODO: remove hardcode

		for i in range(len(dates)-1):
			start = dates[i]
			end = dates[i+1]

			to_acc = conn.execute('select guid, name from accounts where \
				(parent_guid = "89ab14f49063d6f189955700f8fa75f7" \
				or guid in ("5bd720ffe83fd9592488a9e10c43a605",\
				"c6008ebaab83653b94284597ad844ff2","281a489ce89414170f2c215f451f8b78")) \
				and hidden=0')

			cons = conn.execute("select a.name name, sum(s.value_num*826/c.cusip)/c.fraction s from transactions t \
				left join splits s on t.guid = s.tx_guid inner \
				join accounts a on a.guid = s.account_guid inner join commodities c \
				on c.guid = t.currency_guid \
				where t.post_date between '{}' and '{}' \
				and s.account_guid in ({}) \
				and s.value_num > 0 \
				and t.description not in ('None','Transfer','Credit') \
				group by s.account_guid".format(start, end, ','.join(["'"+a[0]+"'" for a in to_acc])))

			cons = [{column: value for column, value in rowproxy.items()} for rowproxy in cons]	

			for c in cons:
				cons_dict['date'].append(end)
				cons_dict['sum'].append(c['s'])
				cons_dict['type'].append(c['name'])


			inc = conn.execute("select a.name, abs(sum(s.value_num*826/c.cusip)/c.fraction) s from transactions t \
				left join splits s on t.guid = s.tx_guid inner \
				join accounts a on a.guid = s.account_guid inner join commodities c \
				on c.guid = t.currency_guid \
				where t.post_date between '{}' and '{}' \
				and s.account_guid in ({}) \
				and s.value_num < 0 \
				and t.description not in ('None','Transfer','Credit') \
				and t.currency_guid = '7ae5ecaa925fae150839e48e784fcf61' \
				group by s.account_guid".format(start, end, ','.
					join(["'"+a+"'" for a in ["5bd720ffe83fd9592488a9e10c43a605", "ccc4bbcb6830dfce5988402798d98521"]])))

			inc = [{column: value for column, value in rowproxy.items()} for rowproxy in inc if rowproxy]

			for c in inc:
				inc_dict['date'].append(end)
				inc_dict['sum'].append(c['s'])
				inc_dict['type'].append(c['name'])

		
		fig1 = pio.to_html(px.bar(cons_dict, x="date", y="sum", color='type'))
		fig2 = pio.to_html(px.bar(inc_dict, x="date", y="sum", color='type'))

		conn.close()

		return render_template('plot.html', fig1=fig1, fig2=fig2)


	@expose('/info/rest')
	@protect(allow_browser_login=True)
	def rest(self):

		# the same for 2020
		acc = ['"36ca6c050017fb0411f0429072eb94f9"','"bf57f831079e04fdfffaaa77b5c6c50b"',
		'"6cdb149b59eb612e1093e57710e2292a"','"4f514a136423e51d60d91de4215a6263"']
		
		start = '2020-01-01'
		end = '2020-12-31'

		engine = create_engine('sqlite:///004.sqlite')
		conn = engine.connect()

		s = conn.execute("select sum(s.value_num)/100 sum \
		from transactions t left join splits s on t.guid = s.tx_guid inner \
		join accounts a on a.guid = s.account_guid inner join commodities c \
		on c.guid = t.currency_guid \
		where t.post_date between '{}' and '{}' \
		and s.account_guid in ({}) \
		and s.value_num < 0 \
		and t.description not in ('None','Transfer','Credit') \
		order by t.post_date".format(start, end, ','.join(acc)))

		s = [{column: value for column, value in rowproxy.items()} for rowproxy in s]	

		r = reportApi()

		rest = int(r.gnucash()['allTogether']) + int(s[0]['sum'])
		avg = 2000
		corr2020 = (112+50+28+24+21+37+75/3+33+300)*12
		rent2020 = 975*2
		# add rest
		rest -= corr2020
		rest -= rent2020
		mn = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
		restYr = 2021+int(rest/(avg*12))
		restMn = (rest/(avg*12) - int(rest/(avg*12)))*12
		u = 'saving enough until {} {} (spenging {} per month) incl. {} ({} per month) correction for 2020 for utilities, food and education,\
			 and {} renting for Nov and Dec 2020'\
			.format(mn[int(restMn)], restYr, avg, int(corr2020), int(corr2020/12), rent2020)

		conn.close()

		return dict(yr2020='currently {}, corrected {} will be spent in 2020'.\
			format(int(s[0]['sum']), int(s[0]['sum'])-corr2020-rent2020), \
			willRest='{} will rest by the end of 2020'.format(rest), \
			upTo = u,
			)


	@expose('/info/indices')
	@protect(allow_browser_login=True)
	def plotIndices(self, depth = 400):
		import pandas as pd
		import plotly.express as px
		from sklearn import preprocessing
		import plotly.graph_objects as go
		import app.TA2 as TA2
		# fill the indeces

		dji = yahoo2('^DJI','1d', period=depth)
		ftse = yahoo2('^FTSE','1d', period=depth)

		dji.Date = dji.Date.apply(lambda x: x[0:9])
		ftse.Date = ftse.Date.apply(lambda x: x[0:9])

		engine = create_engine('sqlite:///004.sqlite')
		conn = engine.connect()

		hsbc = pd.DataFrame.from_dict(conn.execute('select * from R72',as_dict = True))
		hsbc.columns = ['Close','Date','id']
		hsbc = hsbc.drop(['id'],axis=1)
		#print(hsbc)

		hsbc.Date = hsbc.Date.apply(lambda x: (datetime.strptime(x,'%Y-%m-%d').strftime("%d %b %y")))
		hsbc['RealMACD'] = TA2.MACD(hsbc,12,26)['MACD_12_26']

		conn.close()

		#shift = 90
		dji = TA2.MACD(dji,12,26).tail(depth)#['MACD_12_26']
		dji = TA2.STO(dji,10,10,3)
		ftse = TA2.MACD(ftse,12,26).tail(depth)#['MACD_12_26']
		ftse = TA2.STO(ftse,10,10,3)
		hsbc = hsbc.tail(depth)

		macd=ftse.merge(dji,on='Date',how='left',copy=False).\
			drop(['Open_x','Open_y','High_x','High_y','Low_x','Low_y','MACDsign_12_26_x',
			  'MACDsign_12_26_y','MACDdiff_12_26_x','MACDdiff_12_26_y','Volume_x','Volume_y',
			  'SO%d10_x','SO%d10_y'],axis=1)

		macd = macd.merge(hsbc,on='Date',how='left',copy=False)#.dropna()
		macd.columns = ['Date','FTSE','FTSE_MACD','FTSE_K','DJI','DJI_MACD','DJI_K','R72','R72_re_MACD']  #,'R72_im_MACD','R72_im']
		#macd = macd.dropna().drop_duplicates(subset=['Date'])

		min_max_scaler = preprocessing.MinMaxScaler()

		coef_x, coef_y = 0.76764361, 0.42319705

		for c in macd.columns:
			macd[c] = min_max_scaler.fit_transform(macd[c].values.reshape(-1, 1)) if c != 'Date' else macd[c]

			macd['R72_im_MACD'] = macd.DJI_MACD*coef_x+macd.FTSE_MACD*coef_y
			macd.R72_im_MACD = min_max_scaler.fit_transform(macd.R72_im_MACD.values.reshape(-1, 1))
			macd['R72_im'] = macd.DJI*coef_x+macd.FTSE*coef_y
			macd.R72_im = min_max_scaler.fit_transform(macd.R72_im.values.reshape(-1, 1))
			macd['R72_im_K'] = macd.DJI_K*coef_x+macd.FTSE_K*coef_y
			macd.R72_im_MACD = min_max_scaler.fit_transform(macd.R72_im_MACD.values.reshape(-1, 1))

			macd = macd.tail(depth) ##################################### cut the DF 

			# https://mdipierro.github.io/Publications/2011-web2py-for-Scientific-Applications.pdf
			# https://www.quora.com/Is-there-a-way-to-use-Plotly-with-web2py

		plot = {}
		plot['macd'] = go.Figure({
			'data': [
				{'y': macd.DJI_MACD.values.tolist(), 'type': 'scatter', 'name': 'DJI', 'x': macd.Date},
				{'y': macd.FTSE_MACD.values.tolist(), 'type': 'scatter', 'name': 'FTSE', 'x': macd.Date},
				{'y': macd.R72_im_MACD.values.tolist(), 'type': 'scatter', 'name': 'R72_im', 'x': macd.Date},
				{'y': macd.R72_re_MACD.values.tolist(), 'type': 'scatter', 'name': 'R72_re', 'x': macd.Date},
					],
			'layout': go.Layout(xaxis=go.XAxis(title='Date'), 
			yaxis=go.YAxis(title='MACD for main Indices'))
			})#, include_plotlyjs=False, output_type='div')

		plot['sto'] = go.Figure({
			'data': [
			{'y': macd.DJI_K.values.tolist(), 'type': 'scatter', 'name': 'DJI', 'x': macd.Date},
			{'y': macd.FTSE_K.values.tolist(), 'type': 'scatter', 'name': 'FTSE', 'x': macd.Date},
			{'y': macd.R72_im_K.values.tolist(), 'type': 'scatter', 'name': 'HSBC im', 'x': macd.Date},
			#{'y': macd.R72_re_K.values.tolist(), 'type': 'scatter', 'name': 'R72_re'},
				],
			'layout': go.Layout(xaxis=go.XAxis(title='Date'), 
			yaxis=go.YAxis(title='STO for main Indices'))
			})#, include_plotlyjs=False, output_type='div')

		plot['norm'] = go.Figure({
			'data': [
			{'y': macd.DJI.tolist(), 'type': 'scatter', 'name': 'DJI', 'x': macd.Date},
			{'y': macd.FTSE.tolist(), 'type': 'scatter', 'name': 'FTSE', 'x': macd.Date},
			{'y': macd.R72_im.tolist(), 'type': 'scatter', 'name': 'HSBC im', 'x': macd.Date},
			{'y': macd.R72.tolist(), 'type': 'scatter', 'name': 'real HSBC', 'x': macd.Date},
				],
			'layout': go.Layout(xaxis=go.XAxis(title='Date'), 
			yaxis=go.YAxis(title='Normilised values for main Indices'))
			})#, include_plotlyjs=False, output_type='div')

		plot['r72'] = go.Figure({
			'data': [
			{'y': hsbc.Close.tolist(), 'type': 'scatter', 'name': 'R72_re', 'x': hsbc.Date},
				 ],
			'layout': go.Layout(xaxis=go.XAxis(title='Date'), 
			yaxis=go.YAxis(title='Real R72'))
			})#, include_plotlyjs=False, output_type='div')

		return render_template('plot.html', fig1=pio.to_html(plot['macd']), fig2=pio.to_html(plot['sto']),
			fig3=pio.to_html(plot['norm']), fig4=pio.to_html(plot['r72']))


def yahoo2(sym='^DJI', freq='1d', period=15, offset=1):
	import pandas as pd
	"""
	@return dataframe for symbol
	@param period monitoring period in DAYS
	@param freq frequencies fo data [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
	@param offset timezone difference to UTC
	@url 'https://query1.finance.yahoo.com/v8/finance/chart/{0}?symbol={0}'
	'&period1={1}&period2={2}&interval={3}&'
	'includePrePost=true&events=div%7Csplit%7Cearn&lang=en-US&'
	'region=US&crumb=t5QZMhgytYZ&corsDomain=finance.yahoo.com'
	1 - starting time UNIX UTC
	2 - ending time UNIX UTC
	3 - period as above
	"""
	end = int(time.time())
	print(end, period) 
	start = int(end-3600*24*period)
	url = ('https://query1.finance.yahoo.com/v8/finance/chart/{0}?symbol={0}'
		'&period1={1}&period2={2}&interval={3}&'
		'includePrePost=true&events=div%7Csplit%7Cearn&lang=en-US&'
		'region=UK&crumb=t5QZMhgytYZ&corsDomain=finance.yahoo.com').format(sym, start, end, freq)
	#print(url)
	r = pd.read_json(url).chart.result
	df = pd.DataFrame({'Date':r[0]['timestamp'],
					   'Close':r[0]['indicators']['quote'][0]['close'],
					   'Open':r[0]['indicators']['quote'][0]['open'],
					   'High':r[0]['indicators']['quote'][0]['high'],
					   'Low':r[0]['indicators']['quote'][0]['low'],
					   'Volume':r[0]['indicators']['quote'][0]['volume']})#.dropna(subset=['Close'])
	df.Date = df.Date.apply(lambda x: pd.to_datetime(int(x)+3600*offset, unit='s').strftime('%d %b %y %H:%M'))
	df.Close = df.Close.apply(lambda x: round(x,2))
	df.Open = df.Open.apply(lambda x: round(x,2))
	df.High = df.High.apply(lambda x: round(x,2))
	df.Low = df.Low.apply(lambda x: round(x,2) if x>0 else None)
	#df.Low = df.Low.apply(lambda x: min(df.Close, df.Open) if x==0 else round(x,2))
	df.Volume = df.Volume.apply(lambda x: round(x,2))
	return df.dropna(subset=['Close','Low'])


def extremum(data):
	a1,a2,a3 = data
	if float(a1) < float(a2) and float(a2) > float(a3):
		return 'top'
	elif float(a1) > float(a2) and float(a2) < float(a3):
		return 'bott'
	elif float(a1) > float(a2) and float(a2) > float(a3):
		return 'down'
	elif float(a1) < float(a2) and float(a2) < float(a3):
		return 'up'
	else:
		return '--'


def fund(sym):
	''' get fundamental indo from yahoo '''
	url = 'https://query1.finance.yahoo.com/v7/finance/quote?symbols='+sym
	r = pd.read_json(url).quoteResponse.result[0]
	#for k,v in zip(r.keys(),r.values()):
	#	print(k, v)
	'''
	If earnings in the first half of the year, represented by the most recent two quarters, are trending lower, 
	the P/E ratio will be higher than 20x. This tells analysts that the stock may actually be overvalued at the 
	current price given its declining level of earnings.
	'''
	return {'earningDate': datetime.fromtimestamp(r['earningsTimestamp']).strftime('%b %d'), 
			'trailingPE': round(r['trailingPE'],2),
			'fiftyDayAverageChangePercent': round(r['fiftyDayAverageChangePercent'],2),
			'epsTrailingTwelveMonths': r['epsTrailingTwelveMonths'],
			'epsForward': r['epsForward'],
			'forwardPE': round(r['forwardPE'],3),
			'regularMarketPreviousClose': r['regularMarketPreviousClose'],
			'regularMarketPrice': r['regularMarketPrice'],
			'priceHint': r['priceHint'],
			'regularMarketOpen': r['regularMarketOpen'],
			'regularMarketDayHigh': r['regularMarketDayHigh'],
			'regularMarketDayLow': r['regularMarketDayLow'],
			'regularMarketChangePercent': round(r['regularMarketChangePercent'],2),
			'regularMarketVolume': r['regularMarketVolume'],
			'averageDailyVolume10Day': r['averageDailyVolume10Day'],
			'shortName': r['shortName'],
			'symbol': r['symbol']}


def prescan(lst):
	import app.TA2 as TA2
	''' define the best stocks for trending basing on MACD '''
	selected = {}
	# scan daily charts
	for l in lst:
		l = l[0]
		print('scanning {}...'.format(l))
		try:
			df = yahoo2(l,'1d',90)
			#print(df.tail())
		except:
			print('Error')
			continue
		if len(df):
			df['macd'] = TA2.MACD(df,12,26)['MACD_12_26']
			macd = TA2.MACD(df,12,26).tail(3)['MACD_12_26'].values
			#print(macd,macd[1])
			M = extremum(macd)
			print(M)
			if (M=='bott' and macd[1]<0):
				try:
					f = fund(l) # fundamental data
					flash = ('{} added to the shortlist; 50-days change is {}; earning date is {}'\
					  .format(f['shortName'],f['fiftyDayAverageChangePercent'],f['earningDate']))
					# TODO: add 30-min initial data
				except:
					pass
				selected[l] = {'macd':M}
			else:
				print(M)
	#with open('prescan.json', 'w') as outfile:
	#	json.dump(selected, outfile)
	return selected


def hsbc_morningstar(fund='F00000UOBO'):
	'''
	return date, price and change for fund
	'''
	import re, urllib
	url = 'http://www.morningstar.co.uk/uk/funds/snapshot/snapshot.aspx?id='+fund
	page = urllib.request.urlopen(url).read().decode('utf-8')
	m = re.search(r'NAV<span class="heading"><br />(\d{2}/\d{2}/\d{4})',page)
	resp = [m.group(1)]
	m = re.search(r'GBP\W*(\d{1}\.\d{2})',page)
	resp.append(m.group(1))
	m = re.search(r'Day Change</td><td class="line">\W*</td><td class="line text">(\W*\w*\d+\.\d+%)',page)
	resp.append(m.group(1))
	return resp

def mMon(sym, freq = '15m', period = 1):
	''' monitor MACD direction changing, hist for historical period '''
	df = yahoo2(sym, freq, period)
	macd = TA2.MACD(df,12,26).dropna(subset=['Close']).tail(3)['MACD_12_26'].values
	M = extremum(macd)
	return M



appbuilder.add_api(reportApi)
appbuilder.add_api(monthreportApi)