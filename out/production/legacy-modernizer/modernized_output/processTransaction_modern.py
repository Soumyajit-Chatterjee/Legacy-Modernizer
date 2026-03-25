def _validate_account(account_id: str) -> bool:
    """
    Validates if an account ID is not None and has a length of 10.
    """
    return account_id is not None and len(account_id) == 10

def _get_balance(account_id: str) -> float:
    """
    Retrieves the current balance for a given account ID.
    (Mock implementation from legacy code)
    """
    # In a real application, this would fetch data from a database or external service.
    return 500.00

def _update_balance(account_id: str, new_balance: float) -> None:
    """
    Updates the balance for a given account ID.
    (Mock implementation from legacy code)
    """
    # In a real application, this would persist data to a database or external service.
    print(f"Updating balance for {account_id} to {new_balance}")

def _record_audit(account_id: str, amount: float) -> None:
    """
    Records an audit entry for a transaction.
    (Mock implementation from legacy code)
    """
    # In a real application, this would write to an audit log or a dedicated audit service.
    print(f"Audit: Deducted {amount} from {account_id}")

def process_transaction(account_id: str, amount: float) -> bool:
    """
    Processes a financial transaction by deducting an amount from an account.

    Args:
        account_id: The ID of the account to process the transaction for.
        amount: The amount to deduct from the account.

    Returns:
        True if the transaction was successful, False otherwise.
    """
    if not _validate_account(account_id):
        return False

    current_balance = _get_balance(account_id)
    if current_balance < amount:
        print("Insufficient funds!")
        return False

    _update_balance(account_id, current_balance - amount)
    _record_audit(account_id, amount)

    return True