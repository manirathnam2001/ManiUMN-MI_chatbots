"""
Test for rubric directory path resolution in OHI.py and HPV.py.

This test validates that the pages properly resolve rubric directories
from the repository root regardless of where the bot scripts are located.
"""

import os
import sys
from pathlib import Path


def test_ohi_path_resolution():
    """Test OHI.py uses pathlib and searches correct locations."""
    print("Testing OHI.py path resolution...")
    
    with open('pages/OHI.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that pathlib is imported
    assert 'from pathlib import Path' in content, \
        "OHI.py should import pathlib.Path"
    
    # Check for script_dir and repo_root computation
    assert 'script_dir = Path(__file__).resolve().parent' in content, \
        "OHI.py should compute script_dir using Path"
    assert 'repo_root = script_dir.parent' in content, \
        "OHI.py should compute repo_root"
    
    # Check for search in repo_root first
    assert 'repo_root / "ohi_rubrics"' in content, \
        "OHI.py should search repo_root/ohi_rubrics first"
    
    # Check for fallback to script_dir
    assert 'script_dir / "ohi_rubrics"' in content, \
        "OHI.py should have fallback to script_dir/ohi_rubrics"
    
    # Check for error handling
    assert 'if rubrics_dir is None:' in content, \
        "OHI.py should check if rubrics_dir was found"
    assert 'st.error' in content or 'st.stop()' in content, \
        "OHI.py should show error and stop if rubrics not found"
    
    # Check that old working_dir pattern is removed
    assert 'working_dir = os.path.dirname(os.path.abspath(__file__))' not in content, \
        "OHI.py should not use old working_dir pattern"
    
    print("  ✓ OHI.py has correct path resolution")


def test_hpv_path_resolution():
    """Test HPV.py uses pathlib and searches correct locations."""
    print("\nTesting HPV.py path resolution...")
    
    with open('pages/HPV.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that pathlib is imported
    assert 'from pathlib import Path' in content, \
        "HPV.py should import pathlib.Path"
    
    # Check for script_dir and repo_root computation
    assert 'script_dir = Path(__file__).resolve().parent' in content, \
        "HPV.py should compute script_dir using Path"
    assert 'repo_root = script_dir.parent' in content, \
        "HPV.py should compute repo_root"
    
    # Check for search in repo_root first
    assert 'repo_root / "hpv_rubrics"' in content, \
        "HPV.py should search repo_root/hpv_rubrics first"
    
    # Check for fallback to script_dir
    assert 'script_dir / "hpv_rubrics"' in content, \
        "HPV.py should have fallback to script_dir/hpv_rubrics"
    
    # Check for error handling
    assert 'if rubrics_dir is None:' in content, \
        "HPV.py should check if rubrics_dir was found"
    assert 'st.error' in content or 'st.stop()' in content, \
        "HPV.py should show error and stop if rubrics not found"
    
    # Check that old working_dir pattern is removed
    assert 'working_dir = os.path.dirname(os.path.abspath(__file__))' not in content, \
        "HPV.py should not use old working_dir pattern"
    
    print("  ✓ HPV.py has correct path resolution")


def test_rubric_directories_exist():
    """Test that rubric directories exist at repository root."""
    print("\nTesting rubric directories exist...")
    
    repo_root = Path(__file__).resolve().parent
    
    # Check OHI rubrics
    ohi_rubrics = repo_root / "ohi_rubrics"
    assert ohi_rubrics.exists(), "ohi_rubrics directory should exist at repo root"
    assert ohi_rubrics.is_dir(), "ohi_rubrics should be a directory"
    
    # Check for at least one .txt file in ohi_rubrics
    ohi_files = list(ohi_rubrics.glob("*.txt"))
    assert len(ohi_files) > 0, "ohi_rubrics should contain at least one .txt file"
    print(f"  ✓ Found {len(ohi_files)} OHI rubric file(s)")
    
    # Check HPV rubrics
    hpv_rubrics = repo_root / "hpv_rubrics"
    assert hpv_rubrics.exists(), "hpv_rubrics directory should exist at repo root"
    assert hpv_rubrics.is_dir(), "hpv_rubrics should be a directory"
    
    # Check for at least one .txt file in hpv_rubrics
    hpv_files = list(hpv_rubrics.glob("*.txt"))
    assert len(hpv_files) > 0, "hpv_rubrics should contain at least one .txt file"
    print(f"  ✓ Found {len(hpv_files)} HPV rubric file(s)")


def test_path_resolution_logic():
    """Test that the path resolution logic would work correctly."""
    print("\nTesting path resolution logic...")
    
    # Simulate what happens in pages/OHI.py
    script_dir = Path("pages").resolve()
    repo_root = script_dir.parent
    
    # OHI rubrics should be found at repo root
    ohi_search_locations = [
        repo_root / "ohi_rubrics",
        script_dir / "ohi_rubrics"
    ]
    
    ohi_found = None
    for location in ohi_search_locations:
        if location.exists() and location.is_dir():
            ohi_found = location
            break
    
    assert ohi_found is not None, "OHI rubrics should be found"
    assert ohi_found == repo_root / "ohi_rubrics", \
        "OHI rubrics should be found at repo root (first search location)"
    print("  ✓ OHI rubrics would be found at repo root")
    
    # HPV rubrics should be found at repo root
    hpv_search_locations = [
        repo_root / "hpv_rubrics",
        script_dir / "hpv_rubrics"
    ]
    
    hpv_found = None
    for location in hpv_search_locations:
        if location.exists() and location.is_dir():
            hpv_found = location
            break
    
    assert hpv_found is not None, "HPV rubrics should be found"
    assert hpv_found == repo_root / "hpv_rubrics", \
        "HPV rubrics should be found at repo root (first search location)"
    print("  ✓ HPV rubrics would be found at repo root")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Rubric Path Resolution Tests")
    print("=" * 60)
    
    try:
        test_ohi_path_resolution()
        test_hpv_path_resolution()
        test_rubric_directories_exist()
        test_path_resolution_logic()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    
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
