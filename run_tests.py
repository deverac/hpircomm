import sys
import unittest

import src.log

def show_test_names(suites):
    for suite in suites:
        for tests in suite:
            for test in tests:
                print test


def run_tests(args):
    """
    Args:

        --help, -h   Print this help and exit.

        --show-xs    Print excluded and skipped test names after test results


    This script adds the following features to Python's unittest framework:

      1) Filenames that contain tests can be named 't_*.py'. The default
         naming convention, 'test*.py', will also work.

      2) Test names that start with 'ftest_' will be run and all other tests
         will be skipped.

      3) Test names that start with 'xtest_' will be excluded and all other
         tests will be run. This is similar, but not equivalent, to adding the
         '@unittest.skip(...)' annotation to the test.

    If a test has a skip-annotation (e.g. 'skipIf') that evaluates to True
    and the name begins with 'ftest_', the test will be selected for running,
    but when run by the unittest framework, the test will be skipped.

    Python's unittest framework includes skipped tests in the run total. So,
    for example, if there are five tests and two have been annotated with
    '@unittest.skip(...)', then the unittest framework will 'run' all five
    tests, and report that five tests have been run, but only three tests
    will have actually been executed.

    Using '@patch(...)' on a class works only when the test name begins with
    'test_' i.e. Patching a class fails on test names that start with 'ftest_'
    or 'xtest_'. A work-around is to use 'patch()', 'addCleanup()', and
    'start()' in the 'setUp()' test method.
    """
    test_dir = 'tests'
    pattern = 't_*.py'
    show_xs = False
    skipped_tests = None

    for arg in args:
        if arg == '--show-xs':
            show_xs = True
        elif arg == '--help' or arg == '-h':
            print run_tests.__doc__
            return

    loader_ftest = unittest.TestLoader()
    loader_ftest.testMethodPrefix = "ftest_"
    suite_ftest = loader_ftest.discover(test_dir, pattern=pattern)
    suite_ftest.addTests(loader_ftest.discover(test_dir))


    loader_xtest = unittest.TestLoader()
    loader_xtest.testMethodPrefix = "xtest_"
    suite_xtest = loader_xtest.discover(test_dir, pattern=pattern)
    suite_xtest.addTests(loader_xtest.discover(test_dir))


    loader_test = unittest.loader.defaultTestLoader
    suite_test = loader_test.discover(test_dir, pattern=pattern)
    suite_test.addTests(loader_test.discover(test_dir))


    src.log.set_log_level(1) # Suppress output from showing

    if suite_ftest.countTestCases() > 0:
        skipped_tests = unittest.TextTestRunner(verbosity=2).run(suite_ftest).skipped
        excluded_tests_count = suite_xtest.countTestCases() + suite_test.countTestCases()
    else:
        skipped_tests = unittest.TextTestRunner(verbosity=2).run(suite_test).skipped
        excluded_tests_count = suite_xtest.countTestCases()

    if excluded_tests_count > 0:
        print('\nExcluded {} tests:'.format(excluded_tests_count))
        if show_xs:
            show_test_names(suite_xtest)

    if skipped_tests and show_xs:
        print('\nSkipped {} tests:'.format(len(skipped_tests)))
        for name, reason in skipped_tests:
            print name, reason

if __name__ == '__main__':
    run_tests(sys.argv[1:])
