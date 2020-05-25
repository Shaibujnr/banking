from datetime import date, datetime
import typer
from uuid import UUID
from functools import wraps
from typing import Callable
from banking.application import Application
from banking.error import AccountError

banking_app: Application = Application("ledger.pkl")
banking_app.start()

app = typer.Typer()

DATE_FORMAT = "%Y-%m-%d"


def set_occuring_on(func: Callable):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        try:
            occuring_on: str = kwargs.get("date") #type: ignore
            if occuring_on is None:
                return func(*args, **kwargs)
            occuring_on_date: date = datetime.strptime(occuring_on, DATE_FORMAT)
            banking_app.change_current_date(occuring_on_date)
            typer.echo(f"Current date set to {banking_app.CURRENT_DATE.strftime(DATE_FORMAT)}")
            func(*args, **kwargs)
        except ValueError:
            typer.echo("Invalid date")
            typer.Abort()
    return wrapper_func


@app.command()
@set_occuring_on
def open(account_type: str, date: str = None):
    """Open an account. Some accounts type usually require a minimum amount deposit
    to be successfully opened. In this case, company accounts require a minimum initial
    deposit of 5000.

    Arguments:
        account_type {str} -- One of either 'international', 'covid' or 'company'
    """
    account_id = banking_app.open_account(account_type) #type: ignore
    typer.secho(f"{account_type} Account successfully created, Here's the account id {account_id}")

@app.command()
@set_occuring_on
def withdraw(account_id: str, amount: float, atm: bool = False, date: str = None):
    """Withdraw from an account

    Arguments:
        account_id {str} -- Id of account to be debited
        amount {float} -- Amount to withdraw from account

    Keyword Arguments:
        atm {bool} -- Is this an atm withdrawal? (default: {False})
    """
    try:
        transaction_id = banking_app.withdraw(UUID(account_id), amount, atm)
        typer.echo(f"Withdrawal successful, transaction id is {transaction_id}")
    except AccountError as e:
        typer.echo(str(e))

@app.command()
@set_occuring_on
def deposit(account_id: str, amount: float, date: str = None):
    """Deposit into account

    Arguments:
        account_id {str} -- Account to credit
        amount {float} -- Amount to deposit into the account
    """
    try:
        transaction_id = banking_app.deposit( UUID(account_id), amount)
        typer.echo(f"Deposit successful, transaction id is {transaction_id}")
    except AccountError as e:
        typer.echo(str(e))

@app.command()
def ls(show_accounts: bool = True, show_transactions: bool = True, only_ids: bool = False):
    """Display all accounts and/or transactions

    Keyword Arguments:
        show_accounts {bool} -- Display accounts and details (default: {True})
        show_transactions {bool} -- Display transactions and details (default: {True})
        only_ids {bool} -- Display ids only no details (default: {False})
    """
    #todo display entities properly
    accounts = []
    transactions = []
    store = banking_app.ledger.store
    if show_accounts:
        typer.echo("\nAccounts")
        typer.echo("===========")
        accounts += store["accounts"].keys() if only_ids else banking_app.all_accounts()
        accounts = accounts or ["-----No open account---"]
        typer.echo("\n".join(str(acc) for acc in accounts))
    if show_transactions:
        typer.echo("\nTransactions")
        typer.echo("===========")
        transactions += store["transactions"].keys() if only_ids else banking_app.all_transactions()
        transactions = transactions or ["-----No transaction----"]
        typer.echo("\n".join(str(transaction) for transaction in transactions))

@app.command()
def show(entity_id: str):
    try:
        uid: UUID = UUID(entity_id)
        if uid in banking_app.ledger.store["accounts"]:
            typer.echo("Account")
            typer.echo("=========")
            typer.echo(banking_app.get_account_details(uid))
            typer.Exit()
        elif uid in banking_app.ledger.store["transactions"]:
            typer.echo("Transaction")
            typer.echo("=========")
            typer.echo(banking_app.ledger.store["transactions"][uid].to_dict())
            typer.Exit()
    except KeyError:
        typer.echo("Entity not found")
        typer.Abort()
    except ValueError:
        typer.echo(f"Invalid Id {entity_id}")
        typer.Abort()
    
@app.command()
@set_occuring_on
def close(account_id: str, date: str = None):
    """Close account

    Arguments:
        account_id {str} -- Id of account to close
    """
    try:
        transaction_id = banking_app.close_account(UUID(account_id))
        if transaction_id is not None:
            typer.echo(f"Account {account_id} was not empty")
            typer.echo(f"Account balance has been withdrawn")
            typer.echo(f"Transaction id for the withdrawal is {transaction_id}")
        typer.echo(f"Account {account_id} closed and deleted")
    except AccountError as e:
        typer.echo(str(e))
        typer.Abort()


if __name__ == "__main__":
    app()