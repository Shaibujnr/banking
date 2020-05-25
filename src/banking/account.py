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
        cls,
        account_id: UUID,
        transaction_type: TransactionType,
        amount: float,
        occurred_on: Optional[date] = None,
    ) -> "Transaction":
        """Create a new transaction

        Arguments:
            account_id {UUID} -- Id of account the transaction was performed on
            amount {float} -- Amount
            tranaction_type {TransactionType} -- type of transaction debit or credit
            occurred_on {bool} -- Date on which this transaction occurred

        Returns:
            [type] -- [description]
        """
        occurred_on = occurred_on or datetime.now().date()
        return cls(account_id, transaction_type, amount, occurred_on)


class BankAccount:

    MINIMUM_ACCOUNT_BALANCE = 0

    def __init__(self, opened_on: date) -> None:
        self.account_id: UUID = uuid4()
        self.opened_on: date = opened_on

    @classmethod
    def open(cls, opened_on: date = datetime.now().date()) -> "BankAccount":
        """Open a new bank account.
        """
        return cls(opened_on=opened_on)

    def deposit(
        self, amount: float, current_balance: float, occurring_on: Optional[date] = None
    ) -> Transaction:
        """Deposit funds into account.

        Arguments:
            amount {float} -- Amount to deposit
            current_balance {float} -- Current account balance from ledger

        Keyword Arguments:
            occurring_on {Optional[date]} -- Date on which this deposit is taking place (default: {None})

        Returns:
            Transaction -- A new transaction object
        """
        assert amount > 0
        return Transaction.create(
            self.account_id, Transaction.TransactionType.CREDIT, amount, occurring_on
        )

    def withdraw(
        self,
        amount: float,
        current_balance: float,
        is_atm: bool,
        occurring_on: date,
        total_daily_amount_withdrawn: float,
    ) -> Transaction:
        """Withdraw funds from account.

        Arguments:
            amount {float} -- Amount to withdraw
            current_balance {float} -- Current Account balance from ledger
            is_atm {bool} -- Withdrawal method is atm or not
            occurring_on {date} -- Date on which this withdrawal is taking place
            total_daily_amount_withdrawn {float} -- Total amount withdrawn on this day

        Returns:
            Transaction -- A new transaction object
        """
        self.assert_can_withdraw(
            amount, current_balance, is_atm, occurring_on, total_daily_amount_withdrawn
        )
        return Transaction.create(
            self.account_id, Transaction.TransactionType.DEBIT, amount, occurring_on
        )

    def close(
        self,
        current_balance: float,
        occurring_on: date,
        total_daily_amount_withdrawn: float,
    ) -> Optional[Transaction]:
        """withdraw balance and close the account"""
        if current_balance > 0:
            return self.withdraw(
                current_balance,
                current_balance,
                False,
                occurring_on,
                total_daily_amount_withdrawn,
            )

    def assert_can_withdraw(
        self,
        amount: float,
        current_balance: float,
        is_atm: bool,
        occurring_on: date,
        total_daily_amount_withdrawn: float,
    ):
        """Validate and verify if the withdrawal transaction
        should be allowed.

        Arguments:
            amount {float} -- Amount to withdraw
            current_balance {float} -- Current account balance from ledger
            is_atm {bool} -- Withdrawal method is atm or not
            occurring_on {date} -- Date on which the withdrawal is taking place
            total_daily_amount_withdrawn {float} -- Total amount withdrawn on that day

        Raises:
            InsufficientFundError: If amount specified is not available
        """
        assert amount > 0
        if (current_balance - amount) < self.MINIMUM_ACCOUNT_BALANCE:
            raise InsufficientFundError("Insufficient funds in account")


class BankAccount_INT(BankAccount):
    """Foreign Bank Accounts"""


class BankAccount_COVID19(BankAccount):

    MAX_DAILY_WITHDRAWAL: float = 1000
    RESTRICTION_DATE: date = datetime.strptime("01042020", "%d%m%Y").date()

    def assert_can_withdraw(
        self,
        amount: float,
        current_balance: float,
        is_atm: bool,
        occurring_on: date,
        total_daily_amount_withdrawn: float,
    ):
        super().assert_can_withdraw(
            amount, current_balance, is_atm, occurring_on, total_daily_amount_withdrawn
        )
        if occurring_on >= self.RESTRICTION_DATE:
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
        """Ensure company's first deposit is beyond or equal to 
        the minimum account balance which is the non-returnable 
        government loan.

        A company with 0 PLN current account balance denotes that 
        the company has never deposited funds into it's account and
        this would be it's first deposit.

        Arguments:
            amount {float} -- Amount to deposit.
            current_balance {float} -- Current account balance

        Keyword Arguments:
            occurring_on {Optional[date]} -- Date on which this is taking place (default: {None})

        Raises:
            AccountError: If this is company's first deposit and it does not meet the minimum
            balance required.

        Returns:
            Transaction -- A new transaction object
        """
        if current_balance == 0 and amount < self.MINIMUM_ACCOUNT_BALANCE:
            raise AccountError(
                f"Company's first deposit must be non-returnable government loan\
                of {self.MINIMUM_ACCOUNT_BALANCE}"
            )
        return super().deposit(amount, current_balance, occurring_on)

    def close(
        self,
        current_balance: float,
        occurring_on: date,
        total_daily_amount_withdrawn: float,
    ) -> Optional[Transaction]:
        raise ClosingCompanyAccountError("Company account cannot be closed")
