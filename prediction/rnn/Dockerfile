FROM python:3.6

ENV BASE=/opt/fed4fire
ENV DATA=/var/local/fed4fire

RUN echo "deb http://http.debian.net/debian jessie-backports main" >> /etc/apt/sources.list && \
  apt-get update
RUN pip install numpy tensorflow pandas && \
  mkdir -p $BASE

ADD rnn.py $BASE

WORKDIR $DATA

ENTRYPOINT ["python", "/opt/fed4fire/rnn.py"]
CMD ["$DATA/cpu.csv", "$DATA/rnn.txt"]
