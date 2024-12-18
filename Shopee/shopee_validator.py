def validate_response(response_json : dict) -> bool:
    if (response_json.get('data') and response_json['data'].get('item')) or response_json.get('items'):
        return True
    
    if response_json.get('error'):
        return False
    
    return False