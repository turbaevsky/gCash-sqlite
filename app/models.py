from flask_appbuilder import Model
from sqlalchemy import *
from flask_appbuilder.models.mixins import *
from sqlalchemy.orm import relationship


class commodities(Model):
	guid = Column(String, primary_key=True)
	namespace = Column(String())
	mnemonic = Column(String())
	fullname = Column(String())
	cusip = Column(String())
	fraction = Column(Integer())
	quote_flag = Column(Integer())
	quote_source = Column(String())
	quote_tz = Column(String())

	def __repr__(self):
		return '{}'.format(self.mnemonic)

class transactions(Model):
	guid = Column(String, primary_key=True)
	currency_guid = Column(String, ForeignKey('commodities.guid'))
	commodities = relationship('commodities')
	num = Column(Integer())
	post_date = Column(DateTime())
	enter_date = Column(DateTime())
	description = Column(String())
	#id = Column(Integer, primary_key=True)

	def __repr__(self):
		return '{}: {}'.format(self.post_date, self.description)

	def month_year(self):
		return datetime.datetime(self.post_date.year, self.post_date.month, 1)


class accounts(Model):
	guid = Column(String, primary_key=True)
	name = Column(String())
	account_type = Column(String())
	commodity_guid = Column(String, ForeignKey('commodities.guid'))
	commodities = relationship('commodities')
	commodity_scu = Column(Integer())
	non_std_scu = Column(Integer())
	parent_guid = Column(String())
	code = Column(String())
	description = Column(String())
	hidden = Column(Integer())
	placeholder = Column(Integer())
	#id = Column(Integer, primary_key=True)

	def __repr__(self):
		return '{}: {}'.format(self.name, self.account_type)


class splits(Model):
	guid = Column(String, primary_key=True)
	tx_guid = Column(String, ForeignKey('transactions.guid'))
	transactions = relationship('transactions')
	account_guid = Column(String, ForeignKey('accounts.guid'))
	accounts = relationship('accounts')
	memo = Column(String())
	action = Column(String())
	reconcile_state = Column(String())
	reconcile_date = Column(DateTime())
	value_num = Column(Integer())
	value_denom = Column(Integer())
	quantity_num = Column(Integer())
	quantity_denom = Column(Integer())
	lot_guid = Column(String())
	#id = Column(Integer, primary_key=True)

	def __repr__(self):
		return self.value_num/self.value_denom

	def value(self):
		return self.value_num/self.value_denom

class R72(Model):
	Close = Column(Float())
	Date = Column(Date())
	id = Column(Integer, primary_key=True)

class funds(Model):
	name = Column(String())
	amount = Column(Float())
	tax = Column(Float())
	price = Column(Float())
	request = Column(String())
	gain = Column(Float())
	date = Column(Date())
	scan = Column(FileColumn())
	comms = Column(String())
	isActive = Column(Boolean())
	id = Column(Integer, primary_key=True)

class monitor(Model):
	id = Column(Integer, primary_key=True)
	code = Column(String())

class stocks(Model):
	symbol = Column(String())
	amount = Column(Float())
	price = Column(Float())
	date = Column(Date())
	gain = Column(Float())
	tax = Column(Float())
	scan = Column(FileColumn())
	comms = Column(String())
	isActive = Column(Boolean())
	fee = Column(Float())
	id = Column(Integer, primary_key=True)
