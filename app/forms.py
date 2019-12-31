from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_appbuilder.forms import DynamicForm
from wtforms import *
from wtforms.validators import DataRequired
from . import db
import logging
from .models import *
from datetime import datetime, time

s = db.session()

class addTransaction(DynamicForm):
	f_acc = SelectField('From', 
		choices = [(g.guid, g.name) for g in s.query(accounts).filter(accounts.placeholder==1).
		filter(accounts.account_type=='ASSET')])
	to_acc = SelectField('to', 
		choices = [(g.guid, g.name) for g in s.query(accounts).filter(accounts.placeholder==1).
		filter(accounts.account_type=='EXPENSE')])
	amount = FloatField('Amount')
	currency = SelectField('currency', 
		choices = [(g.guid, g.mnemonic) for g in s.query(commodities).
		filter(commodities.namespace=='CURRENCY').
		filter(accounts.account_type=='EXPENSE')])
	desc = StringField(default='ALDI')
	date = DateTimeField(default = datetime.now())


class addTransfer(addTransaction):
		to_acc = SelectField('to', 
		choices = [(g.guid, g.name) for g in s.query(accounts).filter(accounts.placeholder==1).
		filter(accounts.account_type=='ASSET')])
		desc = StringField(default='Transfer')


def from_acc(request,guid):
	pass
	#acc = s.query(accounts).get(guid)
	#form = addTransaction(request.POST, obj=acc)
	#form.f_acc.choices = [(g.guid, g.name) for g in s.query(accounts).all()]