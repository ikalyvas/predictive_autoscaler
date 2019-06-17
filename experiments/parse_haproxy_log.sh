#!/bin/bash

grep 'timeout.\+[0-9]\+ active' /var/log/haproxy.log | awk '{print $3,$16}' | uniq ; grep 'passed.\+[0-9]\+ active' /var/log/haproxy.log | awk '{print $3,$17}' | uniq
