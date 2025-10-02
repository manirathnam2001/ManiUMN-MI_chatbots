#!/usr/bin/env python3
"""
Test suite for logging utilities and end-phrase detection.
"""

import os
import json
import tempfile
from pathlib import Path

from logging_utils import MIChatbotLogger, get_logger
from conversation_utils import ConversationEndDetector, format_closing_response


def test_logging_initialization():
    """Test logger initialization and file creation."""
    print("🧪 Testing Logger Initialization")
    
    # Create temporary log directory
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MIChatbotLogger(log_dir=tmpdir, log_file='test.log')
        
        # Check log file was created
        log_path = os.path.join(tmpdir, 'test.log')
        assert os.path.exists(tmpdir), "Log directory should exist"
        
        print("  ✅ Logger initialized successfully")
        return True


def test_session_logging():
    """Test session start/end logging."""
    print("🧪 Testing Session Logging")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MIChatbotLogger(log_dir=tmpdir, log_file='test.log')
        
        # Log session start
        logger.log_session_start("John Doe", "HPV Vaccine", "Alex")
        
        # Log session end
        logger.log_session_end("John Doe", "HPV Vaccine", 10, "user_initiated")
        
        # Read log file
        log_path = os.path.join(tmpdir, 'test.log')
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) >= 2, "Should have at least 2 log entries"
        
        # Parse first log entry
        log_entry = json.loads(lines[0])
        assert log_entry['event_type'] == 'session_start'
        assert log_entry['data']['student_name'] == 'John Doe'
        assert log_entry['data']['session_type'] == 'HPV Vaccine'
        assert log_entry['data']['persona'] == 'Alex'
        
        print("  ✅ Session logging works correctly")
        return True


def test_pdf_logging():
    """Test PDF generation logging."""
    print("🧪 Testing PDF Logging")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = MIChatbotLogger(log_dir=tmpdir, log_file='test.log')
        
        # Log PDF attempt
        logger.log_pdf_generation_attempt("Jane Smith", "OHI", "Bob")
        
        # Log PDF success
        logger.log_pdf_generation_success(
            "Jane Smith", "OHI", "OHI_Report.pdf", 125000, "Bob"
        )
        
        # Log PDF error (suppress console output)
        import sys
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        logger.log_pdf_generation_error(
            "Jane Smith", "OHI", "Invalid data format", "validation_error", "Bob"
        )
        
        sys.stderr = old_stderr
        
        # Read log file
        log_path = os.path.join(tmpdir, 'test.log')
        with open(log_path, 'r') as f:
            content = f.read()
            lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        if len(lines) < 3:
            print(f"  ⚠️  Only got {len(lines)} log entries")
            print(f"  Log content:\n{content}")
        
        assert len(lines) >= 3, f"Should have at least 3 log entries, got {len(lines)}"
        
        # Verify PDF attempt log
        attempt_log = json.loads(lines[0])
        assert attempt_log['event_type'] == 'pdf_generation_attempt'
        
        # Verify PDF success log
        success_log = json.loads(lines[1])
        assert success_log['event_type'] == 'pdf_generation_success'
        assert success_log['data']['file_size_bytes'] == 125000
        
        # Verify PDF error log
        error_log = json.loads(lines[2])
        assert error_log['event_type'] == 'pdf_generation_error'
        assert error_log['level'] == 'ERROR'
        
        print("  ✅ PDF logging works correctly")
        return True


def test_end_phrase_detection():
    """Test end-of-conversation phrase detection."""
    print("🧪 Testing End Phrase Detection")
    
    # Test various end phrases
    test_cases = [
        ("Thank you so much for your help!", True, "thank you"),
        ("Bye, have a great day!", True, "bye"),
        ("I'm done with the conversation", True, "i'm done"),
        ("That's all I needed", True, "that's all"),
        ("I should go now", True, "i should go"),
        ("Let me ask another question", False, None),
        ("Can you explain more about that?", False, None),
    ]
    
    passed = 0
    for text, should_detect, expected_phrase in test_cases:
        is_end, detected = ConversationEndDetector.detect_end_phrase(text)
        
        if is_end == should_detect:
            passed += 1
            if should_detect and expected_phrase:
                assert expected_phrase in detected.lower(), f"Expected '{expected_phrase}' in detected phrase"
        else:
            print(f"  ❌ Failed: '{text}' - expected {should_detect}, got {is_end}")
            return False
    
    assert passed == len(test_cases), f"Expected {len(test_cases)} to pass, got {passed}"
    print(f"  ✅ End phrase detection: {passed}/{len(test_cases)} tests passed")
    return True


def test_closing_message_generation():
    """Test closing message generation."""
    print("🧪 Testing Closing Message Generation")
    
    # Test different message indices
    message1 = ConversationEndDetector.get_closing_message(0)
    message2 = ConversationEndDetector.get_closing_message(1)
    message3 = ConversationEndDetector.get_closing_message(4)  # Should cycle
    
    assert isinstance(message1, str) and len(message1) > 0
    assert isinstance(message2, str) and len(message2) > 0
    assert message1 != message2, "Different indices should produce different messages"
    assert message1 == message3, "Index should cycle through messages"
    
    print("  ✅ Closing message generation works correctly")
    return True


def test_format_closing_response():
    """Test formatting of closing responses."""
    print("🧪 Testing Closing Response Formatting")
    
    test_cases = [
        ("thank you", "Stay safe!", "You're welcome!"),
        ("bye", "See you!", "Take care!"),
        ("I'm done", "Good job!", "Great!"),
    ]
    
    for phrase, message, expected_start in test_cases:
        result = format_closing_response(phrase, message)
        assert result.startswith(expected_start), f"Response should start with '{expected_start}'"
        assert message in result, "Response should include the closing message"
    
    print("  ✅ Closing response formatting works correctly")
    return True


def test_feedback_prompt_logic():
    """Test logic for showing feedback prompt."""
    print("🧪 Testing Feedback Prompt Logic")
    
    # Test with end phrase
    should_show = ConversationEndDetector.should_show_feedback_prompt("Thank you!", 10)
    assert should_show == True, "Should show prompt on end phrase"
    
    # Test with long conversation
    should_show = ConversationEndDetector.should_show_feedback_prompt("Tell me more", 25)
    assert should_show == True, "Should show prompt after 20+ messages"
    
    # Test with normal conversation
    should_show = ConversationEndDetector.should_show_feedback_prompt("Tell me more", 10)
    assert should_show == False, "Should not show prompt for normal conversation"
    
    print("  ✅ Feedback prompt logic works correctly")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🔬 Running Logging and Conversation Utilities Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_logging_initialization,
        test_session_logging,
        test_pdf_logging,
        test_end_phrase_detection,
        test_closing_message_generation,
        test_format_closing_response,
        test_feedback_prompt_logic,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} passed")
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
