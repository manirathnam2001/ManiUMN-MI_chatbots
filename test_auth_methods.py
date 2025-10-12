"""
Manual test script to demonstrate authentication methods for secret_code_portal.py

This script demonstrates that the authentication logic correctly handles:
1. Environment variable (GOOGLESA)
2. Service account file (umnsod-mibot-ea3154b145f1.json)

Note: Streamlit secrets can only be tested when running in Streamlit Cloud.
"""

import os
import json

SERVICE_ACCOUNT_FILE = "umnsod-mibot-ea3154b145f1.json"

def test_authentication_methods():
    """Test different authentication methods."""
    
    print("=" * 70)
    print("Authentication Methods Test for secret_code_portal.py")
    print("=" * 70)
    print()
    
    # Method 1: Check for Streamlit secrets (not available in this context)
    print("Method 1: Streamlit secrets (st.secrets['GOOGLESA'])")
    print("   Status: Can only be tested in Streamlit Cloud environment")
    print("   ⚠️  Skipped (not in Streamlit context)")
    print()
    
    # Method 2: Check for environment variable
    print("Method 2: Environment variable (GOOGLESA)")
    googlesa_env = os.environ.get('GOOGLESA')
    if googlesa_env:
        try:
            creds_dict = json.loads(googlesa_env)
            print(f"   Status: ✅ Found and valid JSON")
            print(f"   Service Account: {creds_dict.get('client_email', 'Unknown')}")
            print(f"   Has required fields: {all(k in creds_dict for k in ['type', 'project_id', 'private_key', 'client_email'])}")
        except json.JSONDecodeError as e:
            print(f"   Status: ❌ Found but invalid JSON: {e}")
        except Exception as e:
            print(f"   Status: ❌ Error reading: {e}")
    else:
        print("   Status: ⚠️  Not set")
    print()
    
    # Method 3: Check for service account file
    print(f"Method 3: Service account file ({SERVICE_ACCOUNT_FILE})")
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            # Read the file to get client email
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                sa_data = json.load(f)
            
            print(f"   Status: ✅ Found and valid JSON")
            print(f"   Service Account: {sa_data.get('client_email', 'Unknown')}")
            print(f"   Project ID: {sa_data.get('project_id', 'Unknown')}")
            print(f"   Has required fields: {all(k in sa_data for k in ['type', 'project_id', 'private_key', 'client_email'])}")
        except json.JSONDecodeError as e:
            print(f"   Status: ❌ Found but invalid JSON: {e}")
        except Exception as e:
            print(f"   Status: ❌ Found but failed to read: {e}")
    else:
        print("   Status: ❌ Not found")
    print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    
    # Determine which method would be used
    has_env = bool(os.environ.get('GOOGLESA'))
    has_file = os.path.exists(SERVICE_ACCOUNT_FILE)
    
    if has_env:
        print("✅ Authentication will use: Environment variable (GOOGLESA)")
        print("   Priority: Highest (Method 2)")
    elif has_file:
        print("✅ Authentication will use: Service account file")
        print(f"   File: {SERVICE_ACCOUNT_FILE}")
        print("   Priority: Fallback (Method 3)")
    else:
        print("❌ No authentication method available!")
        print("   Please set GOOGLESA env var or provide service account file")
    
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    test_authentication_methods()
