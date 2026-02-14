FROM python:3.14.3-alpine3.23

RUN \
    python -m venv .venv && \
    botenv/bin/pip install -U pip && \
    botenv/bin/pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

USER $UID:$GID

CMD .venv/bin/python3 aprs.py