FROM ubuntu:latest
LABEL authors="AF"

ENTRYPOINT ["top", "-b"]