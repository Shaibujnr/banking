import enum
from datetime import date, datetime
from typing import List, Optional, Union
from uuid import UUID, uuid4

from banking.error import (
    AccountError,
    ATMWithdrawalNotAllowedError,
    ClosingCompanyAccountError,
    DailyWithdrawalLimitError,
    InsufficientFundError,
)
from banking.date_helper import get_todays_date


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
        occurred_on: date,
    ):
        self.transaction_id = uuid4()
        self.account_id = account_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.occurred_on: date = occurred_on

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
            "occurred_on": self.occurred_on.strftime("%Y-%m-%d"),
            "amount": f"{self.amount} PLN",
        }

    @classmethod
    def create(
        cls, account_id: UUID, transaction_type: TransactionType, amount: float
    ) -> "Transaction":
        """Create a new transaction

        Arguments:
            account_id {UUID} -- Id of account the transaction was performed on
            amount {float} -- Amount
            tranaction_type {TransactionType} -- type of transaction debit or credit

        Returns:
            [type] -- [description]
        """
        occurred_on = get_todays_date()
        return cls(account_id, transaction_type, amount, occurred_on)


class BankAccount:

    MINIMUM_ACCOUNT_BALANCE = 0

    def __init__(
        self, account_id: UUID, balance: float = 0, amount_withdrawn_today: float = 0
    ) -> None:
        self.account_id: UUID = account_id
        self.balance = balance
        self.amount_withdrawn_today = amount_withdrawn_today

    @classmethod
    def open(cls) -> "BankAccount":
        """Open a new bank account.
        """
        return cls(uuid4())

    def deposit(self, amount: float) -> Transaction:
        """Deposit funds into account.

        Arguments:
            amount {float} -- Amount to deposit

        Returns:
            Transaction -- A new transaction object
        """
        assert amount > 0
        return Transaction.create(
            self.account_id, Transaction.TransactionType.CREDIT, amount
        )

    def withdraw(self, amount: float, is_atm: bool) -> Transaction:
        """Withdraw funds from account.

        Arguments:
            amount {float} -- Amount to withdraw
            is_atm {bool} -- Withdrawal method is atm or not

        Returns:
            Transaction -- A new transaction object
        """
        self.assert_can_withdraw(amount, is_atm)
        return Transaction.create(
            self.account_id, Transaction.TransactionType.DEBIT, amount
        )

    def close(self) -> Optional[Transaction]:
        """withdraw balance and close the account"""
        if self.balance > 0:
            return self.withdraw(self.balance, False)

    def assert_can_withdraw(
        self, amount: float, is_atm: bool,
    ):
        """Validate and verify if the withdrawal transaction
        should be allowed.

        Arguments:
            amount {float} -- Amount to withdraw
            is_atm {bool} -- Withdrawal method is atm or not

        Raises:
            InsufficientFundError: If amount specified is not available
        """
        assert amount > 0
        if (self.balance - amount) < self.MINIMUM_ACCOUNT_BALANCE:
            raise InsufficientFundError("Insufficient funds in account")


class BankAccount_INT(BankAccount):
    """Foreign Bank Accounts"""


class BankAccount_COVID19(BankAccount):

    MAX_DAILY_WITHDRAWAL: float = 1000
    RESTRICTION_DATE: date = datetime(2020, 4, 1).date()

    def assert_can_withdraw(
        self, amount: float, is_atm: bool,
    ):
        super().assert_can_withdraw(amount, is_atm)
        occurring_on = get_todays_date()
        if occurring_on >= self.RESTRICTION_DATE:
            if is_atm:
                raise ATMWithdrawalNotAllowedError(
                    "ATM withdrawals are no longer allowed as from April 1, 2020"
                )
            elif (self.amount_withdrawn_today + amount) > self.MAX_DAILY_WITHDRAWAL:
                raise DailyWithdrawalLimitError(
                    f"Daily withdrawal amount limit of {self.MAX_DAILY_WITHDRAWAL} exceeded"
                )


class BankAccount_COVID19_Company(BankAccount_COVID19):

    MINIMUM_ACCOUNT_BALANCE = 5000

    def deposit(self, amount: float) -> Transaction:
        """Ensure company's first deposit is beyond or equal to 
        the minimum account balance which is the non-returnable 
        government loan.

        A company with 0 PLN current account balance denotes that 
        the company has never deposited funds into it's account and
        this would be it's first deposit.

        Arguments:
            amount {float} -- Amount to deposit.

        Raises:
            AccountError: If this is company's first deposit and it does not meet the minimum
            balance required.

        Returns:
            Transaction -- A new transaction object
        """
        if self.balance == 0 and amount < self.MINIMUM_ACCOUNT_BALANCE:
            raise AccountError(
                f"Company's first deposit must be non-returnable government loan\
                of {self.MINIMUM_ACCOUNT_BALANCE}"
            )
        return super().deposit(amount)

    def close(self) -> Optional[Transaction]:
        raise ClosingCompanyAccountError("Company account cannot be closed")
