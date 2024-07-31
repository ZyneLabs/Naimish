import requests
from typing import Optional, Dict, Any
from .syphoon_exception import MissingAPIKeyError,SyphoonAPIError,SyphoonAPIRequestError,SyphoonAPIResponseError
from urllib.parse import urlencode

class SyphoonRequest:
    BASE_URL = 'https://api.syphoon.com'

    @classmethod
    def request(cls, api_key: str, method: str, url: str,headers : Dict[str, Any] = None,cookies : Dict[str, Any] = None, params : Dict[str, Any] = None, payload :Dict[str, Any] = None, country_code: Optional[str] = None, render: Optional[str] = None, session_number: Optional[int] = None,**kwargs: Dict[str, Any]):
        if not api_key:
            raise MissingAPIKeyError()

        if params is not None:
            url = f"{url}?{urlencode(params)}"

        if payload is None:
            payload = {}

        if headers is not None:
            payload['keep_headers'] = True
        else:
            headers = {}

        # Add custom parameters if provided
        if country_code:
            payload['country_code'] = country_code
        if render:
            payload['render'] = render
        if session_number:
            payload['session_number'] = session_number

        kwargs['params'] = params
        payload = {
                **payload,
                "key":api_key,
                "url": url,
                "method": method,
            }
        
        if cookies is not None:
            headers["cookie"] = ";".join([f"{k}={v}" for k, v in cookies.items()])

        try:
            response = requests.post(cls.BASE_URL, headers=headers, json=payload)
            print(response.status_code)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response
        
        except requests.exceptions.HTTPError as http_err:
            raise SyphoonAPIRequestError(response.status_code, f"HTTP error occurred: {http_err} {response.json('message')}")
        
        except requests.exceptions.RequestException as req_err:
            raise SyphoonAPIError(f"Request error occurred: {req_err}")
        
        except Exception as err:
            raise SyphoonAPIError(f"An error occurred: {err}")

    @classmethod
    def get(cls, api_key: str, url: str,headers : Dict[str, Any] = None,cookies : Dict[str, Any] = None, params : Dict[str, Any] = None, payload :Dict[str, Any] = None, country_code: Optional[str] = None, render: Optional[str] = None, session_number: Optional[int] = None):
        return cls.request(api_key, 'GET', url, headers,cookies, params, payload, country_code, render, session_number)
    @classmethod
    def post(cls, api_key: str, url: str,headers : Dict[str, Any] = None,cookies : Dict[str, Any] = None, params : Dict[str, Any] = None, payload :Dict[str, Any] = None, country_code: Optional[str] = None, render: Optional[str] = None, session_number: Optional[int] = None):
        return cls.request(api_key, 'POST', url, headers,cookies, params, payload, country_code, render, session_number)

    @classmethod
    def put(cls, api_key: str, url: str,headers : Dict[str, Any] = None,cookies : Dict[str, Any] = None, params : Dict[str, Any] = None, payload :Dict[str, Any] = None, country_code: Optional[str] = None, render: Optional[str] = None, session_number: Optional[int] = None):
        return cls.request(api_key, 'PUT', url, headers,cookies, params, payload, country_code, render, session_number)
    @classmethod
    def delete(cls, api_key: str, url: str,headers : Dict[str, Any] = None,cookies : Dict[str, Any] = None, params : Dict[str, Any] = None, payload :Dict[str, Any] = None, country_code: Optional[str] = None, render: Optional[str] = None, session_number: Optional[int] = None):
        return cls.request(api_key, 'DELETE', url, headers,cookies, params, payload, country_code, render, session_number)

