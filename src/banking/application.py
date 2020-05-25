from datetime import date, datetime
from typing import Dict, List, Literal, Optional, Type
from uuid import UUID

from banking.account import (
    BankAccount,
    BankAccount_COVID19,
    BankAccount_COVID19_Company,
    BankAccount_INT,
    Transaction,
)
from banking.ledger import Ledger

AccountType = Literal["international", "company", "covid"]


class Application:

    CURRENT_DATE: date = datetime(2020, 4, 1).date()  # April 1, 2020

    ACCOUNT_TYPE_CLASS_MAPPING: Dict[str, Type[BankAccount]] = {
        "international": BankAccount_INT,
        "covid": BankAccount_COVID19,
        "company": BankAccount_COVID19_Company,
    }

    def __init__(self, ledger_file_name: str) -> None:
        self.ledger_file_name = ledger_file_name
        self.ledger = Ledger(self.ledger_file_name)

    def start(self):
        """Start the application by loading stored accounts
        and transactions into memory or creating a new pickle
        file if file doesn't exist.
        """
        try:
            open(self.ledger_file_name)
        except FileNotFoundError:
            with open(self.ledger_file_name, "wb"):
                pass
        self.ledger.load()

    def change_current_date(self, new_date: date):
        """Change the current date the simulate the day on
        which actions are performed.
        """
        self.CURRENT_DATE = new_date

    def save_account(self, account: BankAccount):
        """Store account in ledger"""
        return self.ledger.save_object(account)

    def save_transaction(self, transaction: Transaction):
        """Store transaction in ledger"""
        return self.ledger.save_object(transaction)

    def open_account(self, account_type: AccountType) -> UUID:
        """Open a new bank account of a specific type

        Arguments:
            account_type {AccountType} -- Type of account to be opened
            either internaional or covid or company

        Returns:
            UUID -- Account id of the newly opened account.
        """
        account: BankAccount = self.ACCOUNT_TYPE_CLASS_MAPPING[account_type].open(
            self.CURRENT_DATE
        )
        self.save_account(account)
        return account.account_id

    def close_account(self, account_id: UUID) -> Optional[UUID]:
        """Close an existing account"""

        ledger: Ledger = self.ledger
        account = ledger.get_account(account_id)
        current_account_balance: float = ledger.get_account_balance(account_id)
        amount_withdrawn_today = ledger.get_total_withdrawn_amount_by_date(
            account_id, self.CURRENT_DATE
        )
        transaction = account.close(
            current_account_balance, self.CURRENT_DATE, amount_withdrawn_today
        )
        if transaction is not None:
            self.save_transaction(transaction)
        self.ledger.close_account(account_id)
        return transaction.transaction_id if transaction is not None else None

    def withdraw(self, account_id: UUID, amount: float, is_atm: bool) -> UUID:
        """Withdraw a specific amount from an account

        Arguments:
            account_id {UUID} -- Id of account to debit
            amount {float} -- Amount to debit from the account
            is_atm {bool} -- Is withdrawal via ATM

        Returns:
            UUID -- Id of the newly created transaction
        """
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
            amount_withdrawn_on_date,
        )
        self.save_transaction(transaction)
        return transaction.transaction_id

    def deposit(self, account_id: UUID, amount: float) -> UUID:
        """Deposit funds into an account.

        Arguments:
            account_id {UUID} -- Id of account to be credited
            amount {float} -- amount to credit the account with

        Returns:
            UUID -- Id of the newly created transaction
        """
        account = self.ledger.get_account(account_id)
        current_account_balance = self.ledger.get_account_balance(account_id)
        transaction = account.deposit(
            amount, current_account_balance, self.CURRENT_DATE
        )
        self.save_transaction(transaction)
        return transaction.transaction_id

    def all_accounts(self) -> List[dict]:
        """Returns details of all accounts from the ledger"""

        result = []
        for account_id in self.ledger.all_account_ids():
            result.append(self.get_account_details(account_id))
        return result

    def all_transactions(self) -> List[dict]:
        """Returns details of all transactions from the ledger"""
        result = []
        for transaction in self.ledger.store["transactions"].values():
            result.append(transaction.to_dict())
        return result

    def get_account_details(self, account_id: UUID) -> dict:
        result = {}
        account = self.ledger.get_account(account_id)
        balance = self.ledger.get_account_balance(account_id)
        result["account_id"] = str(account_id)
        result["opened_on"] = account.opened_on.strftime("%Y-%m-%d")
        result["balance"] = f"{balance} PLN"
        result["type"] = self.__get_account_type(account)
        return result

    def __get_account_type(self, account: BankAccount):
        if isinstance(account, BankAccount_COVID19):
            return "covid"
        elif isinstance(account, BankAccount_COVID19_Company):
            return "company"
        elif isinstance(account, BankAccount_INT):
            return "international"
        raise Exception("Invalid account type")


def create_application(ledger_file_name: str):
    """Create a bank application

    Arguments:
        ledger_file_name {str} -- name of the ledger.
    """

    return Application(ledger_file_name)
