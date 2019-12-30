from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
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

