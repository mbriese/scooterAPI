"""
Test Runner Script
Runs all tests for the Scooter API

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py --unit    # Run only unit tests (validators)
    python run_tests.py --api     # Run only API tests (requires server)
"""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Run Scooter API tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--api', action='store_true', help='Run only API tests')
    args = parser.parse_args()
    
    all_passed = True
    
    # If no specific test type, run all
    run_unit = args.unit or (not args.unit and not args.api)
    run_api = args.api or (not args.unit and not args.api)
    
    if run_unit:
        print("\n" + "="*60)
        print(" RUNNING UNIT TESTS (Validators)")
        print("="*60)
        from tests.test_validators import run_all_tests
        if not run_all_tests():
            all_passed = False
    
    if run_api:
        print("\n" + "="*60)
        print(" RUNNING API TESTS (Integration)")
        print("="*60)
        from tests.test_api import run_all_api_tests
        if not run_all_api_tests():
            all_passed = False
    
    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print(" [SUCCESS] ALL TEST SUITES PASSED!")
    else:
        print(" [FAILED] SOME TESTS FAILED - Please review above")
    print("="*60 + "\n")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

