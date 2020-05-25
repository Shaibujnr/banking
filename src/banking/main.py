from datetime import date, datetime
from functools import wraps
from typing import Callable
from uuid import UUID

import typer

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
            occuring_on: str = kwargs.get("date")  # type: ignore
            if occuring_on is None:
                return func(*args, **kwargs)
            occuring_on_date: date = datetime.strptime(occuring_on, DATE_FORMAT).date()
            banking_app.change_current_date(occuring_on_date)
            typer.echo(
                f"Current date set to {banking_app.CURRENT_DATE.strftime(DATE_FORMAT)}"
            )
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
@set_occuring_on
def open(account_type: str, date: str = None):
    """Open an account. Some accounts type usually require a minimum amount deposit
    to be successfully opened. In this case, company accounts require a minimum initial
    deposit of 5000.

    Arguments:
        account_type {str} -- One of either 'international', 'covid' or 'company'
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
        transaction_id_string: str = style(str(transaction_id))
        typer.echo(f"Withdrawal successful, transaction id is {transaction_id_string}")
    except AccountError as e:
        typer.echo(style(str(e) + "!!", is_success=False))


@app.command()
@set_occuring_on
def deposit(account_id: str, amount: float, date: str = None):
    """Deposit into account

    Arguments:
        account_id {str} -- Account to credit
        amount {float} -- Amount to deposit into the account
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

    Keyword Arguments:
        show_accounts {bool} -- Display accounts and details (default: {True})
        show_transactions {bool} -- Display transactions and details (default: {True})
        only_ids {bool} -- Display ids only no details (default: {False})
    """
    # todo display entities properly
    accounts = []
    transactions = []
    store = banking_app.ledger.store
    if show_accounts:
        typer.echo(typer.style("\nAccounts", fg=typer.colors.MAGENTA))
        typer.echo(typer.style("===========", fg=typer.colors.MAGENTA))
        accounts += store["accounts"].keys() if only_ids else banking_app.all_accounts()
        accounts = accounts or ["-----No open account---"]
        typer.echo(
            "\n".join(
                typer.style(str(acc), fg=typer.colors.BRIGHT_BLUE) for acc in accounts
            )
        )
    if show_transactions:
        typer.echo(typer.style("\nTransactions", fg=typer.colors.MAGENTA))
        typer.echo(typer.style("===========", fg=typer.colors.MAGENTA))
        transactions += (
            store["transactions"].keys() if only_ids else banking_app.all_transactions()
        )
        transactions = transactions or ["-----No transaction----"]
        typer.echo(
            "\n".join(
                typer.style(str(transaction), fg=typer.colors.BRIGHT_BLUE)
                for transaction in transactions
            )
        )


@app.command()
def show(entity_id: str):
    try:
        uid: UUID = UUID(entity_id)
        if uid in banking_app.ledger.store["accounts"]:
            typer.echo(typer.style("Account", fg=typer.colors.MAGENTA))
            typer.echo(typer.style("=========", fg=typer.colors.MAGENTA))
            typer.echo(
                typer.style(
                    str(banking_app.get_account_details(uid)),
                    fg=typer.colors.BRIGHT_BLUE,
                )
            )
            typer.Exit()
        elif uid in banking_app.ledger.store["transactions"]:
            typer.echo(typer.style("Transaction", fg=typer.colors.MAGENTA))
            typer.echo(typer.style("=========", fg=typer.colors.MAGENTA))
            typer.echo(
                typer.style(
                    str(banking_app.ledger.store["transactions"][uid].to_dict()),
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
@set_occuring_on
def close(account_id: str, date: str = None):
    """Close account

    Arguments:
        account_id {str} -- Id of account to close
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
