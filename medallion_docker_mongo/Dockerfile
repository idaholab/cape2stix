FROM python:latest
RUN pip install medallion pymongo
COPY config.json config.json
COPY default_data.json default_data.json
EXPOSE 5000
CMD ["medallion", "--host", "0.0.0.0", "--port", "5000", "./config.json"]
