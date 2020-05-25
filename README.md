# Banking

`Banking` is a simple CLI application that allows bank employees to open accounts
of various types, deposit funds into these accounts, withdraw from the accounts
and also close the accounts.

To Get Started. Run `make install` on a terminal in a virtual environment (Recommended)

Run: `banking --help`

Test: `make test`

## Transaction

A transcton is an object that encapsulates the details of a monetary action performed
on an account. The two types of transactions supported are `CREDIT` and `DEBIT`

## BankAccount

Bank accounts are the main entities in this domain on which actions are performed on.
The 3 bank account types supported by this application are:
* `international` -> `BankAcount_INT`
* `covid` -> `BankAccount_Covid19`
* `company` -> `BankAccount_Covid19_Company`

A bank account has the following methods:

### Withdraw
The withdraw method on the bankaccount validates and verifies if the withdrawal
should be allowed or not based on the kind of account and the date the withdrawal
is taking place.

The withdrawal method debits the account by creating a transaction of type `DEBIT` with
the debit amount specified.

Withdrawal restrictions of `1, 000 PLN` maximum daily and `No ATM` apply to all account types from `April 1, 2020` except for the `international` bank account.

### Deposit
The deposit method credits the bank account by creating a transaction of type `CREDIT` with the specified amount. 

The deposit methods on `company` accounts ensures the very first deposit transacion on that company account
must be greater or equals to `5, 000 PLN` which is the non-returnable government loan. Subsequent deposits
can be of any amount.

### Close
The close method uses the current account balance and fires the `withdraw` method if the current account balance is greater than 0. Therefore withdrwal restrictions apply to closing non-foreign accounts.

Company accounts cannot be closed.

## Ledger
The Ledger class is responsible for storing and retriving all `accounts` and `transactions`. It is also responsible for constructing an computing an accounts current state from all of the accounts previous CREDIT and DEBIT transactions.

The ledger is also responsible for deleting an account when it is closed.

`NOTE`: When an account is closed and deleted, it's transactions are left intact for reference purposes.

#### Ledger Implementation
The ledger stores accounts and transactions in two `OrderedDicts` one for each with the key of the OrderedDicts being the accountId and transactionId.

The `value` for the accounts OrderedDict is the `class` the account belongs to i.e one of `BankAccount_INT`, `BankAccount_Covid19` or `BankAccount_Covid19_Company`. The ledger uses the accounts transactions to get the current state of the account and therefore it does not need to store the entire account object.

The `value` for the transactions OrderedDict is the transaction object itself as is.

## Application

The application sits on the domain models [`BankAccount` and `Transaction`] and attaches persistence to them. It provides services methods with a similar API to that of the `BankAccount`. These service methods are the use cases of the banking application.

It is reponsible for persisting new accounts and transactions in the ledger.


## CLI
The CLI primarily uses the `Application` services methods. It accepts inputs from the command line, parses them and feeds them to the `Application Service Methods` handles the application errors and displays the results back to users.

The CLI app has 6 commands:

* `open` -> To open a new bank account.
* `deposit` -> To deposit funds into an account.
* `withdraw` -> To withdraw funds from an account.
* `close` -> To close a specific account.
* `ls` -> To list and display all accounts and/or transactions
* `show` -> To display details of a single account or transaction

For a complete guide on how to use this commands, run.

`$ banking [command] --help`

Example:

`$ banking open --help`
   