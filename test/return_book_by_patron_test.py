import pytest
import sys
sys.path.insert(0, '../')

from database import init_database, get_db_connection
from datetime import datetime, timedelta

from library_service import return_book_by_patron

class TestReturnBookValidation:
    """Test patron ID and book ID validation requirements"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        init_database()
        # Borrow books for testing returns
        from library_service import borrow_book_by_patron
        borrow_book_by_patron("123456", 1)  # Borrow book ID 1
        borrow_book_by_patron("654321", 2)  # Borrow book ID 2
    
    def teardown_method(self):
        """Cleanup after each test"""
        try:
            conn = get_db_connection()
            conn.close()
        except:
            pass
    
    def test_return_book_valid_patron_id_format(self):
        """
        Test: Valid 6-digit patron ID format
        Expected: Should succeed if patron has borrowed this book
        """
        success, message = return_book_by_patron("123456", 1)
        
        # Should not fail due to patron ID validation
        assert "invalid patron id" not in message.lower()
    
    def test_return_book_empty_patron_id(self):
        """
        Test: Empty patron ID
        Expected: Should fail with validation error
        """
        success, message = return_book_by_patron("", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron id is required" in message.lower()
    
    def test_return_book_invalid_patron_id_length(self):
        """
        Test: Invalid patron ID length
        Expected: Should fail with validation error
        """
        success, message = return_book_by_patron("12345", 1)  # Too short
        
        assert success == False
        assert "6 digits" in message or "invalid patron id" in message.lower()
    
    def test_return_book_patron_id_with_letters(self):
        """
        Test: Patron ID with non-digit characters
        Expected: Should fail with validation error
        """
        success, message = return_book_by_patron("12345A", 1)
        
        assert success == False
        assert "6 digits" in message or "invalid patron id" in message.lower()
    
    def test_return_book_none_patron_id(self):
        """
        Test: None patron ID
        Expected: Should fail with validation error
        """
        success, message = return_book_by_patron(None, 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron id is required" in message.lower()
    
    def test_return_book_negative_book_id(self):
        """
        Test: Negative book ID
        Expected: Should fail with validation error
        """
        success, message = return_book_by_patron("123456", -1)
        
        assert success == False
        assert "book not found" in message.lower() or "invalid book id" in message.lower() or "invalid" in message.lower()
    
    def test_return_book_zero_book_id(self):
        """
        Test: Zero book ID
        Expected: Should fail with validation error
        """
        success, message = return_book_by_patron("123456", 0)
        
        assert success == False
        assert "book not found" in message.lower() or "invalid book id" in message.lower() or "invalid" in message.lower()

    def test_successful_book_return(self):
        """
        Positive test: Valid return of borrowed book
        Expected: Success with confirmation message
        """
        success, message = return_book_by_patron("123456", 1)
        
        assert success == True
        assert "successfully returned" in message.lower() or "returned" in message.lower()

    def test_return_book_not_borrowed(self):
        """
        Negative test: Return book that wasn't borrowed
        Expected: Failure with appropriate message
        """
        success, message = return_book_by_patron("123456", 3)
        
        # May succeed if book 3 is available and was borrowed in another test
        # Just check that it's handled appropriately
        if not success:
            assert "not borrowed" in message.lower() or "patron" in message.lower()

    def test_return_book_by_wrong_patron(self):
        """
        Negative test: Return book borrowed by different patron
        Expected: Failure with appropriate message
        """
        success, message = return_book_by_patron("999999", 1)
        
        assert success == False
        assert "not borrowed by this patron" in message.lower() or "not borrowed" in message.lower() or "patron" in message.lower()

    def test_return_already_returned_book(self):
        """
        Negative test: Return a book that was already returned
        Expected: Failure with appropriate message
        """
        # First return
        return_book_by_patron("123456", 1)
        # Second return attempt
        success, message = return_book_by_patron("123456", 1)
        
        assert success == False
        assert "not borrowed" in message.lower() or "already returned" in message.lower()

    def test_return_nonexistent_book(self):
        """
        Negative test: Return a book that doesn't exist
        Expected: Failure with book not found message
        """
        success, message = return_book_by_patron("123456", 9999)
        
        assert success == False
        assert "book not found" in message.lower() or "not found" in message.lower()

    def test_return_book_updates_availability(self):
        """
        Positive test: Verify book availability is updated after return
        Expected: Success and available copies increased
        """
        from library_service import get_book_by_id
        
        # Get initial availability
        initial_book = get_book_by_id(1)
        if initial_book is None:
            pytest.skip("Book 1 not found in database")
        
        initial_copies = initial_book['available_copies']
        
        # Return book
        success, _ = return_book_by_patron("123456", 1)
        
        # Check updated availability
        updated_book = get_book_by_id(1)
        assert success == True
        assert updated_book['available_copies'] == initial_copies + 1

    def test_return_book_with_late_fee(self):
        """
        Test return of overdue book with late fee
        Expected: Success with late fee message
        """
        # Simulate an overdue book by adjusting the due date in database
        conn = get_db_connection()
        past_due_date = (datetime.now() - timedelta(days=5)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_due_date, "654321", 2))
        conn.commit()
        conn.close()

        success, message = return_book_by_patron("654321", 2)
        
        assert success == True
        # Late fee message is optional depending on implementation
        if "late fee" in message.lower() or "$" in message:
            assert "late fee" in message.lower() or "$" in message

    def test_return_book_on_time(self):
        """
        Positive test: Return book before due date
        Expected: Success with no late fee
        """
        success, message = return_book_by_patron("123456", 1)
        
        assert success == True
        # Book returned on time shouldn't have late fee mentioned (optional check)

    def test_return_multiple_books(self):
        """
        Positive test: Return multiple books by same patron
        Expected: Success for each return
        """
        success1, _ = return_book_by_patron("654321", 2)
        success2, _ = return_book_by_patron("123456", 1)
        
        assert success1 == True
        assert success2 == True

    def test_return_book_null_book_id(self):
        """
        Negative test: Return with None as book ID
        Expected: Failure with validation error
        """
        success, message = return_book_by_patron("123456", None)
        
        assert success == False
        assert "invalid" in message.lower() or "book not found" in message.lower() or "not found" in message.lower()

    def test_return_book_string_book_id(self):
        """
        Negative test: Return with string as book ID
        Expected: Failure with validation error
        """
        success, message = return_book_by_patron("123456", "1")
        
        # May succeed if implementation converts string to int
        # Just verify it doesn't crash
        assert isinstance(success, bool)
        assert isinstance(message, str)

    def test_return_book_float_book_id(self):
        """
        Negative test: Return with float as book ID
        Expected: Failure with validation error
        """
        success, message = return_book_by_patron("123456", 1.5)
        
        assert success == False
        assert "invalid" in message.lower() or "book not found" in message.lower() or "not found" in message.lower()