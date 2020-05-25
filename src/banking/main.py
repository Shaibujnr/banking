from datetime import date, datetime
from functools import wraps
from typing import Callable
from uuid import UUID

import json
import typer

from banking.application import Application, create_application
from banking.error import AccountError
from banking.date_helper import get_todays_date

banking_app: Application = create_application("ledger.pkl")
banking_app.start()

app = typer.Typer()

DATE_FORMAT = "%Y-%m-%d"


def set_occurring_on(func: Callable):
    """Decorator function to set applications current
    running date and performing whatever action is required
    on that date.
    """

    @wraps(func)
    def wrapper_func(*args, **kwargs):
        try:
            occurring_on: str = kwargs.get("date")  # type: ignore
            if occurring_on is None:
                return func(*args, **kwargs)
            occurring_on_date: date = datetime.strptime(
                occurring_on, DATE_FORMAT
            ).date()
            banking_app.change_current_date(occurring_on_date)
            typer.echo(f"Current date set to {get_todays_date().strftime(DATE_FORMAT)}")
            func(*args, **kwargs)
        except ValueError:
            typer.echo("Invalid date")
            raise typer.Abort()

    return wrapper_func


def style(text: str, is_success: bool = True, bg=False) -> str:
    color = typer.colors.GREEN if is_success else typer.colors.RED
    if bg:
        return typer.style(text, fg=typer.colors.WHITE, bg=color)
    else:
        return typer.style(text, fg=color)


@app.command()
@set_occurring_on
def open(account_type: str, date: str = None):
    """Open an account of a specific type.

    Supported account types are

    - international -- For international/foreign accounts BankAccount_INT

    - covid -- For BankAccount_Covid19

    - company -- For BankAccount_Covid19_Company

    Use --date to optionally set/simulate the date this account is opened

    date format is YYYY-mm-dd eg. 2020-04-01

    Example:

    - banking open covid

    - banking open covid --date 2018-12-23
    """
    try:
        account_id: UUID = banking_app.open_account(account_type)  # type: ignore
        account_type_string: str = style(account_type)
        account_id_string: str = style(str(account_id))
        result_string: str = f"{account_type_string}"
        result_string += " Account successfully created, Here's the account id "
        result_string += f"{account_id_string}"
        typer.echo(result_string)
    except KeyError:
        account_type_string: str = style(account_type, is_success=False)
        typer.echo(f"Invalid account type {account_type_string}")
        raise typer.Abort()


@app.command()
@set_occurring_on
def withdraw(account_id: str, amount: float, atm: bool = False, date: str = None):
    """Withdraw funds from an account

    account_id -- Id of account to be debited

    amount -- Amount to withdraw from account

    Use --atm flag to denote if the withdrawal method is via ATM or not (--no-atm)

    The default withdrawal method is no atm

    Use --date to optionally set/simulate the date this account is opened

    date format is YYYY-mm-dd eg. 2020-04-01

    Example:

    - banking withdraw 7ae3fcfd-da50-43c3-9c6f-c5d1adaaebbc 45.37 --atm

    - banking withdraw 7ae3fcfd-da50-43c3-9c6f-c5d1adaaebbc 45.37 --date 2018-12-23
    """
    try:
        transaction_id = banking_app.withdraw(UUID(account_id), amount, atm)
        transaction_id_string: str = style(str(transaction_id))
        typer.echo(f"Withdrawal successful, transaction id is {transaction_id_string}")
    except AccountError as e:
        typer.echo(style(str(e) + "!!", is_success=False))


@app.command()
@set_occurring_on
def deposit(account_id: str, amount: float, date: str = None):
    """Deposit funds into an account

    account_id -- Id of account to be debited

    amount -- Amount to withdraw from account

    Use --date to optionally set/simulate the date this account is opened

    date format is YYYY-mm-dd eg. 2020-04-01

    Example:

    - banking deposit 7ae3fcfd-da50-43c3-9c6f-c5d1adaaebbc 45.37

    - banking deposit 7ae3fcfd-da50-43c3-9c6f-c5d1adaaebbc 45.37 --date 2018-12-23
    """
    try:
        transaction_id = banking_app.deposit(UUID(account_id), amount)
        transaction_id_string: str = style(str(transaction_id))
        typer.echo(f"Deposit successful, transaction id is {transaction_id_string}")
    except AccountError as e:
        typer.echo(style(str(e) + "!!", is_success=False))


@app.command()
def ls(
    show_accounts: bool = True, show_transactions: bool = True, only_ids: bool = False
):
    """Display all accounts and/or transactions

    Use --show-accounts/--no-show-accounts flag to display/hide accounts. Default is --show-accounts.

    Use --show-transactions/--no-show-transactions flag to display/hide transactions. Default is --show-transactions.

    Use --only-ids flag to display only the ids of the accounts and/or transactions. Disabled by default.

    Exmaple:

    - banking ls --only-ids --no-show-accounts
    """
    accounts = []
    transactions = []
    store = banking_app.ledger.store
    if show_accounts:
        title: str = "Account Ids" if only_ids else "Accounts"
        typer.echo(typer.style(f"\n{title}", fg=typer.colors.MAGENTA))
        typer.echo(typer.style("===========", fg=typer.colors.MAGENTA))
        accounts += (
            [str(uid) for uid in store["accounts"].keys()]
            if only_ids
            else banking_app.all_accounts()
        )
        accounts = accounts or ["-----No open account---"]
        typer.echo(
            "\n".join(
                typer.style(
                    json.dumps(acc, indent=4, sort_keys=True),
                    fg=typer.colors.BRIGHT_BLUE,
                )
                for acc in accounts
            )
        )
    if show_transactions:
        title: str = "Transaction Ids" if only_ids else "Transactions"
        typer.echo(typer.style(f"\n{title}", fg=typer.colors.MAGENTA))
        typer.echo(typer.style("===========", fg=typer.colors.MAGENTA))
        transactions += (
            [str(uid) for uid in store["transactions"].keys()]
            if only_ids
            else banking_app.all_transactions()
        )
        transactions = transactions or ["-----No transaction----"]
        typer.echo(
            "\n".join(
                typer.style(
                    json.dumps(transaction, indent=4, sort_keys=True),
                    fg=typer.colors.BRIGHT_BLUE,
                )
                for transaction in transactions
            )
        )


@app.command()
def show(entity_id: str):
    """Show details of a specific account/transaction

    Enity_Id is the Id of the account or the transaction

    Example:

    - banking show 7ae3fcfd-da50-43c3-9c6f-c5d1adaaebbc
    """
    try:
        uid: UUID = UUID(entity_id)
        if uid in banking_app.ledger.store["accounts"]:
            typer.echo(typer.style("Account", fg=typer.colors.MAGENTA))
            typer.echo(typer.style("=========", fg=typer.colors.MAGENTA))
            typer.echo(
                typer.style(
                    json.dumps(
                        banking_app.get_account_details(uid), indent=4, sort_keys=True
                    ),
                    fg=typer.colors.BRIGHT_BLUE,
                )
            )
            typer.Exit()
        elif uid in banking_app.ledger.store["transactions"]:
            typer.echo(typer.style("Transaction", fg=typer.colors.MAGENTA))
            typer.echo(typer.style("=========", fg=typer.colors.MAGENTA))
            typer.echo(
                typer.style(
                    json.dumps(
                        banking_app.ledger.store["transactions"][uid].to_dict(),
                        indent=4,
                        sort_keys=True,
                    ),
                    fg=typer.colors.BRIGHT_BLUE,
                )
            )
            typer.Exit()
    except KeyError:
        typer.echo(style("Entity not found !!", is_success=False))
        raise typer.Abort()
    except ValueError:
        typer.echo(f"Invalid Id {style(entity_id, is_success=False)}")
        raise typer.Abort()


@app.command()
@set_occurring_on
def close(account_id: str, date: str = None):
    """Close an account

    account_id -- Id of account to be closed

    Use --date to optionally set/simulate the date this account is opened

    date format is YYYY-mm-dd eg. 2020-04-01

    Example:

    - banking close 7ae3fcfd-da50-43c3-9c6f-c5d1adaaebbc

    - banking close 7ae3fcfd-da50-43c3-9c6f-c5d1adaaebbc --date 2018-12-23
    """
    close = typer.confirm("Are you sure you want to close this account?")
    if not close:
        raise typer.Abort()
    try:
        transaction_id = banking_app.close_account(UUID(account_id))
        if transaction_id is not None:
            typer.echo(f"Account {account_id} was not empty")
            typer.echo(f"Account balance has been withdrawn")
            typer.echo(
                f"Transaction id for the withdrawal is {style(str(transaction_id))}"
            )
        typer.echo(
            f"Account {typer.style(str(account_id), fg=typer.colors.BRIGHT_BLUE)} closed and deleted"
        )
    except AccountError as e:
        typer.echo(style(str(e) + " !!!", False))
        raise typer.Abort()


if __name__ == "__main__":
    app()
