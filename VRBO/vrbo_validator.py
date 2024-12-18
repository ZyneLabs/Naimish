def validate_response(response_json : dict | list) -> bool:
    if isinstance(response_json, list):
        return all(validate_response(item) for item in response_json)
    
    if isinstance(response_json, dict):
        if  (response_json.get('extensions') and
            response_json['extensions'].get('analytics') and
            response_json['extensions']['analytics'][0].get('tealiumUtagData') and 
            response_json['extensions']['analytics'][0]['tealiumUtagData'].get('Geo') and
            response_json['extensions']['analytics'][0]['tealiumUtagData']['Geo']['country'].lower() == 'us' and
            response_json.get('data') # I guess all the valid responses have this
            ) :
            return True
            

        if response_json.get('errors') or response_json.get('message'):
            return False
        
    return False