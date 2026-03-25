import unittest
from unittest.mock import patch
import io
import sys

# Assuming the modernized code (_validate_account, _get_balance, _update_balance, _record_audit, process_transaction)
# is available in the current scope or imported from a module like 'transaction_processor'
# For this example, we'll assume it's in the same scope as the tests.

# --- Modernized Code (for context within the test file, normally imported) ---
def _validate_account(account_id: str) -> bool:
    return account_id is not None and len(account_id) == 10

def _get_balance(account_id: str) -> float:
    return 500.00

def _update_balance(account_id: str, new_balance: float) -> None:
    print(f"Updating balance for {account_id} to {new_balance}")

def _record_audit(account_id: str, amount: float) -> None:
    print(f"Audit: Deducted {amount} from {account_id}")

def process_transaction(account_id: str, amount: float) -> bool:
    if not _validate_account(account_id):
        return False

    current_balance = _get_balance(account_id)
    if current_balance < amount:
        print("Insufficient funds!")
        return False

    _update_balance(account_id, current_balance - amount)
    _record_audit(account_id, amount)

    return True
# ---------------------------------------------------------------------------

class TestProcessTransaction(unittest.TestCase):

    def setUp(self):
        # Redirect stdout to capture print statements for assertion
        self.held_stdout = sys.stdout
        self.mock_stdout = io.StringIO()
        sys.stdout = self.mock_stdout

    def tearDown(self):
        # Restore stdout after each test
        sys.stdout = self.held_stdout

    @patch('__main__._validate_account')
    @patch('__main__._get_balance')
    @patch('__main__._update_balance')
    @patch('__main__._record_audit')
    def test_process_transaction_invalid_account(self, mock_record_audit, mock_update_balance, mock_get_balance, mock_validate_account):
        # Arrange
        mock_validate_account.return_value = False
        account_id = "INVALID123"
        amount = 100.0

        # Act
        result = process_transaction(account_id, amount)

        # Assert
        self.assertFalse(result)
        mock_validate_account.assert_called_once_with(account_id)
        mock_get_balance.assert_not_called()
        mock_update_balance.assert_not_called()
        mock_record_audit.assert_not_called()
        self.assertEqual(self.mock_stdout.getvalue(), "") # No print output from process_transaction itself

    @patch('__main__._validate_account')
    @patch('__main__._get_balance')
    @patch('__main__._update_balance')
    @patch('__main__._record_audit')
    def test_process_transaction_insufficient_funds(self, mock_record_audit, mock_update_balance, mock_get_balance, mock_validate_account):
        # Arrange
        mock_validate_account.return_value = True
        mock_get_balance.return_value = 50.0 # Current balance is less than amount
        account_id = "ACCOUNT123"
        amount = 100.0

        # Act
        result = process_transaction(account_id, amount)

        # Assert
        self.assertFalse(result)
        mock_validate_account.assert_called_once_with(account_id)
        mock_get_balance.assert_called_once_with(account_id)
        mock_update_balance.assert_not_called()
        mock_record_audit.assert_not_called()
        self.assertEqual(self.mock_stdout.getvalue(), "Insufficient funds!\n")

    @patch('__main__._validate_account')
    @patch('__main__._get_balance')
    @patch('__main__._update_balance')
    @patch('__main__._record_audit')
    def test_process_transaction_success(self, mock_record_audit, mock_update_balance, mock_get_balance, mock_validate_account):
        # Arrange
        mock_validate_account.return_value = True
        mock_get_balance.return_value = 500.0
        account_id = "ACCOUNT123"
        amount = 100.0
        expected_new_balance = 400.0

        # Act
        result = process_transaction(account_id, amount)

        # Assert
        self.assertTrue(result)
        mock_validate_account.assert_called_once_with(account_id)
        mock_get_balance.assert_called_once_with(account_id)
        mock_update_balance.assert_called_once_with(account_id, expected_new_balance)
        mock_record_audit.assert_called_once_with(account_id, amount)
        self.assertEqual(self.mock_stdout.getvalue(), "") # No print output from process_transaction itself

    @patch('__main__._validate_account')
    @patch('__main__._get_balance')
    @patch('__main__._update_balance')
    @patch('__main__._record_audit')
    def test_process_transaction_zero_amount(self, mock_record_audit, mock_update_balance, mock_get_balance, mock_validate_account):
        # Arrange
        mock_validate_account.return_value = True
        mock_get_balance.return_value = 500.0
        account_id = "ACCOUNT123"
        amount = 0.0
        expected_new_balance = 500.0 # Balance should not change

        # Act
        result = process_transaction(account_id, amount)

        # Assert
        self.assertTrue(result)
        mock_validate_account.assert_called_once_with(account_id)
        mock_get_balance.assert_called_once_with(account_id)
        mock_update_balance.assert_called_once_with(account_id, expected_new_balance)
        mock_record_audit.assert_called_once_with(account_id, amount)
        self.assertEqual(self.mock_stdout.getvalue(), "")

    @patch('__main__._validate_account')
    @patch('__main__._get_balance')
    @patch('__main__._update_balance')
    @patch('__main__._record_audit')
    def test_process_transaction_amount_equals_balance(self, mock_record_audit, mock_update_balance, mock_get_balance, mock_validate_account):
        # Arrange
        mock_validate_account.return_value = True
        mock_get_balance.return_value = 500.0
        account_id = "ACCOUNT123"
        amount = 500.0
        expected_new_balance = 0.0

        # Act
        result = process_transaction(account_id, amount)

        # Assert
        self.assertTrue(result)
        mock_validate_account.assert_called_once_with(account_id)
        mock_get_balance.assert_called_once_with(account_id)
        mock_update_balance.assert_called_once_with(account_id, expected_new_balance)
        mock_record_audit.assert_called_once_with(account_id, amount)
        self.assertEqual(self.mock_stdout.getvalue(), "")

    @patch('__main__._validate_account')
    @patch('__main__._get_balance')
    @patch('__main__._update_balance')
    @patch('__main__._record_audit')
    def test_process_transaction_negative_amount_as_deposit(self, mock_record_audit, mock_update_balance, mock_get_balance, mock_validate_account):
        # Arrange
        # The original Java logic implicitly allows negative amounts to increase balance.
        # This test verifies that behavior.
        mock_validate_account.return_value = True
        mock_get_balance.return_value = 500.0
        account_id = "ACCOUNT123"
        amount = -100.0 # A negative amount, effectively a deposit
        expected_new_balance = 600.0 # 500 - (-100) = 600

        # Act
        result = process_transaction(account_id, amount)

        # Assert
        self.assertTrue(result)
        mock_validate_account.assert_called_once_with(account_id)
        mock_get_balance.assert_called_once_with(account_id)
        mock_update_balance.assert_called_once_with(account_id, expected_new_balance)
        mock_record_audit.assert_called_once_with(account_id, amount)
        self.assertEqual(self.mock_stdout.getvalue(), "")

# To run the tests, uncomment the following block:
# if __name__ == '__main__':
#     unittest.main()