from uuid import uuid4, UUID


class BankAccount:
    def __init__(self) -> None:
        self.balance: float = 0.0
        self.account_id: UUID = uuid4()

    def deposit(self, amount: float):
        pass

    def withdraw(self, amount: float):
        pass

    def close(self):
        pass

class BankAccount_INT(BankAccount):
    pass

class BankAccount_COVID19(BankAccount):
    pass

class BankAccount_COVID19_Company(BankAccount):
    pass