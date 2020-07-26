# Dockerfile
FROM python:3.7-stretch
# FROM python:3.8.3
# RUN apt-get update -y
# RUN apt-get install -y python-pip python-dev build-essential
COPY ./requirements.txt /app/requirements.txt
COPY src/ app/
WORKDIR /app
RUN pip3 install -r requirements.txt
ENV PORT 8080
# ENTRYPOINT ["python"]
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
# CMD ["app.py"]