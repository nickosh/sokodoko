FROM python:3.11.3-alpine3.18

RUN mkdir /app
WORKDIR /app

COPY ./ /app

RUN apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev alpine-sdk
RUN pip install -e .
RUN pip install pytelegrambotapi --upgrade

ENTRYPOINT ["python", "/app/src/sokodoko/main.py"]
