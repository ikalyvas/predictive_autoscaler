#!/bin/bash

INTERVAL=$1
while true; do echo $(date +%T; openstack server list --status ACTIVE --image kurento_autostart | grep kurento | wc -l); sleep $INTERVAL; done