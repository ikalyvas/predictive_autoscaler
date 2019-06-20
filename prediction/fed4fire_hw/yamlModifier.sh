#!/bin/sh

# ./yamlModifier.sh forecast.txt cpu.csv  60

 while true;
 do 
    metric_current_vaule=$(cat $2 | cut -d ',' -f3 | tail -n1);
    forecast_value=$(head -n1 $1);
    ((metric_current_vaule=$metric_current_vaule + 0))
    forecast_valueInt=${forecast_value%.*}
       
       if [ $forecast_valueInt -gt $3 ]
       #if [ $(echo "$forecast_valueInt > $3" | bc) ] 
       then
        echo "Auto scale is going to happen";
        echo $metric_current_vaule;
        echo $forecast_value;
         patchAutoScaler= kubectl patch hpa kurento -p '{"spec":{"targetCPUUtilizationPercentage":'$metric_current_vaule'}}'
       else
        echo "I will not autoscale level forecast  is lower than 60"; 
        patchAutoScaler= kubectl patch hpa kurento -p '{"spec":{"targetCPUUtilizationPercentage":300}}'
       fi   
    sleep 10;

 done
