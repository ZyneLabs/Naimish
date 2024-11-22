import json
from datetime import datetime

def shopee_parser(domain: str, product_json: dict) -> dict:
    
    if not product_json.get('data') and not product_json.get('error'):
        return {
            "error": "Product not found",
        }
    
    product_json = product_json['data']

    details = {}

    details['item_id'] = product_json['item']['item_id']
    details['name'] = product_json['item']['title']
    details['url'] = f"https://{domain}/product-i.{product_json['item']['shop_id']}.{product_json['item']['item_id']}"

    # price info
    if product_json['item'].get('currency'):
        details['currency'] = product_json['item']['currency']

    # Brand
    if product_json['item'].get('brand'):
        details['brand'] = product_json['item']['brand']

    if product_json['item'].get('price'):
        price_info = {'price': product_json['item']['price'],}
        # print(product_json['item'].get('price_max'),product_json['item'].get('price_min'))
        if product_json['item'].get('price_max') != product_json['item'].get('price_min'):
            price_info['price_min'] = product_json['item']['price_min']
            price_info['price_max'] = product_json['item']['price_max']
        
        if product_json['item']['price'] != product_json['item']['price_before_discount']:
            price_info['price_before_discount'] = product_json['item']['price_before_discount']

        if product_json.get('flash_sale'):
            price_info['discount_percentage'] = product_json['flash_sale']['discount_text'].replace('%','')
        elif product_json['item'].get('raw_discount'):
            price_info['discount_percentage'] = product_json['item']['raw_discount']
        elif product_json['item'].get('show_discount'):
            price_info['discount_percentage'] = product_json['item']['show_discount']
        elif product_json['product_price'].get('discount'):
            price_info['discount_percentage'] = product_json['product_price']['discount']

        details['price_info'] = price_info

    if product_json['item'].get('bundle_deal_info'):
        details['bundle_deal_info'] = {
            'text': product_json['item'].get('bundle_deal_info')['bundle_deal_label'],
            **product_json['item'].get('bundle_deal_info')['bundle_deal_rule']
        }
    # wholesale_price
    if product_json['item'].get('wholesale_tier_list'):
        details['wholesale_price_info'] = product_json['item']['wholesale_tier_list']

    base_image_url  = 'https://down-{}.img.susercontent.com/file/'.format(product_json['item']['image'].split('-')[0])
    details['main_image'] = base_image_url+product_json['item']['image']
   
    if product_json.get('product_images',{}).get('images'):
        details['images'] = [base_image_url+image for image in product_json['product_images']['images']]
        
    if product_json.get('product_images',{}).get('video') and product_json['product_images']['video'].get('mms_data'):
        details['video'] = json.loads(product_json['product_images']['video']['mms_data'])['default_format']['url']

    if product_json['item'].get('size_chart'):
        details['size_chart'] = base_image_url+product_json['item']['size_chart']
    
    if product_json.get('product_attributes',{}).get('categories'):
        detailed_category_info = [
            {'catid': category['catid'], 'name': category['display_name']}
            for category in product_json['product_attributes']['categories']
        ]
        details['category_path'] = ' > '.join([category['name'] for category in detailed_category_info]) + ' > '+ product_json['item']['title']
        
        if len(detailed_category_info) >=1:
            details['category_1'] = detailed_category_info[0]['name']
        if len(detailed_category_info) >=2:
            details['category_2'] = detailed_category_info[1]['name']
        if len(detailed_category_info) >=3:
            details['category_3'] = detailed_category_info[2]['name']

        details['detailed_category_info'] = detailed_category_info

    if product_json.get('product_attributes',{}).get('attrs'):
        details['attributes'] ={
            item['name']: item['value'] for item in product_json['product_attributes']['attrs']
        }

    if product_json['item'].get('description'):
        details['description'] = product_json['item']['description']

    if product_json['item'].get('rich_text_description',{}) and product_json['item']['rich_text_description'].get('paragraph_list'):
        details['description_images'] = [base_image_url+image.get('img_id') for image in product_json['item']['rich_text_description']['paragraph_list'] if image.get('img_id')]

    if product_json['item'].get('tier_variations') and product_json['item']['tier_variations'][0].get('name'):
        details['variation_options'] = {}
        for variation in product_json['item']['tier_variations']:
            details['variation_options'][variation['name']] = {'options': variation['options']}

            if variation.get('images'):
                details['variation_options'][variation['name']]['images'] = [base_image_url+image for image in variation['images']]
            
    
    if product_json['item'].get('models') and product_json['item']['models'][0].get('name'):
        details['variants'] = [
            {
                'item_id': model['item_id'],
                'name': model['name'],
                'price':model['price'],
                'url': f"https://{domain}/product-i.{product_json['item']['shop_id']}.{model['item_id']}",
            }
            for model in product_json['item']['models']
        ]
        
    if product_json.get('product_review'):
        details['rating'] = product_json['product_review']['rating_star']
        details['total_rating_count'] = product_json['product_review']['total_rating_count']
        details['liked_count'] = product_json['product_review']['liked_count']
        details['comments_count'] = product_json['product_review']['cmt_count']

        rating_graph = {}
        for start,rating in enumerate(product_json['product_review']['rating_count'][1:],start=1):
            rating_graph[f'{start} stars'] = rating
        details['rating_graph'] = rating_graph
    if product_json['product_price'].get('labels'):
        details['labels'] =[label['text'] for label in product_json['product_price']['labels']] 

    if product_json.get('shop_vouchers'):
        shop_voucher = []
        for voucher in product_json['shop_vouchers']:
            voucher_info = {
                'promotionid': voucher['promotionid'],
                'voucher_code': voucher['voucher_code'],
                'reward_cap': voucher['reward_cap'],
                'min_spend': voucher['min_spend'],
                'percentage_used': voucher['percentage_used'],
                'discount_percentage': voucher['discount_percentage'],
                'start_time':datetime.fromtimestamp(voucher['start_time']).strftime('%Y-%m-%d %H:%M:%S'),
                'end_time':datetime.fromtimestamp(voucher['end_time']).strftime('%Y-%m-%d %H:%M:%S'),
            }

            shop_voucher.append(voucher_info)

        details['shop_vouchers'] = shop_voucher

    if product_json.get('product_shipping'):
        shipping_info = {}
        if product_json['product_shipping'].get('shipping_fee_info'):
            shipping_info['shipping_from'] = product_json['product_shipping']['shipping_fee_info']['ship_from_location']

            if product_json['product_shipping']['shipping_fee_info']['price'].get('single_value') not in [0,-1]:
                shipping_info['shipping_fee'] = product_json['product_shipping']['shipping_fee_info']['price']['single_value']

            if product_json['product_shipping']['shipping_fee_info']['price'].get('range_max') not in [0,-1]:
                shipping_info['max_shipping_fee'] = product_json['product_shipping']['shipping_fee_info']['price']['range_max']

            if product_json['product_shipping']['shipping_fee_info']['price'].get('range_min') not in [0,-1]:
                shipping_info['min_shipping_fee'] = product_json['product_shipping']['shipping_fee_info']['price']['range_min']

        service_type =[]

        if product_json['product_shipping'].get('grouped_channel_infos_by_service_type'):
            service_type.extend([channel for channel_info in product_json['product_shipping']['grouped_channel_infos_by_service_type'] for channel in channel_info['channel_infos']])

        if product_json['product_shipping'].get('ungrouped_channel_infos'):
            service_type.extend(product_json['product_shipping']['ungrouped_channel_infos'])

        if service_type:
            channel_infos = []

            for channel_info in service_type:
                base_info  = {
                    "name": channel_info['name'],
                }

                if channel_info['price'].get('single_value')==0 and channel_info['price'].get('range_min') == -1 and channel_info['price'].get('range_max') == -1:
                    base_info['free_shipping'] = True
                    base_info['shipping_fee'] = 0
                elif channel_info['price'].get('single_value')!=-1:
                    base_info['free_shipping'] = False
                    base_info['shipping_fee'] = channel_info['price']['single_value']
                else:
                    base_info['min_shipping_fee'] = channel_info['price']['range_min']
                    base_info['max_shipping_fee'] = channel_info['price']['range_max']
                
                if channel_info['price_before_discount']:
                    if channel_info['price_before_discount'].get('single_value')!=-1:
                        base_info['shipping_fee_before_discount'] = channel_info['price_before_discount']['single_value']
                    else:
                        base_info['min_shipping_fee_before_discount'] = channel_info['price_before_discount']['range_min']
                        base_info['max_shipping_fee_before_discount'] = channel_info['price_before_discount']['range_max']

                if channel_info.get('channel_delivery_info') and channel_info['channel_delivery_info'].get('estimated_delivery_date_from'):
                    base_info['channel_delivery_info'] = {
                        'min_estimated_delivery_date': datetime.fromtimestamp(channel_info['channel_delivery_info']['estimated_delivery_date_from']).strftime('%Y-%m-%d %H:%M:%S') if channel_info['channel_delivery_info'].get('estimated_delivery_date_from') else channel_info['channel_delivery_info']['estimated_delivery_date_from'],
                        'mix_estimated_delivery_date': datetime.fromtimestamp(channel_info['channel_delivery_info']['estimated_delivery_date_to']).strftime('%Y-%m-%d %H:%M:%S') if channel_info['channel_delivery_info'].get('estimated_delivery_date_to') else channel_info['channel_delivery_info']['estimated_delivery_date_to'],
                        'delay_message': channel_info['channel_delivery_info']['delay_message']
                    }
                elif channel_info.get('warning') and channel_info['warning'].get('warning_msg'):
                    base_info['warning'] = channel_info['warning']['warning_msg']

                channel_infos.append(base_info)

            shipping_info['channel_info'] = channel_infos
        details['shipping_info'] = shipping_info

    shope_details = product_json['shop_detailed']
    shop_info ={
        'shop_id': shope_details['shopid'],
        'user_id' : shope_details['userid'],
        'name': shope_details['name'],
        'last_active_time': datetime.fromtimestamp(shope_details['last_active_time']).strftime('%Y-%m-%d %H:%M:%S'),
        'response_rate': shope_details['response_rate'],
        'location': shope_details['shop_location'],
        'follower_count': shope_details['follower_count'],
        'rating_star': shope_details['rating_star'],
        'rating_bad': shope_details['rating_bad'],
        'rating_good': shope_details['rating_good'],
        'rating_normal': shope_details['rating_normal'],
        'item_count': shope_details['item_count'],
        'join_date': datetime.fromtimestamp(shope_details['ctime']).strftime('%Y-%m-%d %H:%M:%S'),
        'is_official_shop': shope_details['is_official_shop'],
    }
    if not shop_info['location']:
        shop_info['location'] = product_json['item']['shop_location']
    details['shop_info'] = shop_info

    return details
