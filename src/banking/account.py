from datetime import date, datetime
import enum
from typing import Optional, Union
from uuid import uuid4, UUID

from banking.error import (
    ATMWithdrawalNotAllowedError, AccountClosedError, 
    ClosingCompanyAccountError, 
    DailyWithdrawalAmountLimitExceededError, 
    InsufficientFundError, OpenAccountError
)


class Transaction:
    """Transaction object for all account transactions
    """

    class TransactionType(str, enum.Enum):
        CREDIT = "credit"
        DEBIT = "debit"

    def __init__(
        self, 
        account_id:UUID, 
        transaction_type:TransactionType, 
        amount: float, 
        occured_on: date
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

    @classmethod
    def create(
        cls, 
        account_id: UUID, 
        transaction_type:TransactionType, 
        amount: float,
        occured_on: Optional[date] = None
    ) -> "Transaction":
        occured_on = occured_on or datetime.now().date()
        return cls(account_id, transaction_type, amount, occured_on)

class BankAccount:

    MINIMUM_ACCOUNT_BALANCE = 0

    def __init__(self, opened_on: date) -> None:
        self.account_id: UUID = uuid4()
        self.opened_on: date = opened_on

    @classmethod
    def open(cls, amount: float, opened_on: date = datetime.now().date()) -> "BankAccount":
        account = cls(opened_on=opened_on)
        if amount < cls.MINIMUM_ACCOUNT_BALANCE:
            raise OpenAccountError(f"deposit of {cls.MINIMUM_ACCOUNT_BALANCE} minimum is required to open this account")
        if amount > 0:
            #todo persist transaction?
            transaction = account.deposit(amount)
        return account

    def deposit(self, amount: float) -> Transaction:
        assert amount > 0
        return Transaction.create(
            self.account_id,
            Transaction.TransactionType.CREDIT,
            amount
        )

    def withdraw(
        self, 
        amount: float, 
        current_balance: float,
        is_atm: bool,
        occuring_on: date,
        total_daily_amount_withdrawn: float
    ) -> Transaction:
        self.assert_can_withdraw(
            amount, 
            current_balance,
            is_atm,
            occuring_on,
            total_daily_amount_withdrawn
        )
        return self.debit(amount)    

    def debit(self, amount: float) -> Transaction:
        return Transaction.create(
            self.account_id,
            Transaction.TransactionType.DEBIT,
            amount
        )

    def close(self, current_balance: float) -> Optional[Transaction]:
        """withdraw balance and close the account"""
        if current_balance > 0:
            return self.debit(current_balance)

    def assert_can_withdraw(
        self, 
        amount: float, 
        current_balance: float,
        is_atm: bool,
        occuring_on: date,
        total_daily_amount_withdrawn: float
    ):
        assert amount > 0
        if (current_balance - amount) < self.MINIMUM_ACCOUNT_BALANCE:
            raise InsufficientFundError("Insufficient funds in account")

class BankAccount_INT(BankAccount):
    """Foreign Bank Accounts"""

class BankAccount_COVID19(BankAccount):

    MAX_DAILY_WITHDRAWAL: float = 1000
    THRESHOLD_DATE: date = datetime.strptime('01042020', '%d%m%Y').date()


    def assert_can_withdraw(
        self, 
        amount: float, 
        current_balance: float,
        is_atm: bool,
        occuring_on: date,
        total_daily_amount_withdrawn: float
    ):
        super().assert_can_withdraw(
            amount, 
            current_balance, 
            is_atm, 
            occuring_on, 
            total_daily_amount_withdrawn
        )
        if occuring_on >= self.THRESHOLD_DATE:
            if is_atm:
                raise ATMWithdrawalNotAllowedError("ATM withdrawals are no longer allowed")
            elif (total_daily_amount_withdrawn + amount) > self.MAX_DAILY_WITHDRAWAL:
                raise DailyWithdrawalAmountLimitExceededError(
                    f"Daily withdrawal amount limit of {self.MAX_DAILY_WITHDRAWAL} exceeded"
                )

class BankAccount_COVID19_Company(BankAccount_COVID19):

    MINIMUM_ACCOUNT_BALANCE = 5000

    def close(self, current_balance: float):
        raise ClosingCompanyAccountError("Company account cannot be closed")
    
