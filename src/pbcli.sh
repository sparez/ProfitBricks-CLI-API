#!/bin/bash

version="1.1"
help="ProfitBricks API CLI Copyright 2012 ProfitBricks GmbH, licensed under Apache 2.0 ( http://www.apache.org/licenses/LICENSE-2.0 )\nType 'exit' to leave, 'help' for help, 'list' to list available operations or 'last' to repeat your last command."

echo -e "\n$help"

# Read default arguments
echo ""
if [ -e default.auth ]; then
	default_args="-auth default.auth"
	echo "Using -auth default.auth as default arguments"
else
	read -e -p "Default arguments (usually -u user -p pass): " default_args
fi
echo ""

# Enable autocomplete
ops=`./pbapi.py list`
set -o emacs
bind 'set show-all-if-ambiguous on'
bind 'set completion-ignore-case on'
bind 'TAB:dynamic-complete-history'
for i in $ops; do
    history -s $i
done
compgen -W "$ops" "/"

# Loop until 'exit'
last=""
while [ true ]; do
	read -e -p "ProfitBricks> " command
	
	case "$command" in
		"")
			# ignore
			;;
		"help" | "?")
			man -l pbapi.1
			echo -e "$help"
			;;
		"exit" | "quit" | "bye")
			break
			;;
		"last")
			echo "Issuing last command: $last"
			command=$last
			;& # fall through
		*)
			last=$command
			./pbapi.py $default_args $command ; exit_code=$?
			if [ "$exit_code" != "0" ]; then echo "Exit code: $exit_code"; fi
			;;
	esac
done

