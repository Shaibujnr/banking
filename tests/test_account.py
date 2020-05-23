from typing import Optional
import pytest
from tests.conftest import foreign_account
from banking.account import (
    BankAccount, Transaction, BankAccount_INT,
    BankAccount_COVID19, BankAccount_COVID19_Company,
)
from banking.error import (
    InsufficientFundError, AccountClosedError,
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