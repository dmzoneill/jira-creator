#!/usr/bin/env bash

count=$(grep -r 'os.get' jira_creator/* | wc -l)

# Check if the count is 1
if [ "$count" -ne 1 ]; then
    echo "The value of os.get occurrences is > 1."
    echo "Are you using EnvFetcher?"
    exit 1
fi

count=$(grep -r "raise Exce" jira_creator/ | wc -l)

# Check if the count is 1
if [ "$count" -gt 0 ]; then
    echo "Raising bare exceptions is not allowed"
    exit 1
fi

count=$(grep -r "raise (" jira_creator/ | wc -l)

# Check if the count is 1
if [ "$count" -gt 0 ]; then
    echo "Superflous brackets"
    exit 1
fi

count=$(grep -r "# pylint" * | wc -l)

# Check if the count is 1
if [ "$count" -gt 23 ]; then
    echo "Pylint creep"
    exit 1
fi

exit 0