from . import db
from .models import *
from app import app
from datetime import date, timedelta
from flask_appbuilder.api import BaseApi, expose
from . import appbuilder
from flask_appbuilder.security.decorators import * #protect

import pandas as pd  # TODO load only neccesary libs
import time 		 # TODO load only neccesary libs
#from flask import flash

#@app.route('/info/showAll')
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
		'depo':depo, 'pFunds':pFunds, 'pShares':pShares, 'usd':usd, 'eur':eur, 'uah':uah, 'allGBP':allGBP,
		'allTogether': allTogether}


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
		diff = (pd.to_datetime('today') - pd.to_datetime(date)).days
		tax = df[0]['amount']*current*tax*0.01/365*diff
		sell = df[0]['amount']*current - tax
		gain = (int(sell-buy))
	else:
		gain=0
	return int(sell), gain


def cur(sym):
	''' read current quote from yahoo '''
	url = 'https://query1.finance.yahoo.com/v7/finance/quote?symbols='+sym
	#print(url)
	r = pd.read_json(url).quoteResponse.result[0]
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
	@expose('/info/monthly')
	@protect(allow_browser_login=True)
	def monthReport(self):

		from flask import Flask, render_template
		import pandas as pd
		import plotly.express as px
		import plotly
		from datetime import datetime
		from sqlalchemy import create_engine

		import plotly.io as pio
		import json


		engine = create_engine('sqlite:///004.sqlite')
		conn = engine.connect()


		session = db.session()

		acc = ['"36ca6c050017fb0411f0429072eb94f9"','"bf57f831079e04fdfffaaa77b5c6c50b"',
			   '"6cdb149b59eb612e1093e57710e2292a"','"4f514a136423e51d60d91de4215a6263"']
		expences = dict()
		today = datetime.today()
		df = incomes = pd.DataFrame()
		dates = pd.date_range(end='2021-01-31', periods=16, freq='1M').strftime("%Y-%m-%d").values

		for i in range(len(dates)-1):
			start = dates[i]
			end = dates[i+1]

			to_acc = conn.execute('select guid, name from accounts where \
				(parent_guid = "89ab14f49063d6f189955700f8fa75f7" \
				or guid in ("5bd720ffe83fd9592488a9e10c43a605",\
				"c6008ebaab83653b94284597ad844ff2","281a489ce89414170f2c215f451f8b78")) \
				and hidden=0')

			cons = conn.execute("select a.name, sum(s.value_num*826/c.cusip)/c.fraction s from transactions t \
				left join splits s on t.guid = s.tx_guid inner \
				join accounts a on a.guid = s.account_guid inner join commodities c \
				on c.guid = t.currency_guid \
				where t.post_date between '{}' and '{}' \
				and s.account_guid in ({}) \
				and s.value_num > 0 \
				and t.description not in ('None','Transfer','Credit') \
				group by s.account_guid".format(start, end, ','.join(["'"+a[0]+"'" for a in to_acc])))

			cons = [{column: value for column, value in rowproxy.items()} for rowproxy in cons]

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

			# expencies report
			df = df.append(pd.DataFrame(data = {'date':[str(end)[:10] for _ in range(len(cons))],
				'type':[a['name'] for a in cons],
				'amount':[a['s'] for a in cons]}), ignore_index=True)
			# incomes
			incomes = incomes.append(pd.DataFrame(data = {'date':[str(end)[:10] for _ in range(len(inc))],
				'type':[a['name'] for a in inc],
				'amount':[a['s'] for a in inc]}), ignore_index=True)

		# plotting
		
		fig1 = pio.to_html(px.bar(df, x="date", y="amount", color='type'))#.show(renderer='iframe')
		#fig1.update_layout(yaxis_type="log")
		#fig1.show()
		#graphJSON = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
		#print(graphJSON)

		fig2 = pio.to_html(px.bar(incomes, x="date", y="amount", color='type'))#.show(renderer='iframe')
		#fig2.update_layout(yaxis_type="log")
		#fig2.show()
		#div = offplot.plot(fig, show_link=False, output_type="div", include_plotlyjs=False)

		return render_template('plot.html', fig1=fig1, fig2=fig2)

		# the same for 2020
		'''
		start = '2020-01-01'
		end = '2020-12-31'
		s = conn.execute("select sum(s.value_num)/100 \
		from transactions t left join splits s on t.guid = s.tx_guid inner \
		join accounts a on a.guid = s.account_guid inner join commodities c \
		on c.guid = t.currency_guid \
		where t.post_date between '{}' and '{}' \
		and s.account_guid in ({}) \
		and s.value_num < 0 \
		and t.description not in ('None','Transfer','Credit') \
		order by t.post_date".format(start, end, ','.join(acc)))

		
		rest = int(gnucash()['allTogether']) + int(s[0][0])
		avg = 2000
		corr2020 = (112+50+28+24+21+37+75/3+33+300)*12
		corr2019 = 0
		rent2020 = 975*2
		# add rest
		rest -= corr2020
		rest -= corr2019
		rest -= rent2020
		mn = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
		restYr = 2021+int(rest/(avg*12))
		restMn = (rest/(avg*12) - int(rest/(avg*12)))*12
		u = 'saving enough until {} {} (spenging {} per month) incl. {} ({} per month) correction for 2020 for utilities, food and education,\
			 and {} renting for Nov and Dec 2020'\
			.format(mn[int(restMn)], restYr, avg, int(corr2020), int(corr2020/12), rent2020)
		return dict(#ex=expences, \
			yr2020='currently {}, corrected {} will be spent in 2020'.format(int(s[0][0]), int(s[0][0])-corr2020-rent2020), \
			willRest='{} will rest by the end of 2020'.format(rest), \
			upTo = u,
			img1 = XML(pio.to_html(fig1)),
			img2 = XML(pio.to_html(fig2))
			)
		'''



appbuilder.add_api(reportApi)
appbuilder.add_api(monthreportApi)