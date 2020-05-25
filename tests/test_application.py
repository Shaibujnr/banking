from datetime import date, datetime, timedelta
from uuid import UUID

import pytest
from pytest_mock import MockFixture

from banking.account import BankAccount
from banking.application import Application
from banking.error import (
    AccountNotFoundError,
    ATMWithdrawalNotAllowedError,
    ClosingCompanyAccountError,
    DailyWithdrawalLimitError,
)


def test_change_current_date(app: Application):
    from banking.date_helper import get_todays_date

    assert get_todays_date() == datetime(2020, 4, 1).date()
    app.change_current_date(datetime(2018, 2, 23).date())
    assert get_todays_date() == datetime(2018, 2, 23).date()
    app.change_current_date(datetime(2020, 4, 1).date())


def test_open_account(app: Application):
    international_account_id = app.open_account("international")
    assert isinstance(international_account_id, UUID)
    covid_account_id = app.open_account("covid")
    assert isinstance(covid_account_id, UUID)
    company_account_id = app.open_account("company")
    assert isinstance(company_account_id, UUID)


def test_get_account_details(app: Application):
    account_id = app.open_account("international")
    account_details = app.get_account_details(account_id)
    assert isinstance(account_details, dict)
    assert account_details["balance"] == "0 PLN"


def test_deposit_into_account(app: Application):
    account_id = app.open_account("covid")
    assert app.ledger.get_account_balance(account_id) == 0
    app.deposit(account_id, 400)
    assert app.ledger.get_account_balance(account_id) == 400


def test_atm_withdrawal_from_covid_account_on_april_1_2020_fail(
    app: Application, mocker: MockFixture
):
    mock_todays_date = mocker.patch("banking.application.get_todays_date")
    mock_todays_date.return_value = datetime(2020, 4, 1).date()
    account_id = app.open_account("covid")
    app.deposit(account_id, 200)
    with pytest.raises(ATMWithdrawalNotAllowedError):
        app.withdraw(account_id, 10, True)
    assert app.ledger.get_account_balance(account_id) == 200


def test_atm_withdrawal_from_covid_account_before_april_1_2020_ok(app: Application):
    before = (datetime(2020, 4, 1) - timedelta(days=1)).date()
    app.change_current_date(before)
    account_id = app.open_account("covid")
    app.deposit(account_id, 200)
    app.withdraw(account_id, 10, True)
    assert app.ledger.get_account_balance(account_id) == (200 - 10)


def test_withdraw_more_than_max_from_covid_account_on_april_1_2020_fail(
    app: Application,
):
    app.change_current_date(datetime(2020, 4, 1).date())
    account_id = app.open_account("covid")
    app.deposit(account_id, 4000)
    assert app.ledger.get_account_balance(account_id) == 4000
    app.withdraw(account_id, 200, False)
    assert app.ledger.get_account_balance(account_id) == (4000 - 200)
    app.withdraw(account_id, 500, False)
    assert app.ledger.get_account_balance(account_id) == (4000 - 500 - 200)
    with pytest.raises(DailyWithdrawalLimitError):
        app.withdraw(account_id, 500, False)
        print(
            f"\n\namount withdrawn today is {app.ledger.get_total_withdrawn_amount_by_date(account_id, datetime(2020, 4, 1).date())}"
        )
    assert app.ledger.get_account_balance(account_id) == (4000 - 500 - 200)


def test_withdraw_more_than_max_from_covid_account_before_april_1_2020_ok(
    app: Application,
):
    before = (datetime(2020, 4, 1) - timedelta(days=1)).date()
    app.change_current_date(before)
    account_id = app.open_account("covid")
    app.deposit(account_id, 4000)
    assert app.ledger.get_account_balance(account_id) == 4000
    app.withdraw(account_id, 200, False)
    assert app.ledger.get_account_balance(account_id) == (4000 - 200)
    app.withdraw(account_id, 500, False)
    assert app.ledger.get_account_balance(account_id) == (4000 - 500 - 200)
    app.withdraw(account_id, 500, False)
    current_balance = app.ledger.get_account_balance(account_id)
    assert current_balance == (4000 - 500 - 200 - 500)
    account = app.ledger.get_account(account_id)
    assert account.amount_withdrawn_today > 1000


def test_close_company_account_fail(app: Application):
    account_id = app.open_account("company")
    with pytest.raises(ClosingCompanyAccountError):
        app.close_account(account_id)


def test_close_account_ok(app: Application):
    account_id = app.open_account("international")
    assert isinstance(app.ledger.get_account(account_id), BankAccount)
    transaction_id = app.close_account(account_id)
    assert transaction_id is None
    with pytest.raises(AccountNotFoundError):
        app.ledger.get_account(account_id)
