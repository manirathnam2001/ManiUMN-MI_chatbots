#!/usr/bin/env python3
"""
Test script for Box integration and logging functionality.

Tests:
- BoxUploadLogger initialization and logging
- LogAnalyzer statistics and reporting
- BoxUploadMonitor health checks
- BoxUploader initialization and configuration
- Error handling scenarios
"""

import json
import os
import sys
import io
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from upload_logs import BoxUploadLogger, LogAnalyzer, BoxUploadMonitor
from box_integration import BoxUploader, BoxIntegrationError, InvalidFileFormatError


def setup_test_environment():
    """Setup clean test environment."""
    test_log_dir = "./test_logs"
    if os.path.exists(test_log_dir):
        shutil.rmtree(test_log_dir)
    Path(test_log_dir).mkdir(parents=True, exist_ok=True)
    return test_log_dir


def cleanup_test_environment(test_log_dir):
    """Cleanup test environment."""
    if os.path.exists(test_log_dir):
        shutil.rmtree(test_log_dir)


def test_box_upload_logger():
    """Test BoxUploadLogger functionality."""
    print("Testing BoxUploadLogger...")
    
    test_log_dir = setup_test_environment()
    
    try:
        # Test logger initialization
        logger = BoxUploadLogger("OHI", log_directory=test_log_dir)
        assert logger.bot_type == "OHI", "Bot type should be OHI"
        
        # Test log file creation - now includes UTC date
        log_filename = logger._get_log_filename()
        log_file = os.path.join(test_log_dir, log_filename)
        assert os.path.exists(log_file), "Log file should be created"
        
        # Test various logging methods
        logger.log_upload_attempt("Test Student", "test.pdf", "test@box.com", 1024)
        logger.log_upload_success("Test Student", "test.pdf", "test@box.com", 1.5)
        logger.log_upload_failure("Test Student", "test.pdf", "test@box.com", 
                                 "Test error", "TEST_ERROR")
        logger.log_email_delivery_status("test@box.com", "sent", "msg123")
        logger.log_error("TEST_ERROR", "Test error message")
        logger.log_warning("TEST_WARNING", "Test warning message")
        logger.log_critical("CRITICAL_ERROR", "Test critical error")
        
        # Verify log file has content
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0, "Log file should contain entries"
            
            # Verify JSON format
            for line in lines:
                data = json.loads(line.strip())
                assert 'timestamp' in data, "Log entry should have timestamp"
                assert 'bot_type' in data, "Log entry should have bot_type"
                assert 'level' in data, "Log entry should have level"
                assert 'event_type' in data, "Log entry should have event_type"
                assert 'message' in data, "Log entry should have message"
        
        print("  ✅ BoxUploadLogger tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ BoxUploadLogger test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ BoxUploadLogger test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup_test_environment(test_log_dir)


def test_log_analyzer():
    """Test LogAnalyzer functionality."""
    print("Testing LogAnalyzer...")
    
    test_log_dir = setup_test_environment()
    
    try:
        # Create some test logs
        logger = BoxUploadLogger("HPV", log_directory=test_log_dir)
        logger.log_upload_attempt("Student 1", "file1.pdf", "hpv@box.com", 1024)
        logger.log_upload_success("Student 1", "file1.pdf", "hpv@box.com", 1.2)
        logger.log_upload_attempt("Student 2", "file2.pdf", "hpv@box.com", 2048)
        logger.log_upload_failure("Student 2", "file2.pdf", "hpv@box.com", 
                                 "Network error", "NETWORK_ERROR")
        
        # Test analyzer
        analyzer = LogAnalyzer(test_log_dir)
        
        # Test statistics
        stats = analyzer.get_upload_statistics("HPV")
        assert stats['bot_type'] == "HPV", "Bot type should be HPV"
        assert stats['total_attempts'] == 2, "Should have 2 upload attempts"
        assert stats['total_successes'] == 1, "Should have 1 success"
        assert stats['total_failures'] == 1, "Should have 1 failure"
        assert stats['success_rate'] == 50.0, "Success rate should be 50%"
        
        # Test error summary
        errors = analyzer.get_error_summary("HPV")
        assert len(errors) > 0, "Should have error entries"
        
        # Test recent uploads
        uploads = analyzer.get_recent_uploads("HPV")
        assert len(uploads) == 4, "Should have 4 upload-related entries"
        
        print("  ✅ LogAnalyzer tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ LogAnalyzer test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ LogAnalyzer test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup_test_environment(test_log_dir)


def test_box_upload_monitor():
    """Test BoxUploadMonitor functionality."""
    print("Testing BoxUploadMonitor...")
    
    test_log_dir = setup_test_environment()
    
    try:
        # Create some test logs
        logger = BoxUploadLogger("OHI", log_directory=test_log_dir)
        for i in range(10):
            logger.log_upload_attempt(f"Student {i}", f"file{i}.pdf", "ohi@box.com")
            if i < 8:  # 80% success rate
                logger.log_upload_success(f"Student {i}", f"file{i}.pdf", "ohi@box.com")
            else:
                logger.log_upload_failure(f"Student {i}", f"file{i}.pdf", "ohi@box.com",
                                        "Error", "TEST_ERROR")
        
        # Test monitor
        monitor = BoxUploadMonitor(test_log_dir)
        
        # Test health check
        health = monitor.check_health("OHI", threshold=75.0)
        assert health['status'] == 'healthy', "Status should be healthy"
        assert health['success_rate'] == 80.0, "Success rate should be 80%"
        
        # Test unhealthy status
        health_unhealthy = monitor.check_health("OHI", threshold=90.0)
        assert health_unhealthy['status'] == 'unhealthy', "Status should be unhealthy with 90% threshold"
        
        # Test status report
        report = monitor.generate_status_report("OHI")
        assert "OHI Bot" in report, "Report should contain bot type"
        assert "Success Rate" in report, "Report should contain success rate"
        
        print("  ✅ BoxUploadMonitor tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ BoxUploadMonitor test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ BoxUploadMonitor test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup_test_environment(test_log_dir)


def test_box_uploader_init():
    """Test BoxUploader initialization."""
    print("Testing BoxUploader initialization...")
    
    try:
        # Test OHI uploader
        ohi_uploader = BoxUploader("OHI")
        assert ohi_uploader.bot_type == "OHI", "Bot type should be OHI"
        assert ohi_uploader._get_box_email() == "OHI_dir.zcdwwmukjr9ab546@u.box.com", \
            "OHI Box email should match config"
        
        # Test HPV uploader
        hpv_uploader = BoxUploader("HPV")
        assert hpv_uploader.bot_type == "HPV", "Bot type should be HPV"
        assert hpv_uploader._get_box_email() == "HPV_Dir.yqz3brxlhcurhp2l@u.box.com", \
            "HPV Box email should match config"
        
        # Test connection test (should return disabled status)
        test_result = ohi_uploader.test_connection()
        assert test_result['box_upload_enabled'] == False, "Box upload should be disabled by default"
        assert test_result['bot_type'] == "OHI", "Bot type should be OHI"
        
        print("  ✅ BoxUploader initialization tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ BoxUploader initialization test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ BoxUploader initialization test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_box_uploader_pdf_validation():
    """Test PDF validation in BoxUploader."""
    print("Testing BoxUploader PDF validation...")
    
    try:
        uploader = BoxUploader("OHI")
        
        # Test valid PDF
        valid_pdf = io.BytesIO(b'%PDF-1.4\n%Test PDF content')
        assert uploader._validate_pdf(valid_pdf) == True, "Valid PDF should pass validation"
        
        # Test invalid PDF
        invalid_pdf = io.BytesIO(b'Not a PDF file')
        assert uploader._validate_pdf(invalid_pdf) == False, "Invalid PDF should fail validation"
        
        print("  ✅ BoxUploader PDF validation tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ BoxUploader PDF validation test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ BoxUploader PDF validation test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_log_cleanup():
    """Test log cleanup functionality."""
    print("Testing log cleanup...")
    
    test_log_dir = setup_test_environment()
    
    try:
        # Create test logs
        logger = BoxUploadLogger("OHI", log_directory=test_log_dir)
        for i in range(5):
            logger.log_upload_attempt(f"Student {i}", f"file{i}.pdf", "ohi@box.com")
        
        # Test cleanup (should not remove recent files)
        analyzer = LogAnalyzer(test_log_dir)
        cleanup_results = analyzer.cleanup_old_logs(days=90)
        
        assert 'OHI' in cleanup_results, "Cleanup results should include OHI"
        assert cleanup_results['OHI'] == 0, "Should not remove recent log files"
        
        # Verify log file still exists and has entries
        log_filename = logger._get_log_filename()
        log_file = os.path.join(test_log_dir, log_filename)
        assert os.path.exists(log_file), "Log file should still exist"
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0, "Log file should still have entries"
        
        print("  ✅ Log cleanup tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ Log cleanup test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Log cleanup test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup_test_environment(test_log_dir)


def main():
    """Run all tests."""
    print("🧪 Running Box Integration and Logging Tests\n")
    print("=" * 60)
    
    tests = [
        ("BoxUploadLogger", test_box_upload_logger),
        ("LogAnalyzer", test_log_analyzer),
        ("BoxUploadMonitor", test_box_upload_monitor),
        ("BoxUploader Initialization", test_box_uploader_init),
        ("BoxUploader PDF Validation", test_box_uploader_pdf_validation),
        ("Log Cleanup", test_log_cleanup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Box integration and logging tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
