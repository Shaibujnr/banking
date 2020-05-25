import pickle
import typing
from collections import OrderedDict
from datetime import date
from typing import Optional
from uuid import UUID

from banking.account import BankAccount, Transaction
from banking.error import AccountNotFoundError
from banking.date_helper import get_todays_date

EntryType = typing.OrderedDict[
    UUID, typing.Union[typing.Type[BankAccount], Transaction]
]
StoreType = typing.Dict[str, EntryType]


class Ledger:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.store: StoreType = {
            "accounts": OrderedDict(),
            "transactions": OrderedDict(),
        }

    def save_object(self, obj: typing.Union[BankAccount, Transaction]):
        """Store a single account or transaction object"""
        self.save([obj])

    def save(self, objs: typing.List[typing.Union[BankAccount, Transaction]]):
        """Store a list of account and/or transacion objects"""
        for obj in objs:
            self.save_to_store(obj)
        self.persist()

    def save_to_store(self, obj: typing.Union[BankAccount, Transaction]):
        if isinstance(obj, BankAccount):
            self.store["accounts"][obj.account_id] = type(obj)
        elif isinstance(obj, Transaction):
            self.store["transactions"][obj.transaction_id] = obj
        else:
            raise Exception("Programming Error: Invalid object type")

    def persist(self):
        pickle.dump(self.store, open(self.filename, "wb"))

    def load(self):
        """Load transaction and accounts from store"""
        try:
            self.store = pickle.load(open(self.filename, "rb"))
        except EOFError:
            self.store: StoreType = {
                "accounts": OrderedDict(),
                "transactions": OrderedDict(),
            }

    def all_account_ids(self) -> typing.List[UUID]:
        """Return all account Ids"""
        return self.store["accounts"].keys()

    def all_transaction_ids(self) -> typing.List[UUID]:
        """Return all transaction ids"""
        return self.store["transactions"].keys()

    def get_account_balance(self, account_id: UUID) -> float:
        """Fetch and calculate the account balance of a transacion
        from all it's previous transactions

        Arguments:
            account_id {UUID} -- Target account id

        Returns:
            float -- account balance
        """
        account_transactions: typing.List[Transaction] = []
        for transaction in self.store["transactions"].values():
            if transaction.account_id == account_id:
                account_transactions.append(transaction)
        return sum(account_transactions)  # type: ignore

    def get_total_withdrawn_amount_by_date(self, account_id: UUID, date: date) -> float:
        """Get the sum of amount withdrawn by the account on the day 
        denoted by the passed in date.

        Arguments:
            account_id {UUID} -- Target account id
            date {date} -- The date to fetch sum of withdrawal transactions for

        Returns:
            float -- sum of amount of each withdrawal transaction on that day
        """
        withdrawal_transactions = []
        for transaction in self.store["transactions"].values():
            if (
                transaction.transaction_type == Transaction.TransactionType.DEBIT
                and transaction.account_id == account_id
            ):
                withdrawal_transactions.append(transaction)
        return abs(sum(withdrawal_transactions))  # type: ignore

    def get_account(self, account_id: UUID) -> BankAccount:
        """Get an account from the ledger

        Arguments:
            account_id {UUID} -- Id of account

        Raises:
            AccountNotFoundError: When account doesn't exist or is deleted

        Returns:
            BankAccount -- Returns a bank account object.
        """
        current_date = get_todays_date()
        try:
            account_class: typing.Type[BankAccount] = self.store["accounts"][account_id]
            current_balance = self.get_account_balance(account_id)
            amount_withdrawn_today = self.get_total_withdrawn_amount_by_date(
                account_id, current_date
            )
            return account_class(account_id, current_balance, amount_withdrawn_today)
        except KeyError:
            raise AccountNotFoundError(
                "Account not found, it has probably being closed"
            )

    def close_account(self, account_id: UUID):
        """Delete account from store"""
        try:
            del self.store["accounts"][account_id]
            self.persist()
        except KeyError:
            raise AccountNotFoundError(
                "This account does not exist or has already been deleted"
            )

    @property
    def is_empty(self) -> bool:
        """Returns True if store is empty i.e no accounts and no transactions"""
        return len(self.store["accounts"]) == 0 and len(self.store["transactions"]) == 0
