import datetime
import enum
from typing import Optional, Union
from uuid import uuid4, UUID

from banking.error import (
    AccountClosedError, 
    ClosingCompanyAccountError, 
    DailyWithdrawalAmountLimitExceededError, 
    InsufficientFundError
)


class Transaction:
    """Transaction object for all account transactions
    """

    class TransactionType(str, enum.Enum):
        CREDIT = "credit"
        DEBIT = "debit"

    def __init__(self, account_id:UUID, transaction_type:TransactionType, amount: float):
        self.transaction_id = uuid4()
        self.account_id = account_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.date = datetime.datetime.now()

    @classmethod
    def create(cls, account_id: UUID, transaction_type:TransactionType, amount: float) -> "Transaction":
        return cls(account_id, transaction_type, amount)

class BankAccount:

    MINIMUM_ACCOUNT_BALANCE = 0

    def __init__(self) -> None:
        self.balance: float = 0.0
        self.account_id: UUID = uuid4()
        self.is_closed: bool = False

    @classmethod
    def create(cls) -> "BankAccount":
        return cls()

    @property
    def is_empty(self) -> bool:
        return self.balance == 0

    def deposit(self, amount: float) -> Transaction:
        self.assert_account_is_not_closed()
        assert amount > 0
        self.balance += amount
        return Transaction.create(
            self.account_id,
            Transaction.TransactionType.CREDIT,
            amount
        )

    def withdraw(self, amount: float) -> Transaction:
        #todo support withdraw types (ATM and not ATM)?
        self.assert_account_is_not_closed()
        self.assert_can_withdraw(amount)
        return self.debit(amount)    

    def debit(self, amount: float) -> Transaction:
        self.balance  -= amount
        return Transaction.create(
            self.account_id,
            Transaction.TransactionType.DEBIT,
            amount
        )

    def close(self) -> Optional[Transaction]:
        """withdraw balance and close the account"""
        self.is_closed = True
        if self.balance > 0:
            return self.debit(self.balance)

    def assert_can_withdraw(self, amount: float):
        assert amount > 0
        if (self.balance - amount) < self.MINIMUM_ACCOUNT_BALANCE:
            raise InsufficientFundError("Insufficient funds in account")
    
    def assert_account_is_not_closed(self):
        if self.is_closed:
            raise AccountClosedError("Account is closed")

class BankAccount_INT(BankAccount):
    """Foreign Bank Accounts"""

class BankAccount_COVID19(BankAccount):

    MAX_DAILY_WITHDRAWAL: float = 1000
    THRESHOLD_DATE: datetime.date = datetime.datetime.strptime('01042020', '%d%m%Y').date()


    def withdraw(self, amount: float, total_sum_for_the_day: float, date: datetime.date) -> Transaction:
        self.assert_account_is_not_closed()
        self.assert_can_withdraw(amount, total_sum_for_the_day, date)
        return self.debit(amount)

    def assert_can_withdraw(self, amount: float, total_sum_for_the_day: float, date: datetime.date):
        super().assert_can_withdraw(amount)
        if date >= self.THRESHOLD_DATE:
            if (total_sum_for_the_day + amount) > self.MAX_DAILY_WITHDRAWAL:
                raise DailyWithdrawalAmountLimitExceededError(
                    f"Daily withdrawal amount limit of {self.MAX_DAILY_WITHDRAWAL} exceeded"
                )

    def daily_withdrawal_transaction_sum(self, date: datetime.date) -> float:
        #todo calculate current daily withdrawal sum from transactions
        #todo collect date input or use current date?
        return 0

class BankAccount_COVID19_Company(BankAccount_COVID19):

    MINIMUM_ACCOUNT_BALANCE = 5000

    def close(self):
        raise ClosingCompanyAccountError("Company account cannot be closed")
