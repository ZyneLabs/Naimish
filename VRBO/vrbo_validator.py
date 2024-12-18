def validate_response(response_json : dict | list) -> bool:

    if isinstance(response_json, list):
        return all(validate_response(item) for item in response_json)
    
    if isinstance(response_json, dict):
        if response_json.get('data') and (
            response_json['data'].get('propertySearch') or # For property search
            response_json['data'].get('propertyOffers') or # For property offers
            response_json['data'].get('offersContactHost') or  # For contact host
            response_json['data'].get('propertyAvailabilityCalendars') or  # For property calendars
            response_json['data'].get('reviewsOverview') or  # For property reviews
            response_json['data'].get('recommendationsModule') or  # For property recommendations
            response_json['data'] # I guess all the valid responses have this
        ):
            return True

        if response_json.get('errors') or response_json.get('message'):
            return False
        
    return False
