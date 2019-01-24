#!/usr/local/bin/python

import sys
sys.version
import datetime
#Import Libraries
import tensorflow as tf
import pandas as pd
import numpy as np
import os
import random

import tensorflow as tf
import shutil
from dateutil.parser import parse
import tensorflow.contrib.learn as tflearn
import tensorflow.contrib.layers as tflayers
from tensorflow.contrib.learn.python.learn import learn_runner
import tensorflow.contrib.metrics as metrics
import tensorflow.contrib.rnn as rnn
from pandas import date_range, Series, to_datetime

def read_file(path):
    ts = pd.read_csv('cpu.csv',usecols=[0,1], index_col=0)
    return ts

def write_file(path, forecast):
    if path != None:
        with open(path, 'w') as f:
            f.write(str(forecast)+'\n')

def test_data(series,forecast,num_periods):
    test_x_setup = series[-(num_periods + forecast):]
    testX = test_x_setup[:num_periods].reshape(-1, 20, 1)
    testY = series[-(num_periods):].reshape(-1, 20, 1)
    return testX,testY

# @num_periods Number of periods per vector we are using to predict one
#              period ahead
def predict(ts, num_periods):
    series = np.array(ts)

    # Forecast horizon, one period into the future
    f_horizon = 1

    x_data = series[:(len(series)-(len(series) % num_periods))]
    x_batches = x_data.reshape(-1, 20, 1)

    y_data = series[1:(len(series)-(len(series) % num_periods))+f_horizon]
    y_batches = y_data.reshape(-1, 20, 1)

    X_test, Y_test = test_data(series,f_horizon,num_periods )

    # We didn't have any previous graph objects running, but this
    # would reset the graphs
    tf.reset_default_graph()

    # Number of vectors submitted
    inputs = 1
    # Number of neurons we will recursively work through,
    # can be changed to improve accuracy
    hidden = 100
    #number of output vectors
    output = 1

    # Create variable objects
    X = tf.placeholder(tf.float32, [None, num_periods, inputs])
    y = tf.placeholder(tf.float32, [None, num_periods, output])

    # Create our RNN object
    basic_cell = tf.contrib.rnn.BasicRNNCell(num_units=hidden,
        activation=tf.nn.relu)
    # Choose dynamic over static
    rnn_output, states = tf.nn.dynamic_rnn(basic_cell, X,
        dtype=tf.float32)
    # Small learning rate so we don't overshoot the minimum
    learning_rate = 0.001

    # Change the form into a tensor
    stacked_rnn_output = tf.reshape(rnn_output, [-1, hidden])
    # Specify the type of layer (dense)
    stacked_outputs = tf.layers.dense(stacked_rnn_output, output)
    # Shape of results
    outputs = tf.reshape(stacked_outputs, [-1, num_periods, output])

    # Define the cost function which evaluates the quality of our model
    loss = tf.reduce_sum(tf.square(outputs - y))
    # Gradient descent method
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
    # Train the result of the application of the cost_function
    training_op = optimizer.minimize(loss)
    #Initialize all the variables
    init = tf.global_variables_initializer()

    # Number of iterations or training cycles, includes both the
    # FeedFoward and Backpropogation
    epochs = 1000

    with tf.Session() as sess:
        init.run()
        for ep in range(epochs):
            sess.run(training_op, feed_dict={X: x_batches, y: y_batches})
            if ep % 100 == 0:
                mse = loss.eval(feed_dict={X: x_batches, y: y_batches})
        y_pred = sess.run(outputs, feed_dict={X: X_test})

    return y_pred

def main():
    args = sys.argv

    inFile = args[1]
    outFile = args[2]
    periods = int(int(args[3])/10)
    ts = read_file(inFile)

    y_pred = predict(ts, periods)
    forecast = y_pred[0][-1][0]
    print("Forecast: "+str(forecast))

    write_file(outFile, forecast)

if __name__ == "__main__":
    main()
