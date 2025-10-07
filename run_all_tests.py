#!/usr/bin/env python3
"""
Master test runner for internal scoring modifiers implementation.
Runs all tests and provides a comprehensive validation report.
"""

import sys
import subprocess


def run_test(test_file, description):
    """Run a test file and return success status."""
    print(f"\n{'=' * 70}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print(f"{'=' * 70}\n")
    
    result = subprocess.run([sys.executable, test_file], capture_output=False)
    return result.returncode == 0


def main():
    """Run all tests and generate final report."""
    print("\n" + "=" * 70)
    print("INTERNAL SCORING MODIFIERS - MASTER TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("test_scoring_consistency.py", "Scoring Consistency Tests (Legacy + Lenient)"),
        ("test_internal_modifiers.py", "Internal Modifiers Tests (New Features)"),
        ("demo_scoring_system.py", "System Demo (Integration Test)"),
    ]
    
    results = []
    
    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))
    
    # Generate final report
    print("\n" + "=" * 70)
    print("FINAL TEST REPORT")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n📊 Overall Results: {passed}/{total} test suites passed\n")
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {status}: {description}")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Internal scoring modifiers implementation complete and verified!")
        print("\nKey Features Validated:")
        print("  • Maximum score capped at 30 points")
        print("  • Lenient base scoring (0.6 multiplier for Partially Met)")
        print("  • Effort multiplier (1.0-1.3x based on engagement)")
        print("  • Time multiplier (0.9-1.2x based on response timing)")
        print("  • Score consistency maintained")
        print("  • Backward compatibility preserved")
        print("  • Integration with HPV and OHI apps")
        print("\n" + "=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️  SOME TESTS FAILED")
        print("=" * 70)
        print(f"\n{total - passed} test suite(s) need attention.")
        print("\nPlease review the output above for details.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
