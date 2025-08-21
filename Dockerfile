FROM python:3-alpine

WORKDIR /app

RUN pip install --no-cache-dir famly-fetch

VOLUME [ "/pictures" ]

ENV FAMLY_PICTURES_FOLDER=/pictures

ENTRYPOINT [ "famly-fetch" ]
