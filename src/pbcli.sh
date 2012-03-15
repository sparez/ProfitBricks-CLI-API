#!/bin/bash

# Helpers
version="1.1"
tbold=`tput bold`
tnormal=`tput sgr0`
help="${tbold}ProfitBricks API CLI v${version} Copyright 2012 ProfitBricks GmbH${tnormal}, licensed under Apache 2.0 ( http://www.apache.org/licenses/LICENSE-2.0 )\nType 'exit' to leave, 'help' for help, 'list' to list available operations or 'last' to repeat your last command."
home=$(dirname $(readlink -f $0))
last_command=""
default_dc=""
last_command=""
prompt="ProfitBricks> "
wait_dc=""

echo -e "\n$help"

function parse_internal() {
	cmd="$1" ; shift
	args="$@"
	case "${cmd}" in
		"use")
			if [ -n "${args}" ]; then
				default_dc="-dcid ${args}"
				prompt="${args}> "
				echo "Using ${args} as default datacenter"
			else
				default_dc=""
				prompt="ProfitBricks> "
				echo "Removed default datacenter"
			fi
			echo "-"
			command=""
			;;
		"wait")
			wait_dc="$(echo ${args::1} | tr '[A-Z]' '[a-z]')"
			command=""
			;;
	esac
}

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
while [ true ]; do
	read -e -p "${tbold}${prompt}${tnormal}" command
	
	parse_internal ${command}
	
	case "${command}" in
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
			echo "Issuing last command: $last_command"
			command=${last_command}
			;& # fall through
		*)
			last_command=${command}
			${home}/pbapi.py ${default_args} ${default_dc} ${command} ; exit_code=$?
			[ "${exit_code}" != "0" ] && echo "Exit code: ${exit_code}"
			[ "${wait_dc}" == "y" ] && [ -n "${default_dc}" ] && (
				until [ "$(${home}/pbapi.py ${default_args} ${default_dc} get-datacenter-state | grep 'AVAILABLE\|resource does not exist' | wc -l)" -gt 0 ]; do
					echo -n "."
					sleep 1
				done
				echo ""
			) || echo "-"
			;;
	esac
done

