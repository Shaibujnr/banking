from collections import OrderedDict
from datetime import datetime
from uuid import uuid4
from banking.account import BankAccount, BankAccount_INT, Transaction
from banking.ledger import Ledger

#todo write better ledger tests
#todo check type ignores

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

def test_get_account_balance():
    ledger = Ledger("test_ledger.p")
    mock_account_id = uuid4()
    transaction1 = Transaction(
        mock_account_id,
        Transaction.TransactionType.CREDIT,
        400,
        datetime.now().date()
    )
    transaction2 = Transaction(
        mock_account_id,
        Transaction.TransactionType.CREDIT,
        37.99,
        datetime.now().date()
    )
    transaction3 = Transaction(
        mock_account_id,
        Transaction.TransactionType.DEBIT,
        23.47,
        datetime.now().date()
    )
    transaction4 = Transaction(
        mock_account_id,
        Transaction.TransactionType.DEBIT,
        350.26,
        datetime.now().date()
    )
    transaction5 = Transaction(
        mock_account_id,
        Transaction.TransactionType.CREDIT,
        600,
        datetime.now().date()
    )
    assert ledger.is_empty
    transactions = [transaction1, transaction2, transaction3, transaction4, transaction5]
    ledger.save(transactions) #type: ignore
    assert not ledger.is_empty
    current_balance = ledger.get_account_balance(mock_account_id)
    assert current_balance == ( 400 + 37.99 - 23.47 - 350.26 + 600)