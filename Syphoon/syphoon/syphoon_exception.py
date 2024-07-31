class MissingAPIKeyError(Exception):
    """Exception raised when the API key is missing."""
    def __init__(self, message="API key is missing"):
        self.message = message
        super().__init__(self.message)

class SyphoonAPIError(Exception):
    """Base class for other exceptions."""
    def __init__(self, message="An error occurred with the Syphoon API"):
        self.message = message
        super().__init__(self.message)

class SyphoonAPIRequestError(SyphoonAPIError):
    """Exception raised for request errors."""
    def __init__(self, status_code, message="A request error occurred with the Syphoon API"):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message)

class SyphoonAPIResponseError(SyphoonAPIError):
    """Exception raised for response errors."""
    def __init__(self, message="A response error occurred with the Syphoon API"):
        self.message = message
        super().__init__(self.message)