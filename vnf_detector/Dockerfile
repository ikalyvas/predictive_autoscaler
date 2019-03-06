FROM python:2

COPY . /opt/vnf_detector

WORKDIR /opt/vnf_detector

RUN pip install -r requirements.txt

ENV PYTHONPATH=/opt:$PYTHONPATH

CMD [ "python", "./vnf_detector.py" ]