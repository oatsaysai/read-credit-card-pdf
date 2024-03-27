# Read Credit Card Statement

### Install Dependencies

```sh
python3 -m pip install pypdf
python3 -m pip install pycryptodome==3.15.0
python3 -m pip install pandas
python3 -m pip install plotly
python3 -m pip install cli-args-system
```

### How to run

```sh
python3 main.py -p 11111111 -f KBGC_1000000047986508_240225.pdf 
```

### How to build docker image

```sh
docker build -t read-credit-card-pdf .
```

### How to run docker

```sh
docker run -p 8082:8082 --name read-credit-card-pdf read-credit-card-pdf 
```