#!/bin/bash

debug=""
( echo "$@" | grep -e "-debug" >/dev/null ) && debug="-debug"

function api() {
	../src/pbapi.py "$debug" -auth default.auth "$@" 2>&1
	exit_code=$?
	if [ "$exit_code" != "0" ]; then
		echo "WARNING: exit code $exit_code"
	fi
	return $exit_code
}

function assert_text() {
	args="$@"
	message="$1" ; shift
	condition="$1" ; shift
	( api "$@" | grep -e "$condition" >/dev/null ) && ( assert_passed "$message" ) || ( assert_text_failed "$message" "$condition" "$@" )
}

function assert_passed() {
	echo -e "Passed: $1\n"
}

function assert_text_failed() {
	message="$1" ; shift
	condition="$1" ; shift
	echo -e "Failed: $message\nCommand: $@\nMissing text: $condition\n"
}

function assert_not_text() {
	args="$@"
	message="$1" ; shift
	condition="$1" ; shift
	( api "$@" | grep -e "$condition" >/dev/null ) && ( assert_not_text_failed "$message" "$condition" "$@" ) || ( assert_passed "$message" )
}

function assert_not_text_failed() {
	message="$1" ; shift
	condition="$1" ; shift
	echo -e "Failed: $message\nCommand: $@\nFound text: $condition\n"
}

function wait_cmd() {
	message="$1"; shift
	cmd="$@"
	echo -n "Waiting $message ..."
	i=0
	while [ \( $i -le 60 \) -a \( "`( eval $cmd 2>&1 >/dev/null ); echo $?`" != "0" \) ]; do
		echo -n "."
		sleep 3; i=$[ $i + 3 ]
	done
	if [ "$i" -le "60" ]; then
		echo " passed."
		return 0
	else
		echo "FAILED!"
		return 1
	fi
}

### DEFAULT VALUES ###

default_dc_name="api-test-dc"
default_srv_name="api-test-srv"
default_sto_name="api-test-sto"
success="Operation completed"

### DATA CENTER ###

create_dc_command="create-datacenter -name $default_dc_name"
[ "0" == "1" ] && (
	dc_id=`api $create_dc_command | grep 'ID:' | sed -e 's/.*ID: //'`
	[ "$dc_id" == "" ] && ( assert_text_failed "Create DataCenter" "ID:" "$create_dc_command" ) || ( assert_passed "Create DataCenter" )
	
	assert_text "Get DataCenter" "$dc_id" get-datacenter -dcid $dc_id
	assert_text "Get DataCenter state" "Provisioning state" get-datacenter-state -dcid $dc_id # or \(.\+\) instead of AVAILABLE
	assert_text "Get all DataCenters" "$dc_id" get-all-datacenters
	assert_text "Clear DataCenter" "$success" clear-datacenter -dcid $dc_id
	api update-datacenter -dcid $dc_id -name ${default_dc_name}2
	assert_text "Rename DataCenter" "${default_dc_name}2" get-datacenter -dcid $dc_id
	assert_text "Delete DataCenter" "$success" delete-datacenter -dcid $dc_id
	assert_not_text "Get all DataCenters after deletion" "$dc_id" get-all-datacenters
)

echo "Creating victim data center"
dc_id=`api $create_dc_command | grep 'ID:' | sed -e 's/.*ID: //'`
wait_cmd "for data center '$dc_id' to be AVAILABLE" "api get-datacenter-state -dcid $dc_id | grep 'AVAILABLE'"

### VIRTUAL SERVER ###

create_srv_command="create-server -dcid $dc_id -cores 1 -ram 256 -name $default_srv_name"
[ "0" == "1" ] && (
	srv_id=`api $create_srv_command | grep 'ID:' | sed -e 's/.*ID: //'`
	[ "$srv_id" == "" ] && ( assert_text_failed "Create Server" "ID:" "$create_srv_command" ) || ( assert_passed "Create Server" )
	
	assert_text "Get Server" "$srv_id" get-server -srvid "$srv_id"
	wait_cmd "for server $srv_id to boot" "api get-server -srvid $srv_id | grep 'RUNNING'"
	assert_text "Reboot Server" "$success" reboot-server -srvid "$srv_id"
	wait_cmd "for server $srv_id to reboot" "api get-server -srvid $srv_id | awk '/RUNNING/{found=1;exit} END{exit(found)}"
	wait_cmd "for server $srv_id to boot" "api get-server -srvid $srv_id | grep 'RUNNING'"
	assert_text "Delete Server" "$success" delete-server -srvid "$srv_id"
)

echo "Creating victim server"
srv_id=`api $create_srv_command | grep 'ID:' | sed -e 's/.*ID: //'`
wait_cmd "for server '$srv_id' to boot" "api get-server -srvid $srv_id | grep 'RUNNING'"

### STORAGE ###

create_sto_command="create-storage -dcid $dc_id -name $default_sto_name -size 1"
[ "0" == "1" ] && (
	sto_id=`api $create_sto_command | grep 'ID:' | sed -e 's/.*ID: //'`
	[ "$sto_id" == "" ] && ( assert_text_failed "Create Storage" "ID:" "$create_sto_command" ) || ( assert_passed "Create Storage" )
	
	assert_text "Get Storage" "$sto_id" get-storage -stoid "$sto_id"
	wait_cmd "for storage $sto_id to be AVAILABLE" "api get-storage -stoid $sto_id | grep 'AVAILABLE'"
	assert_text "Connect Storage to Server" "$success" connect-storage-to-server -stoid $sto_id -srvid $srv_id -bus ide
	wait_cmd "for storage $sto_id to be AVAILABLE" "api get-storage -stoid $sto_id | grep 'AVAILABLE'"
	assert_text "Disconnect storage from server" "$success" disconnect-storage-from-server -stoid $sto_id -srvid $srv_id
	wait_cmd "for storage $sto_id to be AVAILABLE" "api get-storage -stoid $sto_id | grep 'AVAILABLE'"
	api update-storage -stoid $sto_id -name ${default_dc_name}2
	assert_text "Rename Storage" "${default_dc_name}2" get-storage -stoid $sto_id
	wait_cmd "for storage $sto_id to be AVAILABLE" "api get-storage -stoid $sto_id | grep 'AVAILABLE'"
	assert_text "Delete Storage" "$success" delete-storage -stoid $sto_id
)

echo "Creating victim storage"
sto_id=`api $create_sto_command | grep 'ID:' | sed -e 's/.*ID: //'`
wait_cmd "for storage '$sto_id' to be AVAILABLE" "api get-storage -stoid $sto_id | grep 'AVAILABLE'"

echo -e "\n\nCLEANING UP\n"

api clear-datacenter -dcid $dc_id
wait_cmd "servers to delete" "api get-datacenter -dcid $dc_id | grep 'Servers (0)'"
wait_cmd "storages to delete" "api get-datacenter -dcid $dc_id | grep 'Storages (0)'"
api delete-datacenter -dcid $dc_id
wait_cmd "datacenter to delete" "api get-all-datacenters | awk '/$dc_id/{found=1;exit} END{exit(found)}'" # wait until text is not found

