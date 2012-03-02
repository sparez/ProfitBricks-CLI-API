#!/bin/bash

if [ -e default.auth ]; then
	default_args="-auth default.auth"
else
	#default_args="-auth ../../costi.auth"
	read -e -p "Default arguments (usually -u user -p pass): " default_args
fi

echo "Type 'exit' to leave"
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

