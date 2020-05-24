class AccountError(Exception):
    """Base class for all account errors"""


class InsufficientFundError(AccountError):
    pass


class ClosingCompanyAccountError(AccountError):
    pass

class DailyWithdrawalAmountLimitExceededError(AccountError):
    pass

class AccountClosedError(AccountError):
    """
    Raised when trying to perfom action on a closed account.
    Should probably never be raised since closed account would
    be deleted
    """
    pass

class ATMWithdrawalNotAllowedError(AccountError):
    pass

class AccountNotFoundError(AccountError):
    pass