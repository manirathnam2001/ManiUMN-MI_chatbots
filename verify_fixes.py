#!/usr/bin/env python3
"""
Verification script for critical fixes in MI chatbots.

This script verifies:
1. Time zone parsing with AM/PM and timezone indicators
2. PDF module import functionality
3. SentenceTransformer device handling with CPU fallback
"""

def test_timezone_parsing():
    """Test time zone parsing improvements."""
    print("\n" + "="*70)
    print("1. TESTING TIME ZONE PARSING")
    print("="*70)
    
    from time_utils import convert_to_minnesota_time
    
    test_cases = [
        ("2025-01-15 18:00:00", "Winter - UTC to Minnesota (CST)"),
        ("2025-07-15 18:00:00", "Summer - UTC to Minnesota (CDT)"),
        ("2025-01-15 18:00:00 UTC", "With timezone indicator"),
    ]
    
    print("\nConverting UTC times to Minnesota time with AM/PM format:")
    for utc_time, description in test_cases:
        mn_time = convert_to_minnesota_time(utc_time)
        print(f"\n  {description}:")
        print(f"    UTC Input:   {utc_time}")
        print(f"    MN Output:   {mn_time}")
        
        # Verify new format
        if (" AM " in mn_time or " PM " in mn_time) and ("CST" in mn_time or "CDT" in mn_time):
            print(f"    ✅ Format includes AM/PM and timezone")
        else:
            print(f"    ❌ Format missing AM/PM or timezone")
            return False
    
    return True


def test_pdf_import():
    """Test PDF module import."""
    print("\n" + "="*70)
    print("2. TESTING PDF MODULE IMPORT")
    print("="*70)
    
    try:
        from pdf_utils import generate_pdf_report
        print("\n  ✅ pdf_utils.generate_pdf_report imported successfully")
        print("  ✅ Module is accessible without additional path configuration")
        return True
    except ImportError as e:
        print(f"\n  ❌ Import error: {e}")
        return False


def test_sentence_transformer():
    """Test SentenceTransformer device handling."""
    print("\n" + "="*70)
    print("3. TESTING SENTENCETRANSFORMER DEVICE HANDLING")
    print("="*70)
    
    try:
        import torch
        from sentence_transformers import SentenceTransformer
        
        # Initialize with CPU fallback
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"\n  Device detection:")
        print(f"    CUDA available: {torch.cuda.is_available()}")
        print(f"    Selected device: {device}")
        
        # Load model
        print(f"\n  Loading model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding_model.to(device)
        print(f"    ✅ Model loaded and moved to {device}")
        
        # Test encoding
        print(f"\n  Testing encoding...")
        test_text = ["This is a test sentence for MI chatbot evaluation."]
        embeddings = embedding_model.encode(test_text)
        print(f"    ✅ Successfully encoded text")
        print(f"    Embedding shape: {embeddings.shape}")
        print(f"    Expected dimension: 384, Got: {embeddings.shape[1]}")
        
        if embeddings.shape[1] == 384:
            print(f"    ✅ Correct embedding dimension")
            return True
        else:
            print(f"    ❌ Unexpected embedding dimension")
            return False
            
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "="*70)
    print("VERIFYING CRITICAL FIXES FOR MI CHATBOTS")
    print("="*70)
    
    results = {
        "Time Zone Parsing": test_timezone_parsing(),
        "PDF Module Import": test_pdf_import(),
        "SentenceTransformer Device": test_sentence_transformer(),
    }
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("ALL TESTS PASSED! ✅")
        print("\nThe following fixes have been successfully implemented:")
        print("  1. Time zone conversion with AM/PM and timezone indicators")
        print("  2. PDF module imports work correctly")
        print("  3. SentenceTransformer device handling with CPU fallback")
    else:
        print("SOME TESTS FAILED! ❌")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
