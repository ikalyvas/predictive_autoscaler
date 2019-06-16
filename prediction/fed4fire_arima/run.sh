#!/bin/sh

hw() {
  a=$1
  b=$2
  w=$3
  #cmd="R CMD BATCH --no-save --no-restore  '--args a=$1 b=$2 w=$3' '/opt/forecast/arima/arima-softfire.r'"
  docker run --rm --name arima -v "$PWD":/var/local/fed4fire \
    modiofed4fire/fed4fire:forecast-arima-1.0 \
    "--args a=$a b=$b w=$w" \
    /opt/fed4fire/forecast-arima.r
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
