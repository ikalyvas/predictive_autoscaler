 #!/bin/bash
TIME_TO_SLEEP=20;
FILE_NAME=cpu.csv
counter=1;
time=0;
 while true;
 do 

    if [ $counter -eq 1 ]
    then
  
        if [ -s $FILE_NAME ]
        then
            #newCounter= $(cat cpu.csv | cut -d ',' -f1 | tail -n1);
            echo "Hpa exists"
        else
            echo "Hpa doesnt exits"
            echo  "ID""," "Time""," "CPU_Load" >> $FILE_NAME;
        fi
    fi    

    clear; 
    date=$(date +%s);
    hpa=$(kubectl get hpa  -o json  | jq -r '[.items[] | {status:.status.currentCPUUtilizationPercentage}]' | jq -r '.[].status') ;
    #hpaF=$(echo $hpa+0.0 | bc -l);
    echo  "$counter""," "$time""," "$hpa" >> $FILE_NAME;
    ((counter++))
    ((time=time+TIME_TO_SLEEP))
    sleep $TIME_TO_SLEEP; 
   
 done  
 