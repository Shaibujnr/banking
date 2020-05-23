from datetime import datetime, date, timedelta
from typing import Optional
import pytest
from tests.conftest import company_account, covid_account, foreign_account
from banking.account import (
    BankAccount, Transaction, BankAccount_INT,
    BankAccount_COVID19, BankAccount_COVID19_Company,
)
from banking.error import (
    ClosingCompanyAccountError, InsufficientFundError, AccountClosedError,
    DailyWithdrawalAmountLimitExceededError,
)

def test_deposit_foreign_account_ok(foreign_account: BankAccount_INT):
    deposit_transaction: Transaction = foreign_account.deposit(400)
    assert isinstance(deposit_transaction, Transaction)
    assert deposit_transaction.transaction_type == Transaction.TransactionType.CREDIT
    assert deposit_transaction.amount == 400
    assert deposit_transaction.account_id == foreign_account.account_id
    #todo assert deposit_transaction.date
    assert foreign_account.balance == 400

def test_withdraw_foreign_account_ok(foreign_account: BankAccount_INT):
    foreign_account.deposit(4000)
    withdraw_transaction: Transaction = foreign_account.withdraw(300)
    assert isinstance(withdraw_transaction, Transaction)
    assert withdraw_transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert withdraw_transaction.account_id == foreign_account.account_id
    assert withdraw_transaction.amount == 300
    assert foreign_account.balance == (4000 - 300)

def test_withdraw_foreign_account_fail_insufficient_funds(foreign_account: BankAccount_INT):
    foreign_account.deposit(300)
    with pytest.raises(InsufficientFundError):
        foreign_account.withdraw(300.01)

def test_close_empty_account_ok(foreign_account: BankAccount_INT):
    assert foreign_account.is_empty
    assert not foreign_account.is_closed
    transaction: Optional[Transaction] = foreign_account.close()
    assert transaction is None
    assert foreign_account.is_closed

def test_close_non_empty_account_ok(foreign_account: BankAccount_INT):
    foreign_account.deposit(400)
    assert not foreign_account.is_empty
    transaction: Optional[Transaction] = foreign_account.close()
    assert transaction is not None
    assert foreign_account.is_closed
    assert transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert transaction.account_id == foreign_account.account_id
    assert transaction.amount == 400

def test_withdraw_more_than_max_before_restriction_date_ok(covid_account: BankAccount_COVID19):
    covid_account.deposit(covid_account.MAX_DAILY_WITHDRAWAL * 3)
    assert covid_account.balance == (covid_account.MAX_DAILY_WITHDRAWAL * 3)
    threshold_date: date = covid_account.THRESHOLD_DATE
    threshold_datetime: datetime= datetime(
        threshold_date.year, threshold_date.month, threshold_date.day
    )
    day_before_restriction_date: date = (threshold_datetime - timedelta(days=1)).date()
    transaction = covid_account.withdraw(
        covid_account.MAX_DAILY_WITHDRAWAL *2,
        covid_account.MAX_DAILY_WITHDRAWAL,
        day_before_restriction_date
    )
    assert transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert transaction.amount == covid_account.MAX_DAILY_WITHDRAWAL * 2
    assert transaction.account_id == covid_account.account_id
    assert covid_account.balance == covid_account.MAX_DAILY_WITHDRAWAL

def test_withdraw_more_than_max_on_restriction_date_fail(covid_account: BankAccount_COVID19):
    covid_account.deposit(covid_account.MAX_DAILY_WITHDRAWAL * 3)
    assert covid_account.balance == (covid_account.MAX_DAILY_WITHDRAWAL * 3)
    threshold_date: date = covid_account.THRESHOLD_DATE
    with pytest.raises(DailyWithdrawalAmountLimitExceededError):
        covid_account.withdraw(
            covid_account.MAX_DAILY_WITHDRAWAL *2,
            covid_account.MAX_DAILY_WITHDRAWAL,
            threshold_date
        )

def test_close_company_account_fail(company_account: BankAccount_COVID19_Company):
    with pytest.raises(ClosingCompanyAccountError):
        company_account.close()

def test_company_withdraw_from_minimum_balance(company_account: BankAccount_COVID19_Company):
    company_account.deposit(7000)
    assert company_account.balance == 7000
    with pytest.raises(InsufficientFundError):
        company_account.withdraw(
            ((7000 - company_account.MINIMUM_ACCOUNT_BALANCE)+0.1),
            0,
            company_account.THRESHOLD_DATE
        )