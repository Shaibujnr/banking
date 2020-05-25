from datetime import date, datetime
import enum
from typing import Optional, Union, List
from uuid import uuid4, UUID

from banking.error import (
    ATMWithdrawalNotAllowedError,
    AccountClosedError,
    AccountError,
    ClosingCompanyAccountError,
    DailyWithdrawalLimitError,
    InsufficientFundError,
)


class Transaction:
    """Transaction object for all account transactions
    """

    class TransactionType(str, enum.Enum):
        CREDIT = "credit"
        DEBIT = "debit"

    def __init__(
        self,
        account_id: UUID,
        transaction_type: TransactionType,
        amount: float,
        occured_on: date,
    ):
        self.transaction_id = uuid4()
        self.account_id = account_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.occured_on: date = occured_on

    def __radd__(self, other):
        if self.transaction_type == Transaction.TransactionType.CREDIT:
            return other + self.amount
        else:
            return other - self.amount

    def to_dict(self):
        return {
            "transaction_id": str(self.transaction_id),
            "account_id": str(self.account_id),
            "transaction_type": self.transaction_type.value,
            "occured_on": self.occured_on.strftime("%Y-%m-%d"),
            "amount": f"{self.amount} PLN",
        }

    @classmethod
    def create(
        cls,
        account_id: UUID,
        transaction_type: TransactionType,
        amount: float,
        occured_on: Optional[date] = None,
    ) -> "Transaction":
        occured_on = occured_on or datetime.now().date()
        return cls(account_id, transaction_type, amount, occured_on)


class BankAccount:

    MINIMUM_ACCOUNT_BALANCE = 0

    def __init__(self, opened_on: date) -> None:
        self.account_id: UUID = uuid4()
        self.opened_on: date = opened_on

    @classmethod
    def open(cls, opened_on: date = datetime.now().date()) -> "BankAccount":
        return cls(opened_on=opened_on)

    def deposit(
        self, amount: float, current_balance: float, occurring_on: Optional[date] = None
    ) -> Transaction:
        assert amount > 0
        return Transaction.create(
            self.account_id, Transaction.TransactionType.CREDIT, amount, occurring_on
        )

    def withdraw(
        self,
        amount: float,
        current_balance: float,
        is_atm: bool,
        occuring_on: date,
        total_daily_amount_withdrawn: float,
    ) -> Transaction:
        self.assert_can_withdraw(
            amount, current_balance, is_atm, occuring_on, total_daily_amount_withdrawn
        )
        return Transaction.create(
            self.account_id, Transaction.TransactionType.DEBIT, amount, occuring_on
        )

    def close(
        self,
        current_balance: float,
        occuring_on: date,
        total_daily_amount_withdrawn: float,
    ) -> Optional[Transaction]:
        """withdraw balance and close the account"""
        if current_balance > 0:
            return self.withdraw(
                current_balance,
                current_balance,
                False,
                occuring_on,
                total_daily_amount_withdrawn,
            )

    def assert_can_withdraw(
        self,
        amount: float,
        current_balance: float,
        is_atm: bool,
        occuring_on: date,
        total_daily_amount_withdrawn: float,
    ):
        assert amount > 0
        if (current_balance - amount) < self.MINIMUM_ACCOUNT_BALANCE:
            raise InsufficientFundError("Insufficient funds in account")


class BankAccount_INT(BankAccount):
    """Foreign Bank Accounts"""


class BankAccount_COVID19(BankAccount):

    MAX_DAILY_WITHDRAWAL: float = 1000
    THRESHOLD_DATE: date = datetime.strptime("01042020", "%d%m%Y").date()

    def assert_can_withdraw(
        self,
        amount: float,
        current_balance: float,
        is_atm: bool,
        occuring_on: date,
        total_daily_amount_withdrawn: float,
    ):
        super().assert_can_withdraw(
            amount, current_balance, is_atm, occuring_on, total_daily_amount_withdrawn
        )
        if occuring_on >= self.THRESHOLD_DATE:
            if is_atm:
                raise ATMWithdrawalNotAllowedError(
                    "ATM withdrawals are no longer allowed as from April 1, 2020"
                )
            elif (total_daily_amount_withdrawn + amount) > self.MAX_DAILY_WITHDRAWAL:
                raise DailyWithdrawalLimitError(
                    f"Daily withdrawal amount limit of {self.MAX_DAILY_WITHDRAWAL} exceeded"
                )


class BankAccount_COVID19_Company(BankAccount_COVID19):

    MINIMUM_ACCOUNT_BALANCE = 5000

    def deposit(
        self, amount: float, current_balance: float, occurring_on: Optional[date] = None
    ) -> Transaction:
        if current_balance == 0 and amount < self.MINIMUM_ACCOUNT_BALANCE:
            raise AccountError(
                f"Company's first deposit must be non-returnable government loan\
                of {self.MINIMUM_ACCOUNT_BALANCE}"
            )
        return super().deposit(amount, current_balance, occurring_on)

    def close(
        self,
        current_balance: float,
        occuring_on: date,
        total_daily_amount_withdrawn: float,
    ) -> Optional[Transaction]:
        raise ClosingCompanyAccountError("Company account cannot be closed")
