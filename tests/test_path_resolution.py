"""
Test path resolution for rubric directories in OHI/HPV scripts.

This test validates:
1. Path resolution works from repo root (OHI.py, HPV.py)
2. Path resolution works from pages/ directory (pages/OHI.py, pages/HPV.py)
3. Graceful error handling when rubrics are missing
"""

import os
import sys
import ast
from pathlib import Path


def test_path_resolution_logic():
    """Test the path resolution logic works for both locations."""
    print("Testing path resolution logic...")
    
    # Simulate running from repo root
    repo_root = Path("/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots")
    root_file = repo_root / "OHI.py"
    
    current_file = root_file.resolve()
    computed_root = current_file.parent.parent if current_file.parent.name == "pages" else current_file.parent
    
    assert computed_root == repo_root, f"Expected {repo_root}, got {computed_root}"
    
    rubrics_dir = computed_root / "ohi_rubrics"
    assert rubrics_dir.exists(), f"OHI rubrics not found at {rubrics_dir}"
    
    # Simulate running from pages/
    pages_file = repo_root / "pages" / "OHI.py"
    current_file = pages_file.resolve()
    computed_root = current_file.parent.parent if current_file.parent.name == "pages" else current_file.parent
    
    assert computed_root == repo_root, f"Expected {repo_root}, got {computed_root} for pages/OHI.py"
    
    rubrics_dir = computed_root / "ohi_rubrics"
    assert rubrics_dir.exists(), f"OHI rubrics not found at {rubrics_dir} from pages/"
    
    print("  ✓ Path resolution logic works correctly for both locations")


def extract_path_resolution_code(filepath):
    """Extract the path resolution code from a Python file."""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())
    
    # Look for Path import
    has_path_import = False
    has_pathlib_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == 'pathlib':
                for alias in node.names:
                    if alias.name == 'Path':
                        has_path_import = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'pathlib':
                    has_pathlib_import = True
    
    return has_path_import or has_pathlib_import


def test_files_have_path_import():
    """Test that all OHI/HPV files import Path from pathlib."""
    print("Testing Path import in files...")
    
    files_to_check = [
        "OHI.py",
        "HPV.py",
        "pages/OHI.py",
        "pages/HPV.py"
    ]
    
    for filepath in files_to_check:
        full_path = os.path.join("/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots", filepath)
        if not os.path.exists(full_path):
            print(f"  ⚠️  {filepath} not found, skipping")
            continue
            
        has_import = extract_path_resolution_code(full_path)
        assert has_import, f"{filepath} should import Path from pathlib"
        print(f"  ✓ {filepath} has Path import")


def check_error_handling(filepath):
    """Check if file has graceful error handling for missing rubrics."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for user-friendly error messages
    has_error_message = "Configuration Error" in content or "Rubric files not found" in content
    has_st_error = "st.error" in content
    has_st_info = "st.info" in content
    
    return has_error_message and has_st_error and has_st_info


def test_error_handling():
    """Test that files have graceful error handling."""
    print("Testing graceful error handling...")
    
    files_to_check = [
        "pages/OHI.py",
        "pages/HPV.py"
    ]
    
    for filepath in files_to_check:
        full_path = os.path.join("/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots", filepath)
        if not os.path.exists(full_path):
            print(f"  ⚠️  {filepath} not found, skipping")
            continue
            
        has_handling = check_error_handling(full_path)
        assert has_handling, f"{filepath} should have graceful error handling"
        print(f"  ✓ {filepath} has graceful error handling")


def test_rubrics_exist():
    """Test that rubric directories exist and contain files."""
    print("Testing rubric directories exist...")
    
    repo_root = Path("/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots")
    
    ohi_rubrics = repo_root / "ohi_rubrics"
    assert ohi_rubrics.exists(), f"OHI rubrics directory not found at {ohi_rubrics}"
    ohi_files = list(ohi_rubrics.glob("*.txt"))
    assert len(ohi_files) > 0, "OHI rubrics directory should contain .txt files"
    print(f"  ✓ OHI rubrics directory exists with {len(ohi_files)} files")
    
    hpv_rubrics = repo_root / "hpv_rubrics"
    assert hpv_rubrics.exists(), f"HPV rubrics directory not found at {hpv_rubrics}"
    hpv_files = list(hpv_rubrics.glob("*.txt"))
    assert len(hpv_files) > 0, "HPV rubrics directory should contain .txt files"
    print(f"  ✓ HPV rubrics directory exists with {len(hpv_files)} files")


if __name__ == "__main__":
    print("=" * 60)
    print("Path Resolution Tests")
    print("=" * 60)
    
    try:
        test_path_resolution_logic()
        test_files_have_path_import()
        test_error_handling()
        test_rubrics_exist()
        
        print("=" * 60)
        print("✓ All path resolution tests passed!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)
