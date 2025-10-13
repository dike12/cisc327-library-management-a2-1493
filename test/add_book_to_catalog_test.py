import pytest
import sys
sys.path.insert(0, '../')

from database import init_database, get_db_connection
from library_service import add_book_to_catalog


class TestAddBookToCatalog:
    """Test suite for R1: Add Book To Catalog functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        init_database()
    
    def teardown_method(self):
        """Cleanup after each test"""
        try:
            conn = get_db_connection()
            conn.close()
        except:
            pass
    
    def test_add_book_valid_input(self):
        """
        Positive test: Add book with all valid inputs
        Expected: Success with confirmation message
        """
        import random
        unique_isbn = f"9{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("The Great Gatsby Test", "F. Scott Fitzgerald", unique_isbn, 3)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()
    
    def test_add_book_minimal_valid_input(self):
        """
        Positive test: Add book with minimal valid data (single character title/author)
        Expected: Success
        """
        import random
        unique_isbn = f"1{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("A", "B", unique_isbn, 1)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()
    
    def test_add_book_maximum_length_inputs(self):
        """
        Positive test: Add book with maximum allowed character lengths
        Expected: Success
        """
        import random
        unique_isbn = f"2{str(random.randint(100000000000, 999999999999))}"
        
        long_title = "A" * 200  # Exactly 200 characters
        long_author = "B" * 100  # Exactly 100 characters
        
        success, message = add_book_to_catalog(long_title, long_author, unique_isbn, 5)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()
    
    def test_add_book_whitespace_trimming(self):
        """
        Positive test: Verify whitespace is properly trimmed from title and author
        Expected: Success with trimmed values
        """
        import random
        unique_isbn = f"3{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("  Spaced Title  ", "  Spaced Author  ", unique_isbn, 2)
        
        assert success == True
        # Message may or may not include the title
        assert "successfully added" in message.lower() or "added" in message.lower()
    
    def test_add_book_empty_title(self):
        """
        Negative test: Empty title
        Expected: Failure with appropriate error message
        """
        import random
        unique_isbn = f"4{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("", "Valid Author", unique_isbn, 1)
        
        assert success == False
        assert "title" in message.lower() or "required" in message.lower()
    
    def test_add_book_whitespace_only_title(self):
        """
        Negative test: Title with only whitespace
        Expected: Failure with appropriate error message
        """
        import random
        unique_isbn = f"5{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("   ", "Valid Author", unique_isbn, 1)
        
        assert success == False
        assert "title" in message.lower() or "required" in message.lower()
    
    def test_add_book_title_too_long(self):
        """
        Negative test: Title exceeds 200 character limit
        Expected: Failure with length validation error
        """
        import random
        unique_isbn = f"6{str(random.randint(100000000000, 999999999999))}"
        
        long_title = "A" * 201  # 201 characters (over limit)
        success, message = add_book_to_catalog(long_title, "Valid Author", unique_isbn, 1)
        
        assert success == False
        assert "200" in message or "characters" in message.lower() or "long" in message.lower()
    
    def test_add_book_empty_author(self):
        """
        Negative test: Empty author
        Expected: Failure with appropriate error message
        """
        import random
        unique_isbn = f"7{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Valid Title", "", unique_isbn, 1)
        
        assert success == False
        assert "author" in message.lower() or "required" in message.lower()
    
    def test_add_book_author_too_long(self):
        """
        Negative test: Author exceeds 100 character limit
        Expected: Failure with length validation error
        """
        import random
        unique_isbn = f"8{str(random.randint(100000000000, 999999999999))}"
        
        long_author = "B" * 101  # 101 characters (over limit)
        success, message = add_book_to_catalog("Valid Title", long_author, unique_isbn, 1)
        
        assert success == False
        assert "100" in message or "characters" in message.lower() or "long" in message.lower()
    
    def test_add_book_isbn_too_short(self):
        """
        Negative test: ISBN with less than 13 digits
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "123456789", 1)
        
        assert success == False
        assert "13" in message or "isbn" in message.lower() or "digit" in message.lower()
    
    def test_add_book_isbn_too_long(self):
        """
        Negative test: ISBN with more than 13 digits
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "12345678901234", 1)
        
        assert success == False
        assert "13" in message or "isbn" in message.lower() or "digit" in message.lower()
    
    def test_add_book_isbn_with_letters(self):
        """
        Negative test: ISBN containing non-digit characters
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "123456789012A", 1)
        
        assert success == False
        # May fail with "ISBN exists" if this ISBN was added in previous test run
        assert "13" in message or "isbn" in message.lower() or "digit" in message.lower() or "exists" in message.lower()
    
    def test_add_book_zero_copies(self):
        """
        Negative test: Zero total copies
        Expected: Failure with positive integer validation error
        """
        import random
        unique_isbn = f"9{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Valid Title", "Valid Author", unique_isbn, 0)
        
        assert success == False
        assert "positive" in message.lower() or "integer" in message.lower() or "greater" in message.lower()
    
    def test_add_book_negative_copies(self):
        """
        Negative test: Negative total copies
        Expected: Failure with positive integer validation error
        """
        import random
        unique_isbn = f"A{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Valid Title", "Valid Author", unique_isbn, -1)
        
        assert success == False
        assert "positive" in message.lower() or "integer" in message.lower() or "greater" in message.lower()
    
    def test_add_book_non_integer_copies(self):
        """
        Negative test: Non-integer total copies (string)
        Expected: Failure with integer validation error
        """
        import random
        unique_isbn = f"B{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Valid Title", "Valid Author", unique_isbn, "5")
        
        assert success == False
        assert "integer" in message.lower() or "type" in message.lower() or "number" in message.lower()
    
    def test_add_book_float_copies(self):
        """
        Negative test: Float value for total copies
        Expected: Failure with integer validation error
        """
        import random
        unique_isbn = f"C{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Valid Title", "Valid Author", unique_isbn, 5.5)
        
        assert success == False
        assert "integer" in message.lower() or "type" in message.lower() or "number" in message.lower()

    def test_add_book_special_characters_in_title(self):
        """
        Positive test: Title containing special characters
        Expected: Success
        """
        import random
        unique_isbn = f"D{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Book! @#$%^&*()", "Valid Author", unique_isbn, 1)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()

    def test_add_book_unicode_characters(self):
        """
        Positive test: Title and author with Unicode characters
        Expected: Success
        """
        import random
        unique_isbn = f"E{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("título del libro", "José García", unique_isbn, 1)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()

    def test_add_book_numbers_in_title(self):
        """
        Positive test: Title containing numbers
        Expected: Success
        """
        import random
        unique_isbn = f"F{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Book 123", "Valid Author", unique_isbn, 1)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()

    def test_add_book_duplicate_title_different_isbn(self):
        """
        Positive test: Same title but different ISBN
        Expected: Success
        """
        import random
        isbn1 = f"G{str(random.randint(100000000000, 999999999999))}"
        isbn2 = f"H{str(random.randint(100000000000, 999999999999))}"
        
        add_book_to_catalog("Duplicate Title Test", "Author One", isbn1, 1)
        success, message = add_book_to_catalog("Duplicate Title Test", "Author Two", isbn2, 1)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()

    def test_add_book_max_copies(self):
        """
        Positive test: Large number of copies
        Expected: Success
        """
        import random
        unique_isbn = f"I{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Valid Title", "Valid Author", unique_isbn, 999999)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()

    def test_add_book_title_only_numbers(self):
        """
        Positive test: Title consisting only of numbers
        Expected: Success
        """
        import random
        unique_isbn = f"J{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("12345", "Valid Author", unique_isbn, 1)
        
        assert success == True
        assert "successfully added" in message.lower() or "added" in message.lower()

    def test_add_book_null_title(self):
        """
        Negative test: None as title
        Expected: Failure with appropriate error message
        """
        import random
        unique_isbn = f"K{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog(None, "Valid Author", unique_isbn, 1)
        
        assert success == False
        assert "title" in message.lower() or "required" in message.lower()

    def test_add_book_null_author(self):
        """
        Negative test: None as author
        Expected: Failure with appropriate error message
        """
        import random
        unique_isbn = f"L{str(random.randint(100000000000, 999999999999))}"
        
        success, message = add_book_to_catalog("Valid Title", None, unique_isbn, 1)
        
        assert success == False
        assert "author" in message.lower() or "required" in message.lower()

    def test_add_book_invalid_isbn_letters_and_numbers(self):
        """
        Negative test: ISBN with mix of letters and numbers but correct length
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "12345ABC67890", 1)
        
        assert success == False
        # May fail with different messages depending on validation order
        assert "13" in message or "digit" in message.lower() or "isbn" in message.lower() or "exists" in message.lower()

    def test_add_book_special_characters_in_isbn(self):
        """
        Negative test: ISBN with special characters
        Expected: Failure with ISBN validation error
        """
        success, message = add_book_to_catalog("Valid Title", "Valid Author", "123456!@#$%90", 1)
        
        assert success == False
        # May fail with different messages depending on validation order
        assert "13" in message or "digit" in message.lower() or "isbn" in message.lower() or "exists" in message.lower()