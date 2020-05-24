from datetime import datetime, date
from typing import Literal, Optional, Dict, Type, List
from uuid import UUID
from banking.account import BankAccount, BankAccount_COVID19, BankAccount_COVID19_Company, BankAccount_INT, Transaction
from banking.error import OpenAccountError
from banking.ledger import Ledger


AccountType = Literal["international", "company", "covid"]

class Application:

    CURRENT_DATE: date = datetime(2020, 4, 1).date() # April 1, 2020
    
    ACCOUNT_TYPE_CLASS_MAPPING: Dict[str, Type[BankAccount]] = {
        "international": BankAccount_INT,
        "covid": BankAccount_COVID19,
        "company": BankAccount_COVID19_Company
    }

    def __init__(self, ledger_file_name: str) -> None:
        self.ledger_file_name = ledger_file_name
        self.ledger = Ledger(self.ledger_file_name)

    def start(self):
        try:
            open(self.ledger_file_name)
        except FileNotFoundError:
            with open(self.ledger_file_name, 'wb'): pass
        self.ledger.load()

    def change_current_date(self, new_date: date):
        self.CURRENT_DATE = new_date

    def save_account(self, account: BankAccount):
        return self.ledger.save_object(account)

    def save_transaction(self, transaction: Transaction):
        return self.ledger.save_object(transaction)

    def open_account(self, account_type: AccountType, amount: float = 0) -> UUID:
        account: BankAccount =  self.ACCOUNT_TYPE_CLASS_MAPPING[account_type].open(amount, self.CURRENT_DATE)
        self.save_account(account)
        return account.account_id

    def close_account(self, account_id: UUID) -> Optional[UUID]:
        account = self.ledger.get_account(account_id)
        current_account_balance: float = self.ledger.get_account_balance(account_id)
        transaction = account.close(current_account_balance)
        if transaction is not None:
            self.save_transaction(transaction)
        self.ledger.close_account(account_id)
        return transaction.transaction_id if transaction is not None else None

    def withdraw(self, account_id: UUID, amount: float, is_atm: bool) -> UUID:
        account: BankAccount = self.ledger.get_account(account_id)
        current_account_balance = self.ledger.get_account_balance(account_id)
        amount_withdrawn_on_date = self.ledger.get_total_withdrawn_amount_by_date(
            account_id, self.CURRENT_DATE
        )
        transaction = account.withdraw(
            amount,
            current_account_balance,
            is_atm,
            self.CURRENT_DATE,
            amount_withdrawn_on_date
        )
        self.save_transaction(transaction)
        return transaction.transaction_id
    
    def deposit(self, account_id: UUID, amount: float) -> UUID:
        account = self.ledger.get_account(account_id)
        transaction = account.deposit(amount)
        self.save_transaction(transaction)
        return transaction.transaction_id

    def all_accounts(self) -> List[UUID]:
        return self.ledger.all_account_ids()

    def get_account_details(self, account_id: UUID) -> dict:
        result = {}
        account = self.ledger.get_account(account_id)
        balance = self.ledger.get_account_balance(account_id)
        result["account_id"] = account_id
        result["opened_on"] = account.opened_on
        result["balance"] = balance
        return result
