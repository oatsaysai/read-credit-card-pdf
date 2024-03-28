FROM golang:1.19.13-alpine3.18 AS builder

# Install tools
RUN apk update && apk add --no-cache --virtual .build-deps \
    gcc \
    python3 \
    py3-pip

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip3 install --no-cache-dir pypdf pycryptodome pandas plotly cli-args-system --break-system-package

WORKDIR /app

COPY go.mod go.sum /app/
RUN go mod download

COPY . /app
RUN go build -o main -ldflags '-s -w' main.go

FROM alpine:3.19

# Install tools
RUN apk add --no-cache python3

WORKDIR /app

COPY . /app
COPY --from=builder /app/main /app/main
COPY --from=builder /app/venv /app/venv

# Activate virtual environment
ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT ["/app/main"]
