class AccountError(Exception):
    """Base class for all account errors"""


class InsufficientFundError(AccountError):
    pass


class ClosingCompanyAccountError(AccountError):
    pass

class DailyWithdrawalAmountLimitExceededError(AccountError):
    pass