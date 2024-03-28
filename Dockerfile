FROM golang:1.19.13-alpine3.18 AS builder

# Install tools
RUN apk update && apk add --no-cache --virtual .build-deps \
    gcc \
    python3 \
    py3-pip

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip3 install --no-cache-dir pypdf pycryptodome pandas plotly cli-args-system pyinstaller pdfminer.six --break-system-package

WORKDIR /app

COPY go.mod go.sum /app
RUN go mod download

COPY . /app

# Build go
RUN go build -o main -ldflags '-s -w' main.go

# Build python
RUN pyinstaller --onefile main.py --name pdf-to-graph

FROM alpine:3.19

WORKDIR /app

COPY index.html /app

COPY --from=builder /app/dist/pdf-to-graph /app/pdf-to-graph
COPY --from=builder /app/main /app/main

ENTRYPOINT ["/app/main"]
