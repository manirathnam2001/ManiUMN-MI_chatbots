#!/usr/bin/env python3
"""
Test script to verify PHP utilities integration with existing Python MI chatbots.
This script tests that the PHP utilities maintain compatibility with the existing
Python scoring system and can process the same feedback formats.
"""

import subprocess
import json
import os
import sys

def test_php_feedback_compatibility():
    """Test that PHP FeedbackUtils produces same results as Python scoring_utils"""
    print("🧪 Testing PHP FeedbackUtils compatibility with Python scoring...")
    
    try:
        # Import existing Python utilities
        sys.path.append('/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots')
        from scoring_utils import MIScorer
        from feedback_template import FeedbackFormatter
        
        # Sample feedback that both systems should parse identically
        sample_feedback = """
1. COLLABORATION (7.5 pts): Met - Excellent rapport building and partnership approach.
2. EVOCATION (7.5 pts): Partially Met - Good exploration of motivations but could go deeper.
3. ACCEPTANCE (7.5 pts): Met - Strong respect for autonomy and reflective listening.
4. COMPASSION (7.5 pts): Met - Demonstrated warmth and non-judgmental approach.
        """
        
        # Test Python scoring
        print("  📊 Testing Python scoring...")
        python_scores = MIScorer.parse_feedback_scores(sample_feedback)
        python_total = MIScorer.calculate_total_score(python_scores)
        
        print(f"     Python found {len(python_scores)} components")
        print(f"     Python total score: {python_total}/30.0")
        
        # Test filename generation compatibility
        python_filename = FeedbackFormatter.create_download_filename("John Doe", "HPV", "Sarah")
        print(f"     Python filename: {python_filename}")
        
        print("  ✅ Python utilities working correctly")
        
        # Create a simple PHP test to verify compatibility
        php_test_script = """<?php
require_once 'FeedbackUtils.php';

$sample_feedback = '
1. COLLABORATION (7.5 pts): Met - Excellent rapport building and partnership approach.
2. EVOCATION (7.5 pts): Partially Met - Good exploration of motivations but could go deeper.  
3. ACCEPTANCE (7.5 pts): Met - Strong respect for autonomy and reflective listening.
4. COMPASSION (7.5 pts): Met - Demonstrated warmth and non-judgmental approach.
';

$breakdown = FeedbackUtils::getScoreBreakdown($sample_feedback);
$filename = FeedbackUtils::generateFilename('HPV', 'John Doe', 'Sarah');

echo json_encode([
    'component_count' => count($breakdown['components']),
    'total_score' => $breakdown['total_score'],
    'percentage' => $breakdown['percentage'],
    'performance_level' => $breakdown['performance_level'],
    'filename' => $filename
]);
?>"""
        
        # Write and execute PHP test
        php_test_file = '/tmp/test_php_compatibility.php'
        with open(php_test_file, 'w') as f:
            f.write(php_test_script)
        
        print("  🔧 Testing PHP scoring...")
        result = subprocess.run(['php', php_test_file], capture_output=True, text=True, 
                              cwd='/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots/src/utils')
        
        if result.returncode == 0:
            php_data = json.loads(result.stdout.strip())
            
            print(f"     PHP found {php_data['component_count']} components")
            print(f"     PHP total score: {php_data['total_score']}/30.0")
            print(f"     PHP percentage: {php_data['percentage']}%") 
            print(f"     PHP performance level: {php_data['performance_level']}")
            print(f"     PHP filename: {php_data['filename']}")
            
            # Compare results
            compatibility_check = {
                'component_count': len(python_scores) == php_data['component_count'],
                'total_score': abs(python_total - php_data['total_score']) < 0.1,
                'filename_format': python_filename == php_data['filename']
            }
            
            print("  📋 Compatibility Check:")
            for check, passed in compatibility_check.items():
                status = "✅" if passed else "❌"
                print(f"     {status} {check}: {'PASS' if passed else 'FAIL'}")
            
            if all(compatibility_check.values()):
                print("  🎉 PHP utilities are fully compatible with Python implementation!")
                return True
            else:
                print("  ⚠️  Some compatibility issues found")
                return False
                
        else:
            print(f"  ❌ PHP test failed: {result.stderr}")
            return False
            
    except ImportError as e:
        print(f"  ⚠️  Python utilities not available: {e}")
        print("  📄 This is expected if running outside the full environment")
        return None
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists('/tmp/test_php_compatibility.php'):
            os.remove('/tmp/test_php_compatibility.php')

def test_database_schema():
    """Test that database schema is valid"""
    print("\n🗄️ Testing database schema...")
    
    schema_file = '/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots/database/mi_sessions.sql'
    
    if not os.path.exists(schema_file):
        print("  ❌ Schema file not found")
        return False
    
    with open(schema_file, 'r') as f:
        schema_content = f.read()
    
    # Check for required tables
    required_tables = ['sessions', 'messages', 'feedback', 'pdf_reports', 'activity_log', 'performance_metrics']
    tables_found = []
    
    for table in required_tables:
        if f"CREATE TABLE IF NOT EXISTS {table}" in schema_content:
            tables_found.append(table)
    
    print(f"  📊 Found {len(tables_found)}/{len(required_tables)} required tables")
    
    for table in required_tables:
        status = "✅" if table in tables_found else "❌"
        print(f"     {status} {table}")
    
    # Check for views
    views_found = schema_content.count('CREATE OR REPLACE VIEW')
    print(f"  📋 Found {views_found} views")
    
    # Check for indexes
    indexes_found = schema_content.count('CREATE INDEX')
    print(f"  🔍 Found {indexes_found} additional indexes")
    
    success = len(tables_found) == len(required_tables)
    
    if success:
        print("  ✅ Database schema is complete and valid")
    else:
        print("  ❌ Database schema is missing required tables")
    
    return success

def test_file_structure():
    """Test that all required files are present"""
    print("\n📁 Testing file structure...")
    
    base_path = '/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots'
    
    required_files = [
        'database/mi_sessions.sql',
        'src/utils/FeedbackUtils.php',
        'src/utils/Logger.php', 
        'src/utils/SessionStorage.php',
        'src/utils/PdfGenerator.php',
        'src/utils/README.md',
        'src/utils/example_integration.php'
    ]
    
    files_found = []
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            files_found.append(file_path)
            file_size = os.path.getsize(full_path)
            print(f"  ✅ {file_path} ({file_size:,} bytes)")
        else:
            print(f"  ❌ {file_path} (missing)")
    
    success = len(files_found) == len(required_files)
    print(f"\n  📊 Found {len(files_found)}/{len(required_files)} required files")
    
    if success:
        print("  ✅ All required files are present")
    else:
        print("  ❌ Some required files are missing")
    
    return success

def main():
    """Run all integration tests"""
    print("🎯 MI Chatbots PHP Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Database Schema", test_database_schema), 
        ("PHP Compatibility", test_php_feedback_compatibility)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    
    passed = 0
    total = 0
    
    for test_name, result in results.items():
        if result is not None:
            total += 1
            if result:
                passed += 1
                print(f"✅ {test_name}: PASS")
            else:
                print(f"❌ {test_name}: FAIL")
        else:
            print(f"⚠️  {test_name}: SKIPPED")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total and total > 0:
        print("\n🎉 All tests passed! PHP utilities are ready for production use.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the results above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)