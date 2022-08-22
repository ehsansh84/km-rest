FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
RUN mkdir /app
RUN mkdir /images
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
CMD python boot.py

