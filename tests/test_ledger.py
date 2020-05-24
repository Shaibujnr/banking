from collections import OrderedDict
from banking.account import BankAccount, BankAccount_INT, Transaction
from banking.ledger import Ledger

#todo write better ledger tests

def test_ledger_save(foreign_account, covid_account, company_account):
    ledger = Ledger("test_ledger.p")
    assert ledger.is_empty
    ledger.save([foreign_account, covid_account, company_account])
    assert not ledger.is_empty
    assert len(ledger.store["accounts"]) == 3
    assert len(ledger.store["transactions"]) == 0

def test_ledger_load(foreign_account, covid_account, company_account):
    ledger = Ledger("test_ledger.p")
    assert ledger.is_empty
    ledger.save([foreign_account, covid_account, company_account])
    assert not ledger.is_empty
    ledger.store = {"accounts": OrderedDict(), "transactions": OrderedDict()}
    assert ledger.is_empty
    ledger.load()
    assert not ledger.is_empty


def test_get_account_balance(foreign_account: BankAccount_INT):
    ledger = Ledger("test_ledger.p")
    assert ledger.is_empty
    transactions = []
    transactions.append(
        foreign_account.deposit(4000)
    )
    ledger.save(transactions)
    assert not ledger.is_empty
    assert ledger.get_account_balance(foreign_account.account_id) == 4000