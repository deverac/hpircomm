# Run coverage tests. The 'coverage' module must be installed.
import subprocess

# If any 'check_call' exits with an error, this script will terminate.

# Run tests
subprocess.check_call(['python', '-m', 'coverage', 'run', '--branch', '--source=src', 'run_tests.py'])

# Generate coverage stats
subprocess.check_call(['python', '-m', 'coverage', 'report', '--show-missing'])

# Generate HTML report of coverage stats
subprocess.check_call(['python', '-m', 'coverage', 'html'])

print '\nGenerated HTML coverage file at ./htmlcov/index.html\n'
