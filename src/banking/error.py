class AccountError(Exception):
    """Base class for all account errors"""


class InsufficientFundError(AccountError):
    """Raised when trying to withdrw more than available balance"""


class ClosingCompanyAccountError(AccountError):
    """Raised when trying to close a company account"""


class DailyWithdrawalLimitError(AccountError):
    """Raised when trying to exceed the daily withdrawal limit set 
    on non-foreign accounts"""


class ATMWithdrawalNotAllowedError(AccountError):
    """Raised when trying to withdraw from non-foreign accounts 
    via atm after restriction date"""


class AccountNotFoundError(AccountError):
    """Raised when trying to perform action a non-existing or deleted account
    """
