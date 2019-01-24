#!/bin/sh

hw() {
  a=$1
  b=$2
  w=$3
  docker run --rm --name hw -v "$PWD":/var/local/fed4fire \
    modiofed4fire/fed4fire:forecast-hw-1.0 \
    "--args a=$a b=$b w=$w" \
    /opt/fed4fire/forecast-hw.r
  echo $cmd
eval $cmd
}

while [ true ]; do
  sleep 1
  lines=`wc -l cpu.csv | awk '{print $1}'`
  to=$(($lines -1))
  to=$(($to *10 ))
  echo $lines
  echo $to
  hw 0 $to $1
done
