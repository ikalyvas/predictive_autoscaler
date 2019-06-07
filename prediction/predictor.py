from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from random import random
from collections import namedtuple, OrderedDict
import time
import csv
from prediction.settings import TRAINING_PHASE_DELAY, METRICS_FILE, DEFAULT_GRANULARITY
# contrived dataset
#data = [x + random() for x in range(1, 100)]
# fit model
#model = ARIMA(data, order=(1, 1, 1))
#model_fit = model.fit(disp=False)
# make prediction
#predicted = model_fit.predict(len(data), len(data)+1, typ='levels')
#forecasted = model_fit.forecast()
#print(f"Using predict:Real values: {data[98]} --- predictions :  99th value:{predicted[0]}\n\t\t\t\t100th value:{predicted[1]}")
#print(f"Using forecast:Real values: {data[98]} --- predictions :  99th value:{forecasted[0]}\n\t\t\t\t100th value:{forecasted[1]}")


class Predictor(object):

    @classmethod
    def get_predictor_class(cls, model):
        if model == "ARIMA":
            return ARIMA
        if model == "Simple Holt-Winters":
            return SimpleExpSmoothing
        if model == "Exponential Holt-Winters":
            return ExponentialSmoothing

    def predict_arima(self):
        print(f"Waiting {TRAINING_PHASE_DELAY}for gathering some historical data from Prometheus")
        time.sleep(TRAINING_PHASE_DELAY)
        print(f"Start predicting")
        window_confidence = 3 # num of values that are close to each other, in order to avoid unnecessary scale out/in in case of a sudden spike.
        scale_out_confidence = OrderedDict()
        scale_in_confidence = OrderedDict()
        while True:
            data = self.get_data()
            cpu_load = [item.CPU_LOAD for item in data]
            timestamps = [item.TIMESTAMP for item in data]
            latest_timestamp = timestamps[-1]
            if cpu_load:
                print(f"Will train with {len(cpu_load)} values")
                model = ARIMA(cpu_load, order=(1, 1, 1))
                model_fit = model.fit(disp=False)
                # make prediction
                predicted = model_fit.forecast()
                predicted = predicted[0]
                print(f"Predict that the next value will be {predicted}")
                if predicted > 3: # TODO: assume 3 is the threshold for scale out  and 0.7 for scale in
                    #scale_out_confidence[timestamps[-1]] = predicted
                    self.decide_to_scale(scale_out_confidence, latest_timestamp, predicted, window_confidence)
                elif predicted < 0.7:
                    self.decide_to_scale()
                else:
                    print(f"Normal predicted value {predicted}")


                time.sleep(DEFAULT_GRANULARITY)


    def decide_to_scale(self, scale_data, timestamp, prediction, window_confidence):
        valid_prediction_count = window_confidence - 1
        data_len = len(scale_data)
        if 0 < data_len < window_confidence:
            last_sample_timestamp = list(scale_data.values())[-1]
            if round(timestamp - last_sample_timestamp) != DEFAULT_GRANULARITY:
                print(f"Received timestamp {timestamp} differs more than {DEFAULT_GRANULARITY} with previous sample timestamp {last_sample_timestamp}}")
                scale_data.clear()
            else:
                scale_data[timestamp] = prediction
                if len(scale_data) == window_confidence:
                    return True



    def get_data(self):
        data = []
        Metrics = namedtuple("Metrics", ["CPU_LOAD","TIMESTAMP"])
        fieldnames = ["ID", "TIMESTAMP", "CPU_LOAD"]
        with open(METRICS_FILE, newline='') as metrics_file:
            reader = csv.DictReader(metrics_file, fieldnames=fieldnames)
            header = next(reader)
            for row in reader:
                metric = Metrics(float(row["CPU_LOAD"]),float(row["TIMESTAMP"]))
                data.append(metric)
        return data


if __name__ == '__main__':
    p = Predictor()
    model = Predictor.get_predictor_class("ARIMA")
    p.predict(model)