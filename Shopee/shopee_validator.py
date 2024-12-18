def validate_response(response_json : dict) -> bool:
    if (response_json.get('data') and response_json['data'].get('item')) or response_json.get('items'):
        return True
    
    if response_json.get('error') or response_json.get('message'):
        return False
    
    return False