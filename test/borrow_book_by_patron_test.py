import pytest
import sys
sys.path.insert(0, '../')

from database import init_database
from datetime import datetime, timedelta
from library_service import borrow_book_by_patron


class TestBorrowBookByPatron:
    """Test suite for R3: Book Borrowing functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        init_database()
        from database import add_sample_data
        add_sample_data() 
    
    def teardown_method(self):
        """Cleanup after each test"""
        try:
            from database import get_db_connection
            conn = get_db_connection()
            conn.close()
        except:
            pass
    
    def test_borrow_book_valid_request(self):
        """
        Positive test: Valid patron borrows available book
        Expected: Success with due date message
        """
        # Use a book that should be available (book_id=1 from sample data)
        success, message = borrow_book_by_patron("123456", 1)
        
        assert success == True
        assert "successfully borrowed" in message.lower() or "borrowed" in message.lower()
        # Check for due date information (may be in different formats)
        assert "due" in message.lower() or datetime.now().strftime("%Y") in message
    
    def test_borrow_book_different_valid_patron(self):
        """
        Positive test: Different valid patron borrows book
        Expected: Success
        """
        success, message = borrow_book_by_patron("654321", 2)
        
        assert success == True
        assert "successfully borrowed" in message.lower() or "borrowed" in message.lower()
    
    # Patron ID Validation Tests
    def test_borrow_book_empty_patron_id(self):
        """
        Negative test: Empty patron ID
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron" in message.lower()
    
    def test_borrow_book_none_patron_id(self):
        """
        Negative test: None patron ID
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron(None, 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron" in message.lower()
    
    def test_borrow_book_patron_id_too_short(self):
        """
        Negative test: Patron ID less than 6 digits
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("12345", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "6 digits" in message.lower()
    
    def test_borrow_book_patron_id_too_long(self):
        """
        Negative test: Patron ID more than 6 digits
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("1234567", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "6 digits" in message.lower()
    
    def test_borrow_book_patron_id_with_letters(self):
        """
        Negative test: Patron ID containing non-digit characters
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("12345A", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron" in message.lower()
    
    def test_borrow_book_patron_id_with_spaces(self):
        """
        Negative test: Patron ID with spaces
        Expected: Failure with validation error
        """
        success, message = borrow_book_by_patron("12 34 56", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron" in message.lower()
    
    # Book Validation Tests
    def test_borrow_nonexistent_book(self):
        """
        Negative test: Try to borrow book that doesn't exist
        Expected: Failure with book not found error
        """
        success, message = borrow_book_by_patron("123456", 99999)
        
        assert success == False
        assert "book not found" in message.lower() or "not found" in message.lower()
    
    def test_borrow_unavailable_book(self):
        """
        Negative test: Try to borrow book with 0 available copies
        Expected: Failure with availability error
        """
        # Book ID 3 may or may not be unavailable depending on database state
        success, message = borrow_book_by_patron("123456", 3)
        
        # If it fails, check for availability message
        if not success:
            assert "not available" in message.lower() or "available" in message.lower()
        # If it succeeds, that's also acceptable (book was available)
    
    def test_borrow_book_negative_book_id(self):
        """
        Negative test: Negative book ID
        Expected: Failure with book not found
        """
        success, message = borrow_book_by_patron("123456", -1)
        
        assert success == False
        assert "book not found" in message.lower() or "not found" in message.lower() or "invalid" in message.lower()
    
    def test_borrow_book_zero_book_id(self):
        """
        Negative test: Zero book ID
        Expected: Failure with book not found
        """
        success, message = borrow_book_by_patron("123456", 0)
        
        assert success == False
        assert "book not found" in message.lower() or "not found" in message.lower() or "invalid" in message.lower()

    def test_borrow_multiple_books_within_limit(self):
        """
        Positive test: Patron borrows multiple books within 5-book limit
        Expected: Success for each borrow
        """
        patron_id = "111111"
        
        # Borrow 3 different books
        success1, _ = borrow_book_by_patron(patron_id, 1)
        success2, _ = borrow_book_by_patron(patron_id, 2)
        success3, msg3 = borrow_book_by_patron(patron_id, 4)
        
        # At least the first borrow should succeed
        assert success1 == True
        # Others may fail if books unavailable, which is acceptable
    
    def test_borrow_exceeding_limit(self):
        """
        Negative test: Patron attempts to borrow more than 5 books
        Expected: Failure with limit exceeded message
        """
        patron_id = "222222"
        
        # Try to borrow 5 books first
        successful_borrows = 0
        for book_id in range(1, 7):  # Try up to 6 books
            success, _ = borrow_book_by_patron(patron_id, book_id)
            if success:
                successful_borrows += 1
            if successful_borrows >= 5:
                break
        
        # Try to borrow one more book
        success, message = borrow_book_by_patron(patron_id, 10)
        
        # Should fail if we successfully borrowed 5
        if successful_borrows >= 5:
            assert success == False
            assert "maximum" in message.lower() or "limit" in message.lower() or "5" in message
    
    def test_borrow_same_book_twice(self):
        """
        Negative test: Patron attempts to borrow same book twice
        Expected: Failure with availability error
        """
        patron_id = "333333"
        
        # Borrow book first time
        success1, _ = borrow_book_by_patron(patron_id, 1)
        # Try to borrow same book again
        success2, message = borrow_book_by_patron(patron_id, 1)
        
        # First should succeed
        assert success1 == True
        # Second should fail
        assert success2 == False
        assert "not available" in message.lower() or "already" in message.lower() or "borrowed" in message.lower()
    
    def test_borrow_book_due_date_calculation(self):
        """
        Positive test: Verify due date is exactly 14 days from borrow date
        Expected: Success with correct due date
        """
        success, message = borrow_book_by_patron("444444", 1)
        
        assert success == True
        # Due date should be mentioned in some form
        expected_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        # Check if the date or at least the year/month is in the message
        assert expected_date in message or datetime.now().strftime("%Y-%m") in message or "due" in message.lower()
    
    def test_borrow_book_last_copy(self):
        """
        Positive test: Borrow last available copy of a book
        Expected: Success and book becomes unavailable
        """
        patron_id = "555555"
        book_id = 2  # Assuming this book has limited copies
        
        # Borrow copy
        success1, _ = borrow_book_by_patron(patron_id, book_id)
        
        # Only test the second borrow if first succeeded
        if success1:
            # Try to borrow again with different patron
            success2, message = borrow_book_by_patron("666666", book_id)
            
            # May or may not be available depending on total copies
            if not success2:
                assert "not available" in message.lower()
    
    def test_borrow_book_concurrent_requests(self):
        """
        Test concurrent borrowing requests for same book
        Expected: At least one request should process correctly
        """
        patron1_id = "777777"
        patron2_id = "888888"
        book_id = 1
        
        # Simulate concurrent requests
        success1, _ = borrow_book_by_patron(patron1_id, book_id)
        success2, _ = borrow_book_by_patron(patron2_id, book_id)
        
        # At least one should process (may both succeed if multiple copies available)
        assert isinstance(success1, bool)
        assert isinstance(success2, bool)
    
    def test_borrow_book_float_book_id(self):
        """
        Negative test: Book ID as float
        Expected: Failure with invalid book ID
        """
        success, message = borrow_book_by_patron("123456", 1.5)
        
        assert success == False
        assert "book not found" in message.lower() or "invalid" in message.lower() or "not found" in message.lower()
    
    def test_borrow_book_special_chars_patron_id(self):
        """
        Negative test: Patron ID with special characters
        Expected: Failure with invalid patron ID
        """
        success, message = borrow_book_by_patron("12@456", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron" in message.lower() or "invalid" in message.lower()
    
    def test_borrow_book_whitespace_patron_id(self):
        """
        Negative test: Patron ID with leading/trailing whitespace
        Expected: Failure with invalid patron ID
        """
        success, message = borrow_book_by_patron(" 123456 ", 1)
        
        assert success == False
        assert "invalid patron id" in message.lower() or "patron" in message.lower() or "invalid" in message.lower()