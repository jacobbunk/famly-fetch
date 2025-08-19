FROM python:3-alpine

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

ENTRYPOINT [ "famly-fetch" ]
