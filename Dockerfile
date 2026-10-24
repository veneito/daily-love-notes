FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home app && mkdir /data && chown app:app /data
WORKDIR /app
COPY server.py /app/server.py
COPY dist /app/dist
ENV LOVE_DATA=/data LOVE_SITE=/app/dist
USER app
EXPOSE 8080
CMD ["python", "-u", "server.py"]
