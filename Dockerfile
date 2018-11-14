FROM python:3.6
MAINTAINER Diogo Gomes dgomes@ua.pt
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python3.6", "server.py"]
EXPOSE 8000
