import pickle
import typing
from collections import OrderedDict
from datetime import date
from uuid import UUID

from typing import Optional
from banking.account import BankAccount, Transaction
from banking.error import AccountNotFoundError

EntryType = typing.OrderedDict[UUID, typing.Union[BankAccount, Transaction]]
StoreType = typing.Dict[str, EntryType]

class Ledger:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.store: StoreType = {"accounts": OrderedDict(), "transactions": OrderedDict()}

    def save_object(self, obj: typing.Union[BankAccount, Transaction]):
        self.save([obj])

    def save(self, objs:typing.List[typing.Union[BankAccount, Transaction]]):
        for obj in objs:
            self.save_to_store(obj)
        self.persist()

    def save_to_store(self, obj: typing.Union[BankAccount, Transaction]):
        if isinstance(obj, BankAccount):
            self.store["accounts"][obj.account_id] = obj
        elif isinstance(obj, Transaction):
            self.store["transactions"][obj.transaction_id] = obj
        else:
            raise Exception("Programming Error: Invalid object type")

    def persist(self):
        pickle.dump(self.store, open(self.filename, 'wb'))

    def load(self):
        try:
            self.store = pickle.load(open(self.filename, 'rb'))
        except EOFError:
            self.store: StoreType = {"accounts": OrderedDict(), "transactions": OrderedDict()}

    def all_account_ids(self) -> typing.List[UUID]:
        return self.store["accounts"].keys()

    def get_account_balance(self, account_id: UUID) -> float:
        account_transactions: typing.List[Transaction] = []
        for transaction in self.store["transactions"].values():
            if transaction.account_id == account_id:
                account_transactions.append(transaction)
        return sum(account_transactions) #type: ignore

    def get_total_withdrawn_amount_by_date(self, account_id: UUID, date: date) -> float:
        withdrawal_transactions = []
        for transaction in self.store["transactions"].values():
            if (
                transaction.transaction_type == Transaction.TransactionType.DEBIT
                and transaction.account_id == account_id
            ):
                withdrawal_transactions.append(transaction)
        return abs(sum(withdrawal_transactions)) #type: ignore
    
    def get_account(self, account_id: UUID) -> BankAccount:
        try:
            return self.store["accounts"][account_id]
        except KeyError:
            raise AccountNotFoundError("Account not found, it has probably being closed")

    def close_account(self, account_id: UUID):
        try:
            del self.store["accounts"][account_id]
            self.persist()
        except KeyError:
            raise AccountNotFoundError("This account does not exist or has already been deleted")

    @property
    def is_empty(self) -> bool:
        return (
            len(self.store["accounts"]) == 0
            and len(self.store["transactions"]) == 0
        )
      