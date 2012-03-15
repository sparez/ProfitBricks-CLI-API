#!/bin/bash

# Helpers
version="1.2" # pb api/cli version
tbold=`tput bold` # begin writing bold to stdout
tnormal=`tput sgr0` # end writing bold to stdout
help=""\
"${tbold}ProfitBricks API CLI v${version} Copyright 2012 ProfitBricks GmbH${tnormal}, licensed under Apache 2.0 ( http://www.apache.org/licenses/LICENSE-2.0 )\n"\
"Type 'exit' to leave, 'help' for help, 'list' to list available operations, 'last' to repeat your last command, 'use DCID' to set a default working datacenter." # help text that appears at start-up
home=$(dirname $(readlink -f $0)) # location of pbapi.py
last_operation="" # last operation the user executed (internal commands not taken into account)
default_dc=""
prompt="ProfitBricks> "
wait_dc=""
wait_dc_sleep="2"

echo -e "\n$help"

function parse_internal() {
	cmd="${command% *}"
	args=`( echo "${command}" | grep ' ' >/dev/null ) && echo "${command#* }"`
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
			return 0
			;;
		"wait")
			wait_dc="$(echo ${args::1} | tr '[A-Z]' '[a-z]')"
			if [ "$wait_dc" == "y" ]; then
				if [ -n "$default_dc" ]; then
					echo "All future commands will wait for current data center to become active"
				else
					echo "Waiting for data center to become active has been enabled, but will only function if a default data center is selected by the 'use' command"
				fi
			else
				echo "Waiting for data center provisioning disabled"
			fi
			command=""
			return 0
			;;
		"help" | "?")
			man -l pbapi.1
			echo -e "$help"
			command=""
			return 0
			;;
		"last")
			echo "Issuing last command: $last_operation"
			command=${last_operation}
			return 2
			;;
		"exit" | "quit" | "bye")
			echo "Good bye!"
			exit
			;;
	esac
	return 1
}

function execute_operation() {
	last_operation=${command}
	eval "${home}/pbapi.py" "${default_args}" "${default_dc}" "${command}" ; exit_code=$?
	#[ "${exit_code}" != "0" ] && echo "Exit code: ${exit_code}"
	[ "${wait_dc}" == "y" ] && [ -n "${default_dc}" ] && (
		until [ "$(${home}/pbapi.py ${default_args} ${default_dc} get-datacenter-state | grep 'AVAILABLE\|resource does not exist' | wc -l)" -gt 0 ]; do
			echo -n "."
			sleep ${wait_dc_sleep}
		done
		echo ""
	) || echo "-"
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

# Initialize
command="wait yes" ; parse_internal ; command=""

echo ""
# Loop until 'exit'
while [ true ]; do
	read -e -p "${tbold}${prompt}${tnormal}" command
	parse_internal || execute_operation
done

