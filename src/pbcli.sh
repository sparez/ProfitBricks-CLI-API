#!/bin/bash

version="1.1"
help="ProfitBricks API CLI v${version} Copyright 2012 ProfitBricks GmbH, licensed under Apache 2.0 ( http://www.apache.org/licenses/LICENSE-2.0 )\nType 'exit' to leave, 'help' for help, 'list' to list available operations or 'last' to repeat your last command."

echo -e "\n$help"

# Read default arguments
echo ""
default_args="$@"
if [ -z "$default_args" ]; then
	if [ -f "default.auth" ]; then
		echo "Found default.auth file, no default arguments needed"
	else
		read -e -p "Default arguments (-u user -p pass | -auth authfile): " default_args
	fi
else
	echo "Using custom default arguments"
fi
echo ""

# Enable autocomplete
ops=`./pbapi.py list-simple`
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
			echo ""
			;;
	esac
done

