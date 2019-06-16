FROM r-base

ENV BASE=/opt/fed4fire
ENV DATA=/var/local/fed4fire

RUN apt-get update && apt-get -y install libcurl4-openssl-dev
RUN Rscript -e "install.packages('forecast')"
RUN mkdir -p $BASE && mkdir -p $DATA

ADD forecast-hw.r $BASE
ADD run.sh $BASE

WORKDIR $DATA

ENTRYPOINT ["R", "CMD", "BATCH", "--no-save", "--no-restore"]
CMD ["/opt/fed4fire/forecast-hw.r"]
