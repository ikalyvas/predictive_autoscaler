#!/bin/sh



 while true;
 do 
    metric_current_vaule=$(cat $2 | cut -d ',' -f3 | tail -n1);
    forecast_value=$(head -n1 $1);

       if [ $forecast_value -gt 60 ] || [ $forecast_value -eq 60 ]
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

