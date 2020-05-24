from datetime import datetime, date, timedelta
from typing import Optional
from uuid import uuid4
import pytest
from tests.conftest import company_account, covid_account, foreign_account
from banking.account import (
    BankAccount, Transaction, BankAccount_INT,
    BankAccount_COVID19, BankAccount_COVID19_Company,
)
from banking.error import (
    ATMWithdrawalNotAllowedError, ClosingCompanyAccountError, InsufficientFundError, AccountClosedError,
    DailyWithdrawalAmountLimitExceededError,
)


def test_transaction():
    transaction_list = []
    transaction_list.append(
        Transaction.create(
            uuid4(),
            Transaction.TransactionType.CREDIT,
            400
        )
    )
    transaction_list.append(
        Transaction.create(
            uuid4(),
            Transaction.TransactionType.DEBIT,
            200
        )
    )
    transaction_list.append(
        Transaction.create(
            uuid4(),
            Transaction.TransactionType.CREDIT,
            300
        )
    )
    transaction_list.append(
        Transaction.create(
            uuid4(),
            Transaction.TransactionType.DEBIT,
            600
        )
    )
    assert sum(transaction_list) == (400 - 200 + 300 - 600)

def test_deposit_foreign_account_ok(foreign_account: BankAccount_INT):
    deposit_transaction: Transaction = foreign_account.deposit(400)
    assert isinstance(deposit_transaction, Transaction)
    assert deposit_transaction.transaction_type == Transaction.TransactionType.CREDIT
    assert deposit_transaction.amount == 400
    assert deposit_transaction.account_id == foreign_account.account_id
    #todo assert deposit_transaction.date

def test_withdraw_foreign_account_ok(foreign_account: BankAccount_INT):
    mock_current_balance = 4000
    amount_to_withdraw = 300
    today= datetime.now().date()
    total_amount_withdrawn_today = 5000
    withdraw_transaction: Transaction = foreign_account.withdraw(
        amount_to_withdraw,
        mock_current_balance,
        True,
        today,
        total_amount_withdrawn_today
    )
    assert isinstance(withdraw_transaction, Transaction)
    assert withdraw_transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert withdraw_transaction.account_id == foreign_account.account_id
    assert withdraw_transaction.amount == 300

def test_withdraw_foreign_account_fail_insufficient_funds(foreign_account: BankAccount_INT):
    mock_current_balance = 200
    amount_to_withdraw = 600
    today= datetime.now().date()
    total_amount_withdrawn_today = 5000
    with pytest.raises(InsufficientFundError):
        foreign_account.withdraw(
            amount_to_withdraw,
            mock_current_balance,
            True,
            today,
            total_amount_withdrawn_today
        )

def test_close_empty_account_ok(foreign_account: BankAccount_INT):
    transaction: Optional[Transaction] = foreign_account.close(0)
    assert transaction is None

def test_close_non_empty_account_ok(foreign_account: BankAccount_INT):
    transaction: Optional[Transaction] = foreign_account.close(400)
    assert transaction is not None
    assert transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert transaction.account_id == foreign_account.account_id
    assert transaction.amount == 400

def test_withdraw_more_than_max_before_restriction_date_ok(covid_account: BankAccount_COVID19):
    threshold_date: date = covid_account.THRESHOLD_DATE
    threshold_datetime: datetime= datetime(
        threshold_date.year, threshold_date.month, threshold_date.day
    )
    day_before_restriction_date: date = (threshold_datetime - timedelta(days=1)).date()
    max_amount = covid_account.MAX_DAILY_WITHDRAWAL
    mock_current_balance = max_amount * 3
    amount_to_withdraw = max_amount * 2
    total_amount_withdrawn = 5000
    transaction = covid_account.withdraw(
        amount_to_withdraw,
        mock_current_balance,
        True,
        day_before_restriction_date,
        total_amount_withdrawn
    )
    assert transaction.transaction_type == Transaction.TransactionType.DEBIT
    assert transaction.amount == covid_account.MAX_DAILY_WITHDRAWAL * 2
    assert transaction.account_id == covid_account.account_id

def test_atm_withdraw_after_restriction_date_fail(covid_account: BankAccount_COVID19):
    threshold_date: date = covid_account.THRESHOLD_DATE
    max_amount = covid_account.MAX_DAILY_WITHDRAWAL
    mock_current_balance = max_amount * 3
    amount_to_withdraw = max_amount
    total_amount_withdrawn = 0
    with pytest.raises(ATMWithdrawalNotAllowedError):
        covid_account.withdraw(
            amount_to_withdraw,
            mock_current_balance,
            True,
            threshold_date,
            total_amount_withdrawn
        )

def test_withdraw_more_than_max_on_restriction_date_fail(covid_account: BankAccount_COVID19):
    threshold_date: date = covid_account.THRESHOLD_DATE
    max_amount = covid_account.MAX_DAILY_WITHDRAWAL
    mock_current_balance = max_amount * 3
    amount_to_withdraw = max_amount
    total_amount_withdrawn = 1
    with pytest.raises(DailyWithdrawalAmountLimitExceededError):
        covid_account.withdraw(
            amount_to_withdraw,
            mock_current_balance,
            False,
            threshold_date,
            total_amount_withdrawn
        )

def test_close_company_account_fail(company_account: BankAccount_COVID19_Company):
    with pytest.raises(ClosingCompanyAccountError):
        company_account.close(400)

def test_company_withdraw_from_minimum_balance(company_account: BankAccount_COVID19_Company):
    with pytest.raises(InsufficientFundError):
        company_account.withdraw(
            2001,
            7000,
            False,
            company_account.THRESHOLD_DATE,
            0
        )
