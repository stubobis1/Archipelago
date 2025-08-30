#!/usr/bin/env python3
"""
Quick test to see what's broken with our test imports
"""
import sys

try:
    print("Testing import of test_version_compatibility...")
    from worlds.poe.test.test_version_compatibility import TestVersionConstants
    print("✓ TestVersionConstants imported successfully")
    
    # Try to create an instance
    test_instance = TestVersionConstants()
    print("✓ TestVersionConstants instance created")
    
    # Try the setUp method
    test_instance.setUp()
    print("✓ setUp method executed")
    
    # Try one test method
    test_instance.test_poe_version_format()
    print("✓ test_poe_version_format executed")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except AttributeError as e:
    print(f"❌ Attribute error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting POE_VERSION import...")
    from worlds.poe.Version import POE_VERSION
    print(f"✓ POE_VERSION: {POE_VERSION}")
except Exception as e:
    print(f"❌ POE_VERSION import error: {e}")

try:
    print("\nTesting PathOfExileContext import...")
    from worlds.poe.Client import PathOfExileContext
    print("✓ PathOfExileContext imported")
except Exception as e:
    print(f"❌ PathOfExileContext import error: {e}")
