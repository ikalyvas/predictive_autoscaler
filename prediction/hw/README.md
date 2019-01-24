# Holt-Winters forecasting

## Build container

```
$ docker build -t modiofed4fire/fed4fire:forecast-hw-1.0 .
```

## Run the forecasting tool

Create a CSV file named cpu.csv and place it in the same directory as `run.sh`. Then run:

```
$ ./run.sh {interval}
```

Where {interval} is the sampling interval in seconds, e.g.:

```
$ ./run.sh 10
```

The output will be placed in file `forecast.txt` and will be updated every 1 second.
