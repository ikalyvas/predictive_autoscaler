 #!/bin/bash
TIME_TO_SLEEP=2;
FILE_NAME=cpu.csv
counter=1
 while true;
 do 
    if [ -s $FILE_NAME ]
    then
           echo "Hpa exists"
           
    else
           echo "Hpa doesnt exits"
           echo  "Time""," "CPU_Load" >> $FILE_NAME;
    fi

    clear; 
    date=$(date +%s);
    hpa=$(kubectl get hpa  -o json  | jq -r '[.items[] | {status:.status.currentCPUUtilizationPercentage}]' | jq -r '.[].status') 
    echo  "$date""," "$hpa" >> $FILE_NAME;
    ((counter++))
    sleep $TIME_TO_SLEEP; 
   
 done  
 