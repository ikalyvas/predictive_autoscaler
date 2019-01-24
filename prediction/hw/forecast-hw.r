require(graphics)
require(forecast)
#require(ggplot2)

#Command line arguments

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
    w = 1
}else{
    for(i in 1:length(args)){
         eval(parse(text=args[[i]]))
    }
}

print(a)
print(b)
print(w)

if (a>0) {A <- a/10 + 1} else {A <-0}
#hack
#B <- b/10 + 1
B <- b/10
window <-w/10


#First I need to load the data from my file

data = read.csv('cpu.csv')
#data = ts(data[,3],start = c(0), frequency = 1)
data = ts(data[,3],frequency = 1)

data1 <- data[A:B]
print (data1)

#Second I need to autofit the holt winters

fit <- HoltWinters(data1,gamma=FALSE)

#plot (fit, xlab='Seconds', ylab = 'CPU load')

#Third, I am doing my forecast and I am plotting

forecastObject <-forecast(fit, window)

plot (forecastObject, xlab='Seconds', ylab = 'CPU load')

#Last, I am writing in a file the outcome of the prediction for h=N given by John

value <- as.numeric(forecastObject$mean)[window]

print (value)

fileConn<-file("forecast.txt","w")
string <- as.character(value)
writeLines(string, fileConn)
close(fileConn)
