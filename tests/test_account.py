from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import uuid4

import pytest
from pytest_mock import MockFixture

from banking.account import (
    BankAccount_COVID19,
    BankAccount_COVID19_Company,
    BankAccount_INT,
    Transaction,
)
from banking.error import (
    AccountError,
    ATMWithdrawalNotAllowedError,
    ClosingCompanyAccountError,
    DailyWithdrawalLimitError,
    InsufficientFundError,
)


def test_transactions():
    transaction_list: List[Transaction] = []
    transaction_list.append(
        Transaction.create(uuid4(), Transaction.TransactionType.CREDIT, 400)
    )
    transaction_list.append(
        Transaction.create(uuid4(), Transaction.TransactionType.DEBIT, 200)
    )
    transaction_list.append(
        Transaction.create(uuid4(), Transaction.TransactionType.CREDIT, 300)
    )
    transaction_list.append(
        Transaction.create(uuid4(), Transaction.TransactionType.DEBIT, 600)
    )
    assert transaction_list[0].amount == 400
    assert transaction_list[0].transaction_type == Transaction.TransactionType.CREDIT
    assert sum(transaction_list) == (400 - 200 + 300 - 600)


def test_deposit_foreign_account_ok(foreign_account: BankAccount_INT):
    deposit_transaction: Transaction = foreign_account.deposit(400)
    assert isinstance(deposit_transaction, Transaction)
    assert deposit_transaction.transaction_type == Transaction.TransactionType.CREDIT
    assert deposit_transaction.amount == 400
    assert deposit_transaction.account_id == foreign_account.account_id


def test_withdraw_foreign_account_ok(foreign_account: BankAccount_INT):
    foreign_account.balance = 4000
    foreign_account.amount_withdrawn_today = 5000
    withdraw_transaction: Transaction = foreign_account.withdraw(300, True)
    assert isinstance(withdraw_transaction, Transaction)
    assert withdraw_transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert withdraw_transaction.account_id == foreign_account.account_id
    assert withdraw_transaction.amount == 300


def test_withdraw_foreign_account_fail_insufficient_funds(
    foreign_account: BankAccount_INT,
):
    foreign_account.balance = 200
    foreign_account.amount_withdrawn_today = 5000
    with pytest.raises(InsufficientFundError):
        foreign_account.withdraw(600, True)


def test_close_empty_account_ok(foreign_account: BankAccount_INT):
    foreign_account.balance = 0
    foreign_account.amount_withdrawn_today = 0
    transaction: Optional[Transaction] = foreign_account.close()
    assert transaction is None


def test_close_non_empty_account_ok(foreign_account: BankAccount_INT):
    foreign_account.balance = 400
    foreign_account.amount_withdrawn_today = 0
    transaction: Optional[Transaction] = foreign_account.close()
    assert transaction is not None
    assert transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert transaction.account_id == foreign_account.account_id
    assert transaction.amount == 400


def test_close_covid_account_with_balance_more_than_daily_max_fail(
    covid_account: BankAccount_COVID19,
):
    covid_account.balance = covid_account.MAX_DAILY_WITHDRAWAL + 0.1
    covid_account.amount_withdrawn_today = 1
    with pytest.raises(DailyWithdrawalLimitError):
        transaction: Optional[Transaction] = covid_account.close()


def test_withdraw_more_than_max_before_restriction_date_ok(
    covid_account: BankAccount_COVID19, mocker: MockFixture
):
    restriction_date: date = covid_account.RESTRICTION_DATE
    restriction_datetime: datetime = datetime(
        restriction_date.year, restriction_date.month, restriction_date.day
    )
    day_before_restriction_date: date = (
        restriction_datetime - timedelta(days=1)
    ).date()
    mock_get_todays_date = mocker.patch("banking.account.get_todays_date")
    mock_get_todays_date.return_value = day_before_restriction_date

    max_amount = covid_account.MAX_DAILY_WITHDRAWAL
    covid_account.balance = max_amount * 3
    amount_to_withdraw = max_amount * 2
    covid_account.amount_withdrawn_today = 5000
    transaction = covid_account.withdraw(amount_to_withdraw, True)
    assert transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert transaction.amount == covid_account.MAX_DAILY_WITHDRAWAL * 2
    assert transaction.account_id == covid_account.account_id


def test_atm_withdraw_on_restriction_date_fail(
    covid_account: BankAccount_COVID19, mocker: MockFixture
):
    mock_get_todays_date = mocker.patch("banking.account.get_todays_date")
    mock_get_todays_date.return_value = covid_account.RESTRICTION_DATE
    max_amount = covid_account.MAX_DAILY_WITHDRAWAL
    covid_account.balance = max_amount * 3
    covid_account.amount_withdrawn_today = 0
    amount_to_withdraw = max_amount
    with pytest.raises(ATMWithdrawalNotAllowedError):
        covid_account.withdraw(amount_to_withdraw, True)


def test_withdraw_more_than_max_on_restriction_date_fail(
    covid_account: BankAccount_COVID19, mocker: MockFixture
):
    mock_get_todays_date = mocker.patch("banking.account.get_todays_date")
    mock_get_todays_date.return_value = covid_account.RESTRICTION_DATE
    max_amount = covid_account.MAX_DAILY_WITHDRAWAL
    covid_account.balance = max_amount * 3
    covid_account.amount_withdrawn_today = 1
    amount_to_withdraw = max_amount
    with pytest.raises(DailyWithdrawalLimitError):
        covid_account.withdraw(amount_to_withdraw, False)


def test_close_company_account_fail(company_account: BankAccount_COVID19_Company):
    with pytest.raises(ClosingCompanyAccountError):
        company_account.close()


def test_company_withdraw_from_minimum_balance(
    company_account: BankAccount_COVID19_Company,
):
    company_account.balance = 7000
    company_account.amount_withdrawn_today = 0
    with pytest.raises(InsufficientFundError):
        company_account.withdraw(2001, False)


def test_company_first_deposit_insufficient_fail(
    company_account: BankAccount_COVID19_Company,
):
    with pytest.raises(AccountError):
        company_account.deposit(4999)
