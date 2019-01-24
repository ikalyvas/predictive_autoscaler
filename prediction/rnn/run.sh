#!/bin/sh

predict() {
  docker run --rm --name rnn -v `pwd`:/var/local/fed4fire modiofed4fire/fed4fire:rnn-1.0 $1 $2 $3
}

while [ true ]; do
  sleep 10
  predict cpu.csv rnn.txt $1
done
