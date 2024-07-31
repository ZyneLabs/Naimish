# SyphoonRequest

SyphoonRequest is a Python wrapper for the Syphoon API. It simplifies the process of making requests to the Syphoon API by providing a set of class methods for different HTTP request types.

## Installation

clone the repository and run below command

```bash
python3 setup.py sdist
pip3 install .
```

## Usage

```python
from syphoon import SyphoonRequest

API_KEY = 'you secret key'
url = 'https://httpbin.org/get'

resp = SyphoonRequest.get(API_KEY,url)

print(resp)
```


### post request

```python
from syphoon import SyphoonRequest

API_KEY = 'you secret key'
url = 'https://httpbin.org/anything'
payload = {'sample': 'value'}
resp = SyphoonRequest.post(API_KEY,url,payload=payload)

print(resp)
```



