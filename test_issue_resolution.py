"""
Integration test demonstrating the FileNotFoundError is resolved.

This test validates that the fix correctly resolves the issue where
navigating from Secret Code portal to OHI/HPV would trigger FileNotFoundError.
"""

import os
import sys
from pathlib import Path


def test_issue_resolution():
    """
    Test that demonstrates the original issue is resolved.
    
    Original Issue:
    - After consolidating into multipage app, navigating from Secret Code portal
      to OHI triggered: FileNotFoundError at pages/OHI.py line 120: 
      for filename in os.listdir(rubrics_dir)
    
    Root Cause:
    - pages/OHI.py set rubrics_dir = os.path.join(working_dir, "ohi_rubrics")
    - working_dir was pages/ folder
    - ohi_rubrics lives at repository root
    - Path was incorrect: pages/ohi_rubrics instead of ohi_rubrics
    
    Fix:
    - Uses pathlib to compute repo_root = script_dir.parent
    - Searches repo_root/ohi_rubrics first (correct location)
    - Falls back to script_dir/ohi_rubrics if needed
    - Shows clear error if neither exists
    """
    print("=" * 70)
    print("ISSUE RESOLUTION TEST")
    print("=" * 70)
    
    print("\nOriginal Issue:")
    print("  FileNotFoundError when navigating from portal to OHI/HPV")
    print("  Caused by: pages/[bot].py looking for rubrics in wrong location")
    
    # Verify the fix is in place
    print("\n1. Checking OHI.py fix...")
    with open('pages/OHI.py', 'r') as f:
        ohi_content = f.read()
    
    # Verify old broken pattern is gone
    assert 'working_dir = os.path.dirname(os.path.abspath(__file__))' not in ohi_content, \
        "Old broken pattern should be removed"
    print("   ✓ Old broken pattern removed")
    
    # Verify new fix is present
    assert 'script_dir = Path(__file__).resolve().parent' in ohi_content, \
        "New path resolution should be present"
    assert 'repo_root = script_dir.parent' in ohi_content, \
        "Repo root should be computed"
    assert 'repo_root / "ohi_rubrics"' in ohi_content, \
        "Should search repo root first"
    print("   ✓ New path resolution implemented")
    
    print("\n2. Checking HPV.py fix...")
    with open('pages/HPV.py', 'r') as f:
        hpv_content = f.read()
    
    # Verify old broken pattern is gone
    assert 'working_dir = os.path.dirname(os.path.abspath(__file__))' not in hpv_content, \
        "Old broken pattern should be removed"
    print("   ✓ Old broken pattern removed")
    
    # Verify new fix is present
    assert 'script_dir = Path(__file__).resolve().parent' in hpv_content, \
        "New path resolution should be present"
    assert 'repo_root = script_dir.parent' in hpv_content, \
        "Repo root should be computed"
    assert 'repo_root / "hpv_rubrics"' in hpv_content, \
        "Should search repo root first"
    print("   ✓ New path resolution implemented")
    
    # Simulate the actual scenario
    print("\n3. Simulating navigation from portal to OHI...")
    
    # Simulate being in pages/OHI.py (where the error occurred)
    pages_dir = Path("pages").resolve()
    repo_root = pages_dir.parent
    
    # Old broken approach (would fail)
    old_rubrics_path = pages_dir / "ohi_rubrics"
    print(f"   Old (broken) path: {old_rubrics_path}")
    print(f"   Exists: {old_rubrics_path.exists()}")
    
    # New fixed approach (works)
    new_rubrics_path = repo_root / "ohi_rubrics"
    print(f"   New (fixed) path: {new_rubrics_path}")
    print(f"   Exists: {new_rubrics_path.exists()}")
    
    assert not old_rubrics_path.exists(), "Old path should not exist"
    assert new_rubrics_path.exists(), "New path should exist"
    print("   ✓ Fix resolves the FileNotFoundError")
    
    # Verify files can be listed (the exact operation that was failing)
    print("\n4. Testing the exact operation that was failing...")
    print(f"   os.listdir({new_rubrics_path})")
    
    try:
        files = os.listdir(new_rubrics_path)
        txt_files = [f for f in files if f.endswith('.txt')]
        print(f"   ✓ Success! Found {len(txt_files)} .txt files")
        for f in txt_files:
            print(f"      - {f}")
    except FileNotFoundError:
        print("   ✗ FAILED: FileNotFoundError still occurs")
        return False
    
    print("\n5. Testing HPV path resolution...")
    hpv_rubrics_path = repo_root / "hpv_rubrics"
    print(f"   Path: {hpv_rubrics_path}")
    print(f"   Exists: {hpv_rubrics_path.exists()}")
    
    try:
        files = os.listdir(hpv_rubrics_path)
        txt_files = [f for f in files if f.endswith('.txt')]
        print(f"   ✓ Success! Found {len(txt_files)} .txt files")
        for f in txt_files:
            print(f"      - {f}")
    except FileNotFoundError:
        print("   ✗ FAILED: FileNotFoundError still occurs")
        return False
    
    print("\n" + "=" * 70)
    print("✓ ISSUE RESOLVED: FileNotFoundError will no longer occur")
    print("=" * 70)
    print("\nSummary:")
    print("  - Old pattern removed from both pages/OHI.py and pages/HPV.py")
    print("  - New robust path resolution implemented using pathlib")
    print("  - Rubrics correctly found at repository root")
    print("  - os.listdir() operations now succeed")
    print("  - Users can navigate from portal to OHI/HPV without errors")
    
    return True


def main():
    try:
        success = test_issue_resolution()
        return 0 if success else 1
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
