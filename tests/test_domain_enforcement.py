#!/usr/bin/env python3
"""
Test suite for domain enforcement through corrective re-prompting.

Tests:
- Corrective system messages are properly formatted
- Domain-specific redirects work for both HPV and OHI
- Injection guard messages maintain security
- Persona drift corrections preserve patient role
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona_guard import (
    create_injection_guard_message,
    create_off_topic_guard_message,
    create_persona_drift_correction_message,
    create_conciseness_correction_message,
)
from persona_texts import (
    HPV_DOMAIN_NAME,
    OHI_DOMAIN_NAME,
)


def test_injection_guard_message():
    """Test that injection guard messages are properly formatted."""
    print("\n🔍 Testing Injection Guard Message:")
    
    # Test HPV domain
    guard_msg = create_injection_guard_message(HPV_DOMAIN_NAME)
    
    if guard_msg['role'] != 'system':
        print("  ❌ Guard message role is not 'system'")
        return False
    
    content = guard_msg['content']
    
    # Check for required elements
    required_elements = [
        'SECURITY ALERT',
        HPV_DOMAIN_NAME,
        'REQUIRED RESPONSE',
    ]
    
    for element in required_elements:
        if element not in content:
            print(f"  ❌ Injection guard missing element: '{element}'")
            return False
    
    # Test OHI domain
    guard_msg = create_injection_guard_message(OHI_DOMAIN_NAME)
    if OHI_DOMAIN_NAME not in guard_msg['content']:
        print("  ❌ OHI injection guard doesn't contain domain name")
        return False
    
    print("  ✅ Injection guard messages properly formatted")
    return True


def test_off_topic_guard_message():
    """Test that off-topic guard messages redirect to domain."""
    print("\n🔍 Testing Off-Topic Guard Message:")
    
    # Test HPV domain
    guard_msg = create_off_topic_guard_message(HPV_DOMAIN_NAME)
    
    if guard_msg['role'] != 'system':
        print("  ❌ Off-topic guard message role is not 'system'")
        return False
    
    content = guard_msg['content']
    
    # Check for required elements
    required_elements = [
        'off-topic',
        HPV_DOMAIN_NAME,
        'REQUIRED RESPONSE',
        'polite redirect',
    ]
    
    for element in required_elements:
        if element not in content:
            print(f"  ❌ Off-topic guard missing element: '{element}'")
            return False
    
    # Test OHI domain
    guard_msg = create_off_topic_guard_message(OHI_DOMAIN_NAME)
    if OHI_DOMAIN_NAME not in guard_msg['content']:
        print("  ❌ OHI off-topic guard doesn't contain domain name")
        return False
    
    print("  ✅ Off-topic guard messages properly formatted")
    return True


def test_persona_drift_correction():
    """Test that persona drift correction messages are effective."""
    print("\n🔍 Testing Persona Drift Correction:")
    
    # Test HPV domain
    correction_msg = create_persona_drift_correction_message(HPV_DOMAIN_NAME)
    
    if correction_msg['role'] != 'system':
        print("  ❌ Drift correction message role is not 'system'")
        return False
    
    content = correction_msg['content']
    
    # Check for required elements
    required_elements = [
        'CRITICAL CORRECTION',
        'broken character',
        'patient role',
        'NOT',
        'evaluator',
        HPV_DOMAIN_NAME,
        'REGENERATE',
    ]
    
    for element in required_elements:
        if element not in content:
            print(f"  ❌ Drift correction missing element: '{element}'")
            return False
    
    # Test OHI domain
    correction_msg = create_persona_drift_correction_message(OHI_DOMAIN_NAME)
    if OHI_DOMAIN_NAME not in correction_msg['content']:
        print("  ❌ OHI drift correction doesn't contain domain name")
        return False
    
    print("  ✅ Persona drift correction messages properly formatted")
    return True


def test_conciseness_correction():
    """Test that conciseness correction messages enforce brevity."""
    print("\n🔍 Testing Conciseness Correction:")
    
    correction_msg = create_conciseness_correction_message()
    
    if correction_msg['role'] != 'system':
        print("  ❌ Conciseness correction message role is not 'system'")
        return False
    
    content = correction_msg['content']
    
    # Check for required elements
    required_elements = [
        'too long',
        'CRITICAL',
        '2-3 sentences',
        'REGENERATE',
    ]
    
    for element in required_elements:
        if element not in content:
            print(f"  ❌ Conciseness correction missing element: '{element}'")
            return False
    
    print("  ✅ Conciseness correction message properly formatted")
    return True


def test_message_structure_consistency():
    """Test that all corrective messages follow consistent structure."""
    print("\n🔍 Testing Message Structure Consistency:")
    
    messages = [
        create_injection_guard_message(HPV_DOMAIN_NAME),
        create_off_topic_guard_message(HPV_DOMAIN_NAME),
        create_persona_drift_correction_message(HPV_DOMAIN_NAME),
        create_conciseness_correction_message(),
    ]
    
    for msg in messages:
        # Check basic structure
        if 'role' not in msg or 'content' not in msg:
            print("  ❌ Message missing basic structure")
            return False
        
        # Check role is system
        if msg['role'] != 'system':
            print(f"  ❌ Message has wrong role: {msg['role']}")
            return False
        
        # Check content is non-empty string
        if not isinstance(msg['content'], str) or len(msg['content']) == 0:
            print("  ❌ Message content is empty or not a string")
            return False
    
    print("  ✅ All corrective messages follow consistent structure")
    return True


def test_domain_specificity():
    """Test that domain-specific messages contain correct domain references."""
    print("\n🔍 Testing Domain Specificity:")
    
    # HPV messages should contain HPV references
    hpv_messages = [
        create_injection_guard_message(HPV_DOMAIN_NAME),
        create_off_topic_guard_message(HPV_DOMAIN_NAME),
        create_persona_drift_correction_message(HPV_DOMAIN_NAME),
    ]
    
    for msg in hpv_messages:
        if HPV_DOMAIN_NAME not in msg['content']:
            print(f"  ❌ HPV message doesn't contain HPV domain name")
            return False
        
        # Should not contain OHI references
        if OHI_DOMAIN_NAME in msg['content']:
            print(f"  ❌ HPV message incorrectly contains OHI domain name")
            return False
    
    # OHI messages should contain OHI references
    ohi_messages = [
        create_injection_guard_message(OHI_DOMAIN_NAME),
        create_off_topic_guard_message(OHI_DOMAIN_NAME),
        create_persona_drift_correction_message(OHI_DOMAIN_NAME),
    ]
    
    for msg in ohi_messages:
        if OHI_DOMAIN_NAME not in msg['content']:
            print(f"  ❌ OHI message doesn't contain OHI domain name")
            return False
        
        # Should not contain HPV references
        if HPV_DOMAIN_NAME in msg['content']:
            print(f"  ❌ OHI message incorrectly contains HPV domain name")
            return False
    
    print("  ✅ Domain specificity maintained correctly")
    return True


def test_corrective_tone():
    """Test that corrective messages use appropriate assertive tone."""
    print("\n🔍 Testing Corrective Tone:")
    
    messages = [
        create_injection_guard_message(HPV_DOMAIN_NAME),
        create_off_topic_guard_message(HPV_DOMAIN_NAME),
        create_persona_drift_correction_message(HPV_DOMAIN_NAME),
        create_conciseness_correction_message(),
    ]
    
    # Check for assertive language
    assertive_indicators = ['REQUIRED', 'MUST', 'CRITICAL', 'DO NOT', 'REGENERATE']
    
    for msg in messages:
        content = msg['content']
        has_assertive = any(indicator in content for indicator in assertive_indicators)
        
        if not has_assertive:
            print(f"  ❌ Message lacks assertive tone indicators")
            return False
    
    print("  ✅ Corrective messages use appropriate assertive tone")
    return True


def main():
    """Run all domain enforcement tests."""
    print("🧪 Running Domain Enforcement Tests\n")
    
    tests = [
        ("Injection Guard Message", test_injection_guard_message),
        ("Off-Topic Guard Message", test_off_topic_guard_message),
        ("Persona Drift Correction", test_persona_drift_correction),
        ("Conciseness Correction", test_conciseness_correction),
        ("Message Structure Consistency", test_message_structure_consistency),
        ("Domain Specificity", test_domain_specificity),
        ("Corrective Tone", test_corrective_tone),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ {test_name} raised exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if failed == 0:
        print("🎉 All tests passed! Domain enforcement is working correctly.")
        return 0
    else:
        print(f"⚠️  {failed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
