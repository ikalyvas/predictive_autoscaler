FROM python:3.6

COPY . /opt/vnf_detector

WORKDIR /opt/vnf_detector

RUN pip install -U pip
RUN pip install -r requirements.txt
#RUN pip install pipenv
#RUN pipenv shell

ENV PYTHONPATH=/opt:$PYTHONPATH

CMD [ "python", "./vnf_detect.py" ]