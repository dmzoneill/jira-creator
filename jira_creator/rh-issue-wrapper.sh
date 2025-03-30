#!/bin/bash
# Get the real location of this script (even if symlinked)
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
PROJECT_ROOT="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

cd "$PROJECT_ROOT" || exit 1
CLI_NAME=$(basename "$0")
export CLI_NAME
PIPENV_VERBOSITY=-1 exec pipenv run python rh_jira.py "$@"

