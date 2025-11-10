#!/usr/bin/env python3
"""Smoke test for nmsi package to verify basic functionality after installation."""

import sys


def test_import():
    """Test that the nmsi module can be imported."""
    try:
        import nmsi
        print("✓ Successfully imported nmsi module")
        return True
    except ImportError as e:
        print(f"✗ Failed to import nmsi module: {e}")
        return False

def test_main_function():
    """Test that main function exists and is callable."""
    try:
        import nmsi
        assert hasattr(nmsi, 'main'), "nmsi module should have main function"
        assert callable(nmsi.main), "nmsi.main should be callable"
        print("✓ main() function exists and is callable")
        return True
    except Exception as e:
        print(f"✗ Main function test failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("Running smoke tests for nmsi package...")
    print()
    
    tests = [
        test_import,
        test_main_function,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} raised exception: {e}")
            failed += 1
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("Smoke tests failed!")
        sys.exit(1)
    else:
        print("All smoke tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

