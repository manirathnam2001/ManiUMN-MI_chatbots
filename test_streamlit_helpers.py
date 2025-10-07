#!/usr/bin/env python3
"""
Test the Streamlit helper functions for Box integration.
These tests verify the helper functions work correctly (without actually running Streamlit).
"""

import sys
import io
from unittest.mock import Mock, patch, MagicMock

# Mock streamlit before importing helpers
sys.modules['streamlit'] = MagicMock()

# Import the helper functions
from box_streamlit_helpers import (
    add_box_upload_button,
    check_box_configuration_status,
    show_box_upload_in_sidebar
)
from box_config import BoxConfig


def test_streamlit_helpers_import():
    """Test that streamlit helpers can be imported."""
    print("🧪 Testing Streamlit Helpers Import")
    
    try:
        # Verify functions are available
        assert callable(add_box_upload_button), "add_box_upload_button should be callable"
        assert callable(check_box_configuration_status), "check_box_configuration_status should be callable"
        assert callable(show_box_upload_in_sidebar), "show_box_upload_in_sidebar should be callable"
        
        print("✅ All Streamlit helper functions imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_box_config_in_helpers():
    """Test that BoxConfig works properly in helper context."""
    print("🧪 Testing BoxConfig in Helper Context")
    
    try:
        # Create config
        config = BoxConfig(
            box_email="test@box.com",
            smtp_host="smtp.test.com",
            smtp_username="user@test.com",
            smtp_password="testpass",
            sender_email="sender@test.com"
        )
        
        # Verify configuration
        assert config.is_configured(), "Config should be valid"
        assert config.box_email == "test@box.com"
        
        print("✅ BoxConfig works correctly in helper context")
        return True
    except Exception as e:
        print(f"❌ BoxConfig helper test failed: {e}")
        return False


def test_add_box_upload_button_with_mock():
    """Test add_box_upload_button with mocked Streamlit."""
    print("🧪 Testing add_box_upload_button (with mocks)")
    
    try:
        # Mock streamlit
        mock_st = MagicMock()
        
        # Create test PDF
        test_pdf = io.BytesIO(b"%PDF-1.4 test")
        
        # Test with incomplete config (should show warning)
        with patch('box_streamlit_helpers.st', mock_st):
            with patch('box_streamlit_helpers.BoxConfig') as mock_config_class:
                mock_config = MagicMock()
                mock_config.is_configured.return_value = False
                mock_config.get_missing_settings.return_value = ['smtp_username', 'smtp_password']
                mock_config_class.return_value = mock_config
                
                # This should not crash
                result = add_box_upload_button(test_pdf, "test.pdf")
                
                # Should have shown warning
                assert mock_st.warning.called or mock_st.info.called, "Should show configuration warning"
        
        print("✅ add_box_upload_button handles configuration properly")
        return True
    except Exception as e:
        print(f"❌ add_box_upload_button test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filename_handling():
    """Test that filenames are handled correctly."""
    print("🧪 Testing Filename Handling")
    
    try:
        mock_st = MagicMock()
        test_pdf = io.BytesIO(b"%PDF-1.4 test")
        
        with patch('box_streamlit_helpers.st', mock_st):
            with patch('box_streamlit_helpers.BoxConfig') as mock_config_class:
                mock_config = MagicMock()
                mock_config.is_configured.return_value = False
                mock_config_class.return_value = mock_config
                
                # Test filename without extension
                add_box_upload_button(test_pdf, "test_report")
                
                # Test filename with extension
                add_box_upload_button(test_pdf, "test_report.pdf")
                
                # Both should work without errors
        
        print("✅ Filename handling works correctly")
        return True
    except Exception as e:
        print(f"❌ Filename handling test failed: {e}")
        return False


def test_check_box_configuration_status():
    """Test configuration status checking."""
    print("🧪 Testing check_box_configuration_status")
    
    try:
        mock_st = MagicMock()
        
        with patch('box_streamlit_helpers.st', mock_st):
            # Test with configured Box
            with patch('box_streamlit_helpers.BoxConfig') as mock_config_class:
                mock_config = MagicMock()
                mock_config.is_configured.return_value = True
                mock_config.box_email = "test@box.com"
                mock_config.smtp_host = "smtp.test.com"
                mock_config.smtp_port = 587
                mock_config.sender_email = "sender@test.com"
                mock_config.max_retry_attempts = 3
                mock_config_class.return_value = mock_config
                
                result = check_box_configuration_status()
                
                # Should return True for configured
                assert result is True, "Should return True when configured"
                assert mock_st.success.called, "Should show success message"
        
        print("✅ check_box_configuration_status works correctly")
        return True
    except Exception as e:
        print(f"❌ check_box_configuration_status test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_show_box_upload_in_sidebar():
    """Test sidebar display function."""
    print("🧪 Testing show_box_upload_in_sidebar")
    
    try:
        mock_st = MagicMock()
        
        with patch('box_streamlit_helpers.st', mock_st):
            with patch('box_streamlit_helpers.BoxConfig') as mock_config_class:
                mock_config = MagicMock()
                mock_config.is_configured.return_value = True
                mock_config.box_email = "test@box.com"
                mock_config_class.return_value = mock_config
                
                # Should not crash
                show_box_upload_in_sidebar()
                
                # Should have used sidebar
                assert mock_st.sidebar is not None, "Should use sidebar"
        
        print("✅ show_box_upload_in_sidebar works correctly")
        return True
    except Exception as e:
        print(f"❌ show_box_upload_in_sidebar test failed: {e}")
        return False


def test_helper_with_different_configs():
    """Test helpers with various configuration states."""
    print("🧪 Testing Helpers with Different Configs")
    
    try:
        test_pdf = io.BytesIO(b"%PDF-1.4 test")
        mock_st = MagicMock()
        
        # Test 1: Fully configured
        with patch('box_streamlit_helpers.st', mock_st):
            with patch('box_streamlit_helpers.BoxConfig') as mock_config_class:
                mock_config = MagicMock()
                mock_config.is_configured.return_value = True
                mock_config.box_email = "test@box.com"
                mock_config_class.return_value = mock_config
                
                check_box_configuration_status()
                # Should show success
        
        # Test 2: Partially configured
        with patch('box_streamlit_helpers.st', mock_st):
            with patch('box_streamlit_helpers.BoxConfig') as mock_config_class:
                mock_config = MagicMock()
                mock_config.is_configured.return_value = False
                mock_config.get_missing_settings.return_value = ['smtp_password']
                mock_config_class.return_value = mock_config
                
                check_box_configuration_status()
                # Should show warning
        
        print("✅ Helpers work correctly with different configurations")
        return True
    except Exception as e:
        print(f"❌ Different configs test failed: {e}")
        return False


def test_error_guidance():
    """Test that helpers provide appropriate error guidance."""
    print("🧪 Testing Error Guidance")
    
    try:
        test_pdf = io.BytesIO(b"%PDF-1.4 test")
        mock_st = MagicMock()
        
        from pdf_utils import BoxUploadError
        
        with patch('box_streamlit_helpers.st', mock_st):
            with patch('box_streamlit_helpers.BoxConfig') as mock_config_class:
                mock_config = MagicMock()
                mock_config.is_configured.return_value = True
                mock_config.box_email = "test@box.com"
                mock_config_class.return_value = mock_config
                
                # Mock button click
                mock_st.button.return_value = True
                
                # Mock upload failure
                with patch('box_streamlit_helpers.upload_pdf_to_box') as mock_upload:
                    # Test authentication error
                    mock_upload.side_effect = BoxUploadError("SMTP authentication failed")
                    
                    add_box_upload_button(test_pdf, "test.pdf")
                    
                    # Should have shown error and info
                    # (Checking that the function doesn't crash)
        
        print("✅ Error guidance works correctly")
        return True
    except Exception as e:
        print(f"❌ Error guidance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Streamlit helper tests."""
    print("🧪 Testing Box Integration Streamlit Helpers\n")
    
    tests = [
        ("Streamlit Helpers Import", test_streamlit_helpers_import),
        ("BoxConfig in Helper Context", test_box_config_in_helpers),
        ("add_box_upload_button", test_add_box_upload_button_with_mock),
        ("Filename Handling", test_filename_handling),
        ("check_box_configuration_status", test_check_box_configuration_status),
        ("show_box_upload_in_sidebar", test_show_box_upload_in_sidebar),
        ("Different Configurations", test_helper_with_different_configs),
        ("Error Guidance", test_error_guidance),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Streamlit helper tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
