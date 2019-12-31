from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from flask_appbuilder.models.sqla.filters import *
from . import appbuilder, db
from flask_appbuilder.views import *
from .models import *

#from app import app
#from flask_appbuilder import expose, has_access, permission_name

class commoditiesView(ModelView):
    datamodel = SQLAInterface(commodities)
    list_columns = [
        'guid',
        'namespace',
        'mnemonic',
        'fullname',
        'cusip',
        'fraction',
        'quote_flag',
        'quote_source',
        'quote_tz',
    ]

class accountsView(ModelView):
    datamodel = SQLAInterface(accounts)
    list_columns = [
    'name',
    'account_type',
    'description'
    ]
    related_view = [commoditiesView]
    base_filters = [['hidden',FilterEqual,0],
                    ['account_type',FilterNotEqual,'ROOT']]

class splitsView(ModelView):
    datamodel = SQLAInterface(splits)
    list_columns = [
    'memo',
    'action',
    'value_num',
    'value_denom',
    'transactions',
    ]
    related_view = [accounts]

class transactionsView(ModelView):
    datamodel = SQLAInterface(transactions)
    list_columns = [    
    'post_date',
    'description',
    ]
    related_views = [splitsView]
    base_order = ('post_date','desc')


class R72View(ModelView):
    datamodel = SQLAInterface(R72)
    list_columns = ['Date','Close']

class fundsView(ModelView):
    datamodel = SQLAInterface(funds)
    list_columns = [
    'name',
    'amount',
    'tax',
    'price',
    'request',
    'gain',
    'date',
    'scan',
    'comms',
    'isActive']

class stocksView(ModelView):
    datamodel = SQLAInterface(stocks)
    list_columns = [
    'symbol',
    'amount',
    'price',
    'date',
    'gain',
    'tax',
    'scan',
    'comms',
    'isActive',
    'fee'
    ]

class monitorView(ModelView):
    datamodel = SQLAInterface(monitor)


from .forms import *
import secrets


class addTransView(SimpleFormView):
    form = addTransaction
    form_title = "Payment form"

    def form_get(self, form):
        pass
        #form.field1.data = "This was prefilled"

    def form_post(self, form):
        # post process form
        s = db.session()
        t = secrets.token_hex(16) # transaction guid = splits tx_guid
        trans = transactions(guid=t, currency_guid=form.currency.data, post_date=form.date.data,
            enter_date=form.date.data, description=form.desc.data)
        split_in = splits(guid=secrets.token_hex(16), tx_guid=t, account_guid=form.to_acc.data, 
            value_num = int(form.amount.data*100), value_denom = 100, quantity_num=int(form.amount.data*100), 
            quantity_denom=100, memo='test',action='auto', reconcile_state='n')
        split_out = splits(guid=secrets.token_hex(16), tx_guid=t, account_guid=form.f_acc.data, 
            value_num = int(form.amount.data*-100), value_denom = 100, quantity_num=int(form.amount.data*-100), 
            quantity_denom=100, memo='test',action='auto', reconcile_state='n')
        s.add(trans)
        s.add(split_in)
        s.add(split_out)
        s.commit()
        flash('{}->{}: {} {} on {}'.
            format(form.f_acc.data, form.to_acc.data, form.amount.data, form.currency.data, form.date.data), "info")


class addTransferView(addTransView):
    form = addTransfer
    form_title = 'Transfer form'


"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )

appbuilder.add_view(
    transactionsView,
    "My transactionsView",
    icon="fa-folder-open-o",
    category="My Category",
    category_icon='fa-envelope'
)

appbuilder.add_view(
    splitsView,
    "My splitsView",
    icon="fa-folder-open-o",
    category="My Category",
    category_icon='fa-envelope'
)

appbuilder.add_view(
    accountsView,
    "My accountsView",
    icon="fa-folder-open-o",
    category="My Category",
    category_icon='fa-envelope'
)

appbuilder.add_view(
    commoditiesView,
    "My commoditiesView",
    icon="fa-folder-open-o",
    category="My Category",
    category_icon='fa-envelope'
)


appbuilder.add_view(
    addTransView,
    "add transaction",
    icon="fa-group",
    label="add transaction",
    category="Transactions",
    category_icon="fa-cogs",
)

appbuilder.add_view(
    addTransferView,
    "add transfer",
    icon="fa-group",
    label="add transfer",
    category="Transactions",
    category_icon="fa-cogs",
)

appbuilder.add_view(
    R72View,
    "R72",
    icon="fa-group",
    label="R72",
    category="Trading",
    category_icon="fa-cogs",
)

appbuilder.add_view(
    fundsView,
    "funds",
    icon="fa-group",
    label="funds",
    category="Trading",
    category_icon="fa-cogs",
)

appbuilder.add_view(
    stocksView,
    "stocks",
    icon="fa-group",
    label="stocks",
    category="Trading",
    category_icon="fa-cogs",
)

appbuilder.add_view(
    monitorView,
    "monitor",
    icon="fa-group",
    label="monitor",
    category="Trading",
    category_icon="fa-cogs",
)

############################

appbuilder.add_link(
    "showAll",
    href="/api/v1/reportapi/info/showAll",
    icon="fa-group",
    label="showAll",
    category="Info",
    category_icon="fa-cogs",
)

appbuilder.add_link(
    "showRest",
    href="/info/showRest",
    icon="fa-group",
    label="showRest",
    category="Info",
    category_icon="fa-cogs",
)

#db.create_all()
