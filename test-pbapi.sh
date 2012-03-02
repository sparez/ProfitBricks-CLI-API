#!/bin/bash

debug=""
( echo "$@" | grep -e "-debug" >/dev/null ) && debug="-debug"

function api() {
	./pbapi.py "$debug" -auth costi.auth "$@" 2>&1
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

function wait_text() {
	message="$1"; shift
	cmd="$@"
	echo -n "Waiting $message"
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
	
	assert_text "Get DataCenter" "$default_dc_name" get-datacenter -dcid $dc_id
	assert_text "Get DataCenter state" "Provisioning state" get-datacenter-state -dcid $dc_id # or \(.\+\) instead of AVAILABLE
	assert_text "Get all DataCenters" "$default_dc_name" get-all-datacenters
	assert_text "Clear DataCenter" "$success" clear-datacenter -dcid $dc_id
	api update-datacenter -dcid $dc_id -name ${default_dc_name}2
	assert_text "Rename DataCenter" "${default_dc_name}2" get-datacenter -dcid $dc_id
	assert_text "Delete DataCenter" "$success" delete-datacenter -dcid $dc_id
	assert_not_text "Get all DataCenters after deletion" "$default_dc_name" get-all-datacenters
)

dc_id=`api $create_dc_command | grep 'ID:' | sed -e 's/.*ID: //'`

### VIRTUAL SERVER ###

create_srv_command="create-server -dcid $dc_id -cpu 1 -ram 256 -name $default_srv_name"
[ "0" == "1" ] && (
	srv_id=`api $create_srv_command | grep 'ID:' | sed -e 's/.*ID: //'`
	[ "$srv_id" == "" ] && ( assert_text_failed "Create Server" "ID:" "$create_srv_command" ) || ( assert_passed "Create Server" )
	
	assert_text "Get Server" "$default_srv_name" get-server -srvid "$srv_id"
	wait_text "for server $srv_id to boot" "api get-server -srvid $srv_id | grep 'RUNNING'"
	assert_text "Reboot Server" "$success" reboot-server -srvid "$srv_id"
	wait_text "for server $srv_id to reboot" "api get-server -srvid $srv_id |grep 'NOSTATE'"
	wait_text "for server $srv_id to boot" "api get-server -srvid $srv_id | grep 'RUNNING'"
	assert_text "Delete Server" "$success" delete-server -srvid "$srv_id"
)

echo "Creating victim server"
srv_id=`api $create_srv_command | grep 'ID:' | sed -e 's/.*ID: //'`
wait_text "for server $srv_id to boot" "api get-server -srvid $srv_id | grep 'RUNNING'"

### STORAGE ###

[ "0" == "1" ] && (
	create_sto_command="create-storage -dcid $dc_id -cpu 1 -ram 256 -name $default_sto_name"
	#sto_id=`api $create_sto_command | grep 'ID:' | sed -e 's/.*ID: //'` # <- enable when create-server works
	sto_id="c0abc720-bd2f-9931-fe17-dce463643eca" # <- temporary
	if [ "$sto_id" == "" ]; then assert_text_failed "Create Storage" "ID:" "$create_sto_command"; else assert_passed "Create Storage"; fi
	
	assert_text "Get Storage" "$default_sto_name" get-storage -stoid "$sto_id"
	assert_text "Connect Storage to Server" "$success" connect-storage-to-server -stoid $sto_id -srvid $srv_id -bus ide
	assert_text "Delete Storage" "$success" delete-storage -stoid $sto_id
	#sto_id=`api $create_sto_command | grep 'ID:' | sed -e 's/.*ID: //'` # <- enable when create-server works
)

#api create-datacenter -name "$default_dc_name"
#api delete-datacenter -dcid 04257178-95c4-4655-b7ce-17daab7dcc1a

api clear-datacenter -dcid $dc_id
sleep 15
api delete-datacenter -dcid $dc_id
api get-all-datacenters

