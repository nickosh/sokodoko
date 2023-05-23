FROM python:3.11.3-alpine3.18

VOLUME [ "/app"]
WORKDIR /app

EXPOSE 80

COPY pyproject.toml ./

RUN apk add --update --no-cache make gcc musl-dev libffi-dev openssl-dev build-base zlib zlib-dev openssl-dev git openssh && \
    pip install pip --upgrade && \
    pip install .

#ENTRYPOINT ["python", "main.py"]
