from typer.testing import CliRunner

from banking.main import app

runner = CliRunner()


def test_open_command():
    result = runner.invoke(app, ["open", "covid"])
    assert result.exit_code == 0
    assert "Account successfully created" in result.stdout


def test_withdraw_command():
    result = runner.invoke(app, ["withdraw", "", 45.37])
    pass


def test_ls_command_with_defaults():
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "Accounts" in result.stdout
    assert "Transactions" in result.stdout


def test_ls_command_no_accounts():
    result = runner.invoke(app, ["ls", "--no-show-accounts"])
    assert result.exit_code == 0
    assert "Accounts" not in result.stdout
    assert "Transactions" in result.stdout


def test_ls_command_no_transactions():
    result = runner.invoke(app, ["ls", "--no-show-transactions"])
    assert result.exit_code == 0
    assert "Accounts" in result.stdout
    assert "Transactions" not in result.stdout


def test_ls_command_only_ids():
    result = runner.invoke(app, ["ls", "--only-ids"])
    assert result.exit_code == 0
    assert "Accounts" not in result.stdout
    assert "Transactions" not in result.stdout
    assert "Account Ids" in result.stdout
    assert "Transaction Ids" in result.stdout


def test_show_command():
    pass
