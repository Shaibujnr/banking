import typer
from uuid import UUID
from banking.application import Application
from banking.error import AccountError, DailyWithdrawalAmountLimitExceededError, InsufficientFundError, OpenAccountError

banking_app: Application = Application("ledger.pkl")
banking_app.start()

app = typer.Typer()


@app.command()
def open(account_type: str, amount: float = typer.Argument(0, min=0)):
    """Open an account. Some accounts type usually require a minimum amount deposit
    to be successfully opened. In this case, company accounts require a minimum initial
    deposit of 5000.

    Arguments:
        account_type {str} -- One of either 'international', 'covid' or 'company'

    Keyword Arguments:
        amount {float} -- Initial deposit (default: {typer.Argument(0, min=0)})
    """
    try:
        account_id = banking_app.open_account(account_type, amount) #type: ignore
        typer.secho(f"{account_type} Account successfully created, Here's the account id {account_id}")
    except OpenAccountError:
        typer.echo("Company acounts must be opened with an initial deposit of at least 5000")
        typer.Abort()


@app.command()
def withdraw(account_id: str, amount: float, atm: bool = False):
    """Withdraw from an account

    Arguments:
        account_id {str} -- Id of account to be debited
        amount {float} -- Amount to withdraw from account

    Keyword Arguments:
        atm {bool} -- Is this an atm withdrawal? (default: {False})
    """
    #todo ATM withdrawals were no longer allowed as from April 1, 2020
    try:
        transaction_id = banking_app.withdraw(UUID(account_id), amount, atm)
        typer.echo(f"Withdrawal successful, transaction id is {transaction_id}")
    except AccountError as e:
        typer.echo(str(e))


@app.command()
def deposit(account_id: str, amount: float):
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
    #todo refactor method, rewrite documentation for all commands
    #todo display transactions properly
    accounts = []
    transactions = []
    if only_ids:
        if show_accounts:
            accounts += banking_app.ledger.store["accounts"].keys()
            typer.echo("\nAccounts")
            typer.echo("===========")
            typer.echo("\n".join(str(acc) for acc in accounts))
        if show_transactions:
            transactions += banking_app.ledger.store["transactions"].keys()
            typer.echo("\nTransactions")
            typer.echo("===========")
            typer.echo("\n".join(str(transaction) for transaction in transactions))
    else:
        if show_accounts:
            accounts += banking_app.all_accounts()
            typer.echo("Accounts")
            typer.echo("===========\n\n")
            typer.echo(accounts)
        if show_transactions:
            transactions += banking_app.ledger.store["transactions"].values()
            typer.echo("Transactions")
            typer.echo("===========\n\n")
            typer.echo(transactions)


@app.command()
def close(account_id: str):
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