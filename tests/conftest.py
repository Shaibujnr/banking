from datetime import datetime
import pytest
from uuid import UUID, uuid4
from banking.account import (
    BankAccount, Transaction, BankAccount_INT,
    BankAccount_COVID19, BankAccount_COVID19_Company,
)
from banking.application import Application
from banking.ledger import Ledger


@pytest.fixture
def foreign_account() -> BankAccount_INT:
    account = BankAccount_INT.open(0)
    assert isinstance(account, BankAccount)
    assert isinstance(account, BankAccount_INT)
    assert isinstance(account.account_id, UUID)
    assert account.MINIMUM_ACCOUNT_BALANCE == 0
    return account

@pytest.fixture
def covid_account() -> BankAccount_COVID19:
    account = BankAccount_COVID19.open(0)
    assert isinstance(account, BankAccount)
    assert isinstance(account, BankAccount_COVID19) 
    assert isinstance(account.account_id, UUID)
    assert account.MINIMUM_ACCOUNT_BALANCE == 0
    assert account.MAX_DAILY_WITHDRAWAL == 1000
    #todo assert date?
    return account

@pytest.fixture
def company_account() -> BankAccount_COVID19_Company:
    account = BankAccount_COVID19_Company.open(5000)
    assert isinstance(account, BankAccount)
    assert isinstance(account, BankAccount_COVID19_Company)
    assert isinstance(account.account_id, UUID)
    assert account.MINIMUM_ACCOUNT_BALANCE == 5000
    assert account.MAX_DAILY_WITHDRAWAL == 1000
    #todo assert date?
    return account

@pytest.fixture
def app() -> Application:
    app = Application("test_ledger.p")
    assert isinstance(app.ledger, Ledger)
    app.start()
    return app