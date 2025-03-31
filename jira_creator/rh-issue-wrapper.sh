#!/bin/bash

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

if [[ "$1" == "--_completion" ]]; then
  # Register autocomplete just for this CLI call
  PIPENV_VERBOSITY=-1 exec pipenv run register-python-argcomplete rh_jira.py
else
  PIPENV_VERBOSITY=-1 exec pipenv run python rh_jira.py "$@"
fi
