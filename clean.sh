#!/bin/bash
# Delete auto-generated files.
rm -f .coverage
rm -rf htmlcov
rm -f *.pyc
rm -f ./src/*.pyc
rm -rf ./src/__pycache__
rm -f ./tests/*.pyc
