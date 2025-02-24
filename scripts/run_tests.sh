#!/bin/bash
#
# Run project tests
#
# NOTE: This script expects to be run from the project root with
# ./scripts/run_tests.sh

set -o pipefail

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  TEST=$3

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$TEST failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$TEST passed\033[0m"
  fi
}

if [[ -z "$VIRTUAL_ENV" ]] && [[ -d venv ]]; then
  source ./venv/bin/activate
fi

flake8 .
display_result $? 1 "Code style check"

isort --check-only ./app ./tests
display_result $? 2 "Import order check"

npm test
display_result $? 3 "Javascript tests have"

py.test -n auto --maxfail=10 tests/
display_result $? 4 "Unit tests have"
