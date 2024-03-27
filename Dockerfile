FROM golang:1.19.13 AS builder

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

RUN pip3 install pypdf pycryptodome==3.15.0 pandas plotly cli-args-system --break-system-package

WORKDIR /app

COPY . /app

RUN go build -o main main.go

ENTRYPOINT ["/app/main"]
