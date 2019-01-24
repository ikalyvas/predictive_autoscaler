require(graphics)
require(forecast)
require(ggplot2)

##First read in the arguments listed at the command line
args=(commandArgs(TRUE))

##args is now a list of character vectors
## First check to see if arguments are passed.
## Then cycle through each element of the list and evaluate the expressions.
if(length(args)==0){
    print("No arguments supplied.")
    ##supply default values
    a = 1
    b = 1
    w=1
}else{
    for(i in 1:length(args)){
         eval(parse(text=args[[i]]))
    }
}

# a and b stand for seconds
print(a)
print(b)
print(w)
if (a>0) {A <- a/10 + 1} else {A <-0}
B <- b/10 + 1
window <-w/10

#First I need to load the data from my file

data = read.csv('cpu.csv')
#data = ts(data[,3],start = c(0), frequency = 1)
data = ts(data[,3],frequency = 1)

data1 <- data[A:B]

print (data1)
#Second I need to autofit the ARIMA

ARIMAfit = auto.arima(data1, approximation=FALSE,trace=FALSE)
summary(ARIMAfit)

#Third, I am doing my forecast and I am plotting
forecastObject <-forecast(ARIMAfit, h=window)
plot (forecastObject, xlab='Seconds', ylab = 'Total CPU load')

#Last, I am writing in a file the outcome of the prediction for h=N given by John

print (as.numeric(forecastObject$mean)[window])

fileConn<-file("forecast.txt", "w")
string <- as.character(as.numeric(forecastObject$mean)[window])
writeLines(string, fileConn)
close(fileConn)
