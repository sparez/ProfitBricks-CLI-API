#!/bin/bash

echo ""

if [ -e default.auth ]; then
	default_args="-auth default.auth"
	echo "Using -auth default.auth as default arguments"
else
	read -e -p "Default arguments (usually -u user -p pass): " default_args
fi

echo "Type 'exit' to leave or 'help' for help."
echo ""
while [ true ]; do
	read -e -p "ProfitBricks> " command
	
	case "$command" in
		"help")
			man -l pbapi.1
			;;
		"exit" | "quit" | "bye")
			break
			;;
		*)
			./pbapi.py $default_args $command
			;;
	esac
done

