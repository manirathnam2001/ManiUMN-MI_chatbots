"""
Test error handling for missing rubric files.

This test validates graceful error handling when rubric files are missing.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path


def test_error_handling_missing_directory():
    """Test that code handles missing rubric directory gracefully."""
    print("Testing error handling for missing rubric directory...")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_script.py"
        
        # Write a minimal test script with our path resolution logic
        test_script = '''
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent if current_file.parent.name == "pages" else current_file.parent

rubrics_dir = None
possible_paths = [
    repo_root / "test_rubrics",
    current_file.parent / "test_rubrics",
]

for path in possible_paths:
    if path.exists() and path.is_dir():
        rubrics_dir = path
        break

if rubrics_dir is None:
    print("ERROR: Rubric directory not found")
    sys.exit(0)  # Expected outcome

print("FAIL: Should not reach here")
sys.exit(1)
'''
        
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        # Run the test script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True
        )
        
        assert "ERROR: Rubric directory not found" in result.stdout, \
            "Should detect missing directory"
        assert result.returncode == 0, "Should exit gracefully"
        
    print("  ✓ Error handling works for missing directory")


def test_error_handling_empty_directory():
    """Test that code handles empty rubric directory gracefully."""
    print("Testing error handling for empty rubric directory...")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_script.py"
        rubrics_dir = Path(tmpdir) / "test_rubrics"
        rubrics_dir.mkdir()
        
        # Write a minimal test script with our rubric loading logic
        test_script = f'''
import sys
from pathlib import Path

rubrics_dir = Path("{rubrics_dir}")

rubric_files = list(rubrics_dir.glob("*.txt"))
if not rubric_files:
    print("ERROR: No rubric files found")
    sys.exit(0)  # Expected outcome

print("FAIL: Should not reach here")
sys.exit(1)
'''
        
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        # Run the test script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True
        )
        
        assert "ERROR: No rubric files found" in result.stdout, \
            "Should detect empty directory"
        assert result.returncode == 0, "Should exit gracefully"
        
    print("  ✓ Error handling works for empty directory")


def test_path_resolution_from_pages():
    """Test that path resolution correctly identifies repo root from pages/ subdirectory."""
    print("Testing path resolution from pages/ subdirectory...")
    
    # Create temporary test environment that mimics repo structure
    with tempfile.TemporaryDirectory() as tmpdir:
        pages_dir = Path(tmpdir) / "pages"
        pages_dir.mkdir()
        rubrics_dir = Path(tmpdir) / "test_rubrics"
        rubrics_dir.mkdir()
        
        # Create a test rubric file
        test_rubric = rubrics_dir / "test.txt"
        test_rubric.write_text("Test rubric content")
        
        test_file = pages_dir / "test_script.py"
        
        # Write a test script that mimics our path resolution
        test_script = f'''
import sys
from pathlib import Path

current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent if current_file.parent.name == "pages" else current_file.parent

print(f"Current file parent name: {{current_file.parent.name}}")
print(f"Repo root: {{repo_root}}")

rubrics_dir = None
possible_paths = [
    repo_root / "test_rubrics",
    current_file.parent / "test_rubrics",
]

for path in possible_paths:
    print(f"Checking: {{path}} - exists: {{path.exists()}}")
    if path.exists() and path.is_dir():
        rubrics_dir = path
        break

if rubrics_dir is None:
    print("FAIL: Could not find rubrics directory")
    sys.exit(1)

print(f"SUCCESS: Found rubrics at {{rubrics_dir}}")
rubric_files = list(rubrics_dir.glob("*.txt"))
print(f"Found {{len(rubric_files)}} rubric files")

if len(rubric_files) == 0:
    print("FAIL: No rubric files")
    sys.exit(1)

sys.exit(0)
'''
        
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        # Run the test script
        import subprocess
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True
        )
        
        print(f"  Output: {result.stdout}")
        assert "SUCCESS: Found rubrics" in result.stdout, \
            "Should find rubrics from pages/ subdirectory"
        assert result.returncode == 0, "Should succeed"
        
    print("  ✓ Path resolution works correctly from pages/")


if __name__ == "__main__":
    print("=" * 60)
    print("Error Handling Tests for Missing Rubrics")
    print("=" * 60)
    
    try:
        test_error_handling_missing_directory()
        test_error_handling_empty_directory()
        test_path_resolution_from_pages()
        
        print("=" * 60)
        print("✓ All error handling tests passed!")
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
