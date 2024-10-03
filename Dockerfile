FROM python
ENV TZ="Europe/Berlin"
WORKDIR /app
COPY . /app/
RUN apt-get update && apt-get install -y python3 && apt-get install -y python3-pip
RUN pip3 install -r /app/requirements.txt
ENTRYPOINT ["python3"]
CMD ["main.py"]