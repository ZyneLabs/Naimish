from common import send_req_syphoon


def walmart_scraper(product_url,pid):
    try:
        try:
            with open(f'{pid}.html', 'r', encoding='utf-8') as f:
                html = f.read()
        except:
            req = send_req_syphoon(0, 'get', product_url)
            req.raise_for_status()
            with open(f'{pid}.html', 'w', encoding='utf-8') as f:
                f.write(req.text)
            html = req.text
        return html
    except Exception as e:
        print(e)