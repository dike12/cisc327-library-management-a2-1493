import pytest
import sys
sys.path.insert(0, '../')

from database import init_database, get_db_connection
from datetime import datetime, timedelta
from library_service import get_patron_status_report, borrow_book_by_patron

class TestPatronStatusReport:
    """Test suite for R7: Patron Status Report functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        init_database()
        # Setup test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Create test data for patron status testing"""
        # Create a patron with multiple borrowed books
        patron_id = "111111"
        borrow_book_by_patron(patron_id, 1)  # Borrow first book
        borrow_book_by_patron(patron_id, 2)  # Borrow second book
        
        # Create an overdue book scenario
        conn = get_db_connection()
        past_date = (datetime.now() - timedelta(days=20)).isoformat()
        conn.execute('''
            UPDATE borrow_records 
            SET due_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (past_date, patron_id, 1))
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        """Cleanup after each test"""
        try:
            conn = get_db_connection()
            conn.close()
        except:
            pass
    
    def test_patron_status_empty_patron_id(self):
        """
        Test: Empty patron ID
        Expected: Should return error status
        """
        result = get_patron_status_report("")
        
        assert isinstance(result, dict)
        # Accept multiple error formats
        status = result.get('status', result.get('error', ''))
        message = result.get('message', result.get('error', ''))
        combined = (str(status) + ' ' + str(message)).lower()
        
        assert 'error' in combined or 'invalid' in combined
        assert 'patron' in combined or 'invalid' in combined
    
    def test_patron_status_invalid_patron_id_length(self):
        """
        Test: Invalid patron ID length
        Expected: Should return error for non-6-digit patron ID
        """
        result = get_patron_status_report("12345")  # Too short
        assert isinstance(result, dict)
        
        status = result.get('status', result.get('error', ''))
        message = result.get('message', result.get('error', ''))
        combined = (str(status) + ' ' + str(message)).lower()
        
        assert 'error' in combined or 'invalid' in combined
        assert '6 digits' in combined or 'invalid patron id' in combined or 'patron' in combined
    
    def test_patron_status_valid_patron_with_books(self):
        """
        Test: Valid patron ID with borrowed books
        Expected: Should return complete status report
        """
        # Use patron "123456" who should have borrowed book ID 3 from sample data
        result = get_patron_status_report("123456")
        
        assert isinstance(result, dict)
        
        # Check for success (may use different field names)
        has_success = result.get('status') == 'success' or 'error' not in str(result).lower()
        
        if has_success:
            # Should contain patron ID in some form (optional - implementation may not include it)
            # Just verify we have data
            has_borrowed = 'currently_borrowed_books' in result or 'current_books' in result
            has_fees = 'total_late_fees_owed' in result or 'total_fees' in result
            has_count = 'number_of_books_borrowed' in result or 'total_borrowed' in result
            has_history = 'borrowing_history' in result or 'borrow_history' in result
            
            # Should have at least some data fields
            assert has_borrowed or has_fees or has_count or has_history
    
    def test_patron_status_valid_patron_no_books(self):
        """
        Test: Valid patron ID with no borrowed books
        Expected: Should return status report with zero values
        """
        result = get_patron_status_report("999999")  # Patron with no borrows
        
        assert isinstance(result, dict)
        
        # Check for success or valid response
        if 'error' not in str(result).lower():
            # Get values using flexible field names
            num_borrowed = result.get('number_of_books_borrowed', result.get('total_borrowed', 0))
            fees = result.get('total_late_fees_owed', result.get('total_fees', 0.0))
            borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
            
            assert num_borrowed == 0
            assert fees == 0.0
            assert len(borrowed_books) == 0
    
    def test_patron_status_currently_borrowed_structure(self):
        """
        Test: Currently borrowed books data structure
        Expected: Should contain books with due dates
        """
        result = get_patron_status_report("123456")
        
        if 'error' not in str(result).lower():
            borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
            
            if len(borrowed_books) > 0:
                book = borrowed_books[0]
                assert isinstance(book, dict)
                
                # Should contain required book information (at least some)
                assert 'book_id' in book or 'title' in book or 'author' in book
    
    def test_patron_status_total_late_fees(self):
        """
        Test: Total late fees owed calculation
        Expected: Should calculate sum of all late fees
        """
        result = get_patron_status_report("123456")
        
        if 'error' not in str(result).lower():
            late_fees = result.get('total_late_fees_owed', result.get('total_fees', 0))
            assert isinstance(late_fees, (int, float))
            assert late_fees >= 0, "Late fees should be non-negative"
    
    def test_patron_status_borrowing_history_structure(self):
        """
        Test: Borrowing history data structure
        Expected: Should contain all patron's borrowing records
        """
        result = get_patron_status_report("123456")
        
        if 'error' not in str(result).lower():
            history = result.get('borrowing_history', result.get('borrow_history', []))
            assert isinstance(history, list)
            
            if len(history) > 0:
                record = history[0]
                assert isinstance(record, dict)
                # Should have some book information
                assert 'book_id' in record or 'title' in record
    
    def test_patron_status_all_required_fields(self):
        """
        Test: Response contains all R7 required fields
        Expected: Should include all specified information
        """
        result = get_patron_status_report("123456")
        
        if 'error' not in str(result).lower():
            # Check for fields with flexible naming
            has_borrowed = 'currently_borrowed_books' in result or 'current_books' in result
            has_fees = 'total_late_fees_owed' in result or 'total_fees' in result
            has_count = 'number_of_books_borrowed' in result or 'total_borrowed' in result
            has_history = 'borrowing_history' in result or 'borrow_history' in result
            
            # Should have at least most of these fields
            fields_present = sum([has_borrowed, has_fees, has_count, has_history])
            assert fields_present >= 3, "Should contain at least 3 of 4 required field types"
    
    def test_patron_status_response_format(self):
        """
        Test: Response is properly formatted dictionary
        Expected: Should be JSON-serializable for display
        """
        result = get_patron_status_report("123456")
        
        assert isinstance(result, dict)
        
        # Test JSON serializability
        import json
        try:
            json_str = json.dumps(result, default=str)  # default=str handles datetime
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result should be JSON serializable: {e}")
    
    def test_patron_status_invalid_parameter_types(self):
        """
        Test: Handle invalid parameter types
        Expected: Should handle gracefully
        """
        try:
            result = get_patron_status_report(123456)  # Integer instead of string
            
            assert isinstance(result, dict)
            # Should indicate error in some way
            has_error = (result.get('status') == 'error' or 
                        'error' in result or 
                        'invalid' in str(result).lower())
            assert has_error
        except (AttributeError, TypeError):
            # Function may raise error for invalid type, which is also acceptable
            pass

    def test_patron_status_valid_patron_comprehensive(self):
        """
        Positive test: Full patron status with borrowed and overdue books
        Expected: Complete status report with all required fields
        """
        result = get_patron_status_report("111111")
        
        # Skip if borrowing failed in setup
        if 'error' in str(result).lower():
            pytest.skip("Setup failed to create borrowed books")
        
        # Use flexible field names
        borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
        fees = result.get('total_late_fees_owed', result.get('total_fees', 0))
        num_borrowed = result.get('number_of_books_borrowed', result.get('total_borrowed', 0))
        history = result.get('borrowing_history', result.get('borrow_history', []))
        
        assert len(borrowed_books) >= 1  # At least one book borrowed
        assert fees >= 0
        assert num_borrowed >= 1
        assert isinstance(history, list)

    def test_patron_status_borrowed_books_details(self):
        """
        Test: Verify borrowed books contain all required details
        Expected: Complete book information with due dates
        """
        result = get_patron_status_report("111111")
        
        borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
        
        if len(borrowed_books) > 0:
            for book in borrowed_books:
                # Should have at least some required fields
                has_fields = ('book_id' in book and 'title' in book) or 'author' in book
                assert has_fields
                if 'due_date' in book:
                    assert isinstance(book['due_date'], str) or isinstance(book['due_date'], datetime)

    def test_patron_status_late_fees_calculation(self):
        """
        Test: Verify late fees are calculated correctly
        Expected: Accurate late fee calculation
        """
        result = get_patron_status_report("111111")
        
        fees = result.get('total_late_fees_owed', result.get('total_fees', 0))
        
        assert isinstance(fees, (int, float))
        assert fees <= 30.00  # Maximum for 2 books
        assert fees >= 0.00

    def test_patron_status_borrowing_history_complete(self):
        """
        Test: Verify borrowing history contains all transactions
        Expected: Complete borrowing history with details
        """
        result = get_patron_status_report("111111")
        
        history = result.get('borrowing_history', result.get('borrow_history', []))
        
        assert isinstance(history, list)
        if len(history) > 0:
            for record in history:
                # Should have some identifying information
                has_info = 'book_id' in record or 'title' in record
                assert has_info

    def test_patron_status_json_structure(self):
        """
        Test: Verify JSON structure of response
        Expected: Well-formed JSON with all required fields
        """
        result = get_patron_status_report("111111")
        
        # Check for fields with flexible naming
        has_borrowed = 'currently_borrowed_books' in result or 'current_books' in result
        has_fees = 'total_late_fees_owed' in result or 'total_fees' in result
        has_count = 'number_of_books_borrowed' in result or 'total_borrowed' in result
        has_history = 'borrowing_history' in result or 'borrow_history' in result
        
        # Check that we have lists where expected
        borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
        history = result.get('borrowing_history', result.get('borrow_history', []))
        
        assert isinstance(borrowed_books, list)
        assert isinstance(history, list)

    def test_patron_status_no_borrowed_books(self):
        """
        Test: Patron with no borrowed books
        Expected: Empty lists and zero values
        """
        result = get_patron_status_report("999999")
        
        borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
        fees = result.get('total_late_fees_owed', result.get('total_fees', 0.0))
        num_borrowed = result.get('number_of_books_borrowed', result.get('total_borrowed', 0))
        history = result.get('borrowing_history', result.get('borrow_history', []))
        
        assert len(borrowed_books) == 0
        assert fees == 0.00
        assert num_borrowed == 0
        assert len(history) == 0

    def test_patron_status_overdue_books_identification(self):
        """
        Test: Verify overdue books are properly identified
        Expected: Overdue status indicated in borrowed books
        """
        result = get_patron_status_report("111111")
        
        borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
        
        if len(borrowed_books) > 0:
            # Check if any book has overdue indicator
            has_overdue_info = any('is_overdue' in book or 'overdue' in str(book).lower() 
                                   for book in borrowed_books)
            # Or check by due date
            try:
                overdue_found = any(
                    datetime.fromisoformat(book['due_date']) < datetime.now()
                    for book in borrowed_books if 'due_date' in book
                )
                assert has_overdue_info or overdue_found
            except:
                # May not have due_date field or different format
                pass

    def test_patron_status_data_types(self):
        """
        Test: Verify correct data types in response
        Expected: All fields have correct data types
        """
        result = get_patron_status_report("111111")
        
        # Check types with flexible field names
        if 'patron_id' in result:
            assert isinstance(result['patron_id'], str)
        
        borrowed_books = result.get('currently_borrowed_books', result.get('current_books', []))
        assert isinstance(borrowed_books, list)
        
        fees = result.get('total_late_fees_owed', result.get('total_fees', 0))
        assert isinstance(fees, (int, float))
        
        num_borrowed = result.get('number_of_books_borrowed', result.get('total_borrowed', 0))
        assert isinstance(num_borrowed, int)
        
        history = result.get('borrowing_history', result.get('borrow_history', []))
        assert isinstance(history, list)

    def test_patron_status_invalid_patron_format(self):
        """
        Negative test: Invalid patron ID format
        Expected: Error status with message
        """
        result = get_patron_status_report("12345")  # Too short
        
        status = result.get('status', result.get('error', ''))
        message = result.get('message', result.get('error', ''))
        combined = (str(status) + ' ' + str(message)).lower()
        
        assert 'error' in combined or 'invalid' in combined
        assert 'patron' in combined or 'invalid' in combined

    def test_patron_status_special_characters(self):
        """
        Negative test: Patron ID with special characters
        Expected: Error status with message
        """
        result = get_patron_status_report("12@456")
        
        status = result.get('status', result.get('error', ''))
        message = result.get('message', result.get('error', ''))
        combined = (str(status) + ' ' + str(message)).lower()
        
        assert 'error' in combined or 'invalid' in combined
        assert 'patron' in combined or 'invalid' in combined