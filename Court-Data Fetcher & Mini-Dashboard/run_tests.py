"""
Test runner for Court Data Fetcher application
"""

import os
import sys
import unittest
import coverage

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_tests_with_coverage():
    """Run tests with coverage reporting"""
    # Initialize coverage
    cov = coverage.Coverage()
    cov.start()
    
    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = 'tests'
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\n" + "="*50)
        print("COVERAGE REPORT")
        print("="*50)
        cov.report()
        
        # Generate HTML coverage report
        try:
            cov.html_report(directory='htmlcov')
            print(f"\nHTML coverage report generated in 'htmlcov' directory")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")
        
        # Return exit code based on test results
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def run_tests_simple():
    """Run tests without coverage"""
    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = 'tests'
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def run_specific_test(test_name):
    """Run a specific test"""
    try:
        # Load specific test
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(f'tests.{test_name}')
        
        # Run test
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        print(f"Error running test {test_name}: {e}")
        return 1

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test runner for Court Data Fetcher')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--simple', action='store_true', help='Run tests without coverage')
    parser.add_argument('--test', type=str, help='Run specific test (e.g., test_app.HomePageTestCase)')
    parser.add_argument('--install-deps', action='store_true', help='Install test dependencies')
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        os.system('pip install coverage')
        print("Test dependencies installed.")
        return 0
    
    # Create tests directory if it doesn't exist
    os.makedirs('tests', exist_ok=True)
    
    # Create __init__.py in tests directory
    init_file = os.path.join('tests', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Test package\n')
    
    # Run specific test
    if args.test:
        print(f"Running specific test: {args.test}")
        return run_specific_test(args.test)
    
    # Run tests with coverage
    if args.coverage:
        try:
            import coverage
            print("Running tests with coverage...")
            return run_tests_with_coverage()
        except ImportError:
            print("Coverage not installed. Run with --install-deps first, or use --simple")
            return 1
    
    # Default: run simple tests
    print("Running tests...")
    return run_tests_simple()

if __name__ == '__main__':
    sys.exit(main())