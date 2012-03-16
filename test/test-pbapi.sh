#!/bin/bash

debug=""
pause=""
( echo "$@" | grep -e "-debug" >/dev/null ) && debug="-debug"
( echo "$@" | grep -e "-pause" >/dev/null ) && pause="-pause"

function api() {
	../src/pbapi.py ${debug} "$@" | grep -v 'Request ID'
	exit_code=$?
	if [ -n "${dc_id}" ]; then
		cmd="eval ../src/pbapi.py ${debug} get-datacenter-state -dcid ${dc_id} | grep 'AVAILABLE' 2>&1 >/dev/null ; echo \$?"
		while [ "$(${cmd})" != "0" ]; do
			sleep 2
		done
	fi
	return ${exit_code}
}

function assert_text() {
	args="$@"
	message="$1" ; shift
	condition="$1" ; shift
	output=`api $@`
	if [ ! -z "${debug}" ]; then echo ${output}; fi
	( echo ${output} | grep -e "${condition}" >/dev/null ) && ( assert_passed "${message}" ) || ( assert_text_failed "${message}" "${condition}" "$@" )
	next_test
}

function assert_passed() {
	echo "Passed: $1"
}

function assert_text_failed() {
	message="$1" ; shift
	condition="$1" ; shift
	echo -en "\x07"
	echo -e "\nFailed: ${message}\nCommand: $@\nMissing text: ${condition}\n"
	sleep 1
	echo -en "\x07"
}

function assert_not_text() {
	args="$@"
	message="$1" ; shift
	condition="$1" ; shift
	output=`api $@`
	if [ ! -z "${debug}" ]; then echo ${output}; fi
	( echo ${output} | grep -e "${condition}" >/dev/null ) && ( assert_not_text_failed "${message}" "${condition}" "$@" ) || ( assert_passed "${message}" )
	next_test
}

function assert_not_text_failed() {
	message="$1" ; shift
	condition="$1" ; shift
	echo -en "\x07"
	echo -e "\nFailed: ${message}\nCommand: $@\nFound text: ${condition}\n"
	sleep 1
	echo -en "\x07"
}

function wait_cmd() {
	message="$1"; shift
	cmd="eval $@ 2>&1 >/dev/null; echo \$?"
	echo -n "Waiting ${message} .."
	i=0
	while [ ${i} -le 60 ]; do
		echo -n "."
		if [ "$(${cmd})" == "0" ]; then
			echo " passed."
			next_test
			return 0
		fi
		sleep 3; i=$[ ${i} + 3 ]
	done
	echo "FAILED!"
	next_test
	return 1
}

function next_test() {
	if [ -n "${pause}" ]; then
		echo " = press enter to continue ="
		read
	fi
}

### DEFAULT VALUES ###

name_key="test-2"

default_dc_name="${name_key}-dc"
default_srv_name="${name_key}-srv"
default_sto_name="${name_key}-sto"

success="Operation completed" # do not change this unless it is also changed in src/pb/formatter.py

### ENABLED TESTS ###

test_data_center="1"
test_virtual_server="0"
test_storage="0"

### DATA CENTER ###

create_dc_command="create-datacenter -name ${default_dc_name}"
[ "${test_data_center}" == "1" ] && (
	echo -e "\n === RUNNING DATA CENTER TESTS ===\n"
	dc_id=`api ${create_dc_command} | grep 'ID:' | sed -e 's/.*ID: //'`
	[ "${dc_id}" == "" ] && ( assert_text_failed "Create DataCenter" "ID:" "${create_dc_command}" ) || ( assert_passed "Create DataCenter (${dc_id})" )
	assert_text "Get DataCenter" "${default_dc_name}" get-datacenter -dcid ${dc_id}
	assert_text "Get DataCenter state" "Provisioning state" get-datacenter-state -dcid ${dc_id}
	assert_text "Get all DataCenters" "${dc_id}" get-all-datacenters
	assert_text "Clear empty DataCenter" "${success}" clear-datacenter -dcid ${dc_id}
	srv_id=`api create-server -dcid ${dc_id} -cores 1 -ram 256 -name ${default_srv_name} | grep 'ID:' | sed -e 's/.*ID: //'`
	wait_cmd "for server ${srv_id} to boot" "api get-server -srvid ${srv_id} | grep 'RUNNING'"
	assert_text "Clear DataCenter with server" "${success}" clear-datacenter -dcid ${dc_id}
	wait_cmd "server to delete" "api get-datacenter -dcid ${dc_id} | grep 'Servers (0)'"
	api update-datacenter -dcid ${dc_id} -name ${default_dc_name}2
	assert_text "Rename DataCenter" "${default_dc_name}2" get-datacenter -dcid ${dc_id}
	old_dc_id="${dc_id}"
	dc_id="" # need to do this because the api() function waits for the datacenter $dc_id to be in AVAILABLE state after each command
	assert_text "Delete DataCenter" "${success}" delete-datacenter -dcid ${old_dc_id}
	assert_not_text "Get all DataCenters after deletion" "${old_dc_id}" get-all-datacenters
)

echo "Creating victim data center"
dc_id=`api ${create_dc_command} | grep 'ID:' | sed -e 's/.*ID: //'`

### VIRTUAL SERVER ###

create_srv_command="create-server -dcid ${dc_id} -cores 1 -ram 256 -name ${default_srv_name}"
[ "${test_virtual_server}" == "1" ] && (
	echo -e "\n === RUNNING VIRTUAL SERVER TESTS ===\n"
	srv_id=`api ${create_srv_command} | grep 'ID:' | sed -e 's/.*ID: //'`
	[ "${srv_id}" == "" ] && ( assert_text_failed "Create Server" "ID:" "${create_srv_command}" ) || ( assert_passed "Create Server (${srv_id})" )
	
	assert_text "Get Server" "${default_srv_name}" get-server -srvid "${srv_id}"
	wait_cmd "for server ${srv_id} to boot" "api get-server -srvid ${srv_id} | grep 'RUNNING'"
	assert_text "Reboot Server" "${success}" reboot-server -srvid "${srv_id}"
	wait_cmd "for server ${srv_id} to reboot" "api get-server -srvid ${srv_id} | grep 'RUNNING'"
	assert_text "Delete Server" "${success}" delete-server -srvid "${srv_id}"
)

echo "Creating victim server"
srv_id=`api ${create_srv_command} | grep 'ID:' | sed -e 's/.*ID: //'`
wait_cmd "for server '${srv_id}' to boot" "api get-server -srvid ${srv_id} | grep 'RUNNING'"

### STORAGE ###

create_sto_command="create-storage -dcid ${dc_id} -name ${default_sto_name} -size 1"
[ "${test_storage}" == "1" ] && (
	echo -e "\n === RUNNING STORAGE TESTS ===\n"
	sto_id=`api ${create_sto_command} | grep 'ID:' | sed -e 's/.*ID: //'`
	[ "${sto_id}" == "" ] && ( assert_text_failed "Create Storage" "ID:" "${create_sto_command}" ) || ( assert_passed "Create Storage (${sto_id})" )
	
	assert_text "Get Storage" "${default_sto_name}" get-storage -stoid "${sto_id}"
	wait_cmd "for storage ${sto_id} to be AVAILABLE" "api get-storage -stoid ${sto_id} | grep 'AVAILABLE'"
	assert_text "Connect Storage to Server" "${success}" connect-storage-to-server -stoid ${sto_id} -srvid ${srv_id} -bus ide
	wait_cmd "for storage ${sto_id} to be AVAILABLE" "api get-storage -stoid ${sto_id} | grep 'AVAILABLE'"
	assert_text "Disconnect storage from server" "${success}" disconnect-storage-from-server -stoid ${sto_id} -srvid ${srv_id}
	wait_cmd "for storage ${sto_id} to be AVAILABLE" "api get-storage -stoid ${sto_id} | grep 'AVAILABLE'"
	api update-storage -stoid ${sto_id} -name ${default_dc_name}2
	assert_text "Rename Storage" "${default_dc_name}2" get-storage -stoid ${sto_id}
	wait_cmd "for storage ${sto_id} to be AVAILABLE" "api get-storage -stoid ${sto_id} | grep 'AVAILABLE'"
	assert_text "Delete Storage" "${success}" delete-storage -stoid ${sto_id}
)

echo "Creating victim storage"
sto_id=`api ${create_sto_command} | grep 'ID:' | sed -e 's/.*ID: //'`
wait_cmd "for storage '${sto_id}' to be AVAILABLE" "api get-storage -stoid ${sto_id} | grep 'AVAILABLE'"

### LOAD BALANCER ###


### CLEAN-UP ###

echo -e "\n === CLEANING UP ===\n"

api clear-datacenter -dcid ${dc_id}
wait_cmd "for servers to delete" "api get-datacenter -dcid ${dc_id} | grep 'Servers (0)'"
wait_cmd "for storages to delete" "api get-datacenter -dcid ${dc_id} | grep 'Storages (0)'"
old_dc_id="${dc_id}"
dc_id="" # need to do this because the api() function waits for the datacenter $dc_id to be in AVAILABLE state after each command
api delete-datacenter -dcid ${old_dc_id}
wait_cmd "for datacenter to delete" "api get-all-datacenters | awk '/${old_dc_id}/{found=1;exit} END{exit(found)}'" # wait until text is not found

