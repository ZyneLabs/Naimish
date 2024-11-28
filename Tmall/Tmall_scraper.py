from playwright.sync_api import sync_playwright
import re


def tmall_parser(url):
    
    data = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector('h1')

            data['name'] = page.query_selector('h1').text_content()
            data['currncy'] = page.locator('span[class*="unit"]').first.text_content()
            data['price'] = page.locator('span[class*="text"]').first.text_content()

            # select images with regex
            data['images'] = []
            images = page.query_selector_all('li img')
            for image in images:
                src = image.get_attribute('src')
                if src:
                    data['images'].append(src)

            data['shop_name'] = page.query_selector('span[class*="shopName"]').text_content()
            data['rating'] = page.query_selector('span[class*="starNum"]').text_content()
            data['about'] = ' | '.join([item.text_content() for item in page.query_selector_all('div[class*="evaluateItem"]')])
            browser.close()
    except Exception as e:
        print(e)
        data['error'] = "Error: " + str(e)

    return data


if __name__ == '__main__':
    url = 'https://item.taobao.com/item.htm?spm=a21bo.tmall%2Fa.201876.d8.6614c3d5bpZvdK&id=810479080067&scm=1007.40986.413660.0&pvid=3a3633d7-daca-4183-b9ab-4809361db405&xxc=home_recommend&skuId=5503269349598&utparam=%7B%22aplus_abtest%22%3A%2286c5fd3ee4a86194446e230f3f465b1b%22%7D&priceTId=2150436d17327137831566549e5f03&pisk=fKAIQQYKNZjZdvMEhz3NfekcSVfS73GVPz_JoUFUy6CL2uLAb7WEK3uWC3KGLMdWr7_Jy30h42Dw-eflwmo2Vj8H-cwwxoRCJ1I9Sa78p3-XZc1lwmoSgj8H-_xDxvZFyRQOja_RJ9KR6NQ5y_QR2W31Xa_0ekKJ2F31yayRyWIRXFQFk_ERp_QTXw782gCRyl31PGEdJFDLlaMCxegZfnfIGxZB-GN8GlbhptlcX7Uy6wOvqeeuw7d1R9OlSM4uS_9JoL1R12hJ-nSGeIKt_W1WWatflHZt76LD3hsFG4ycqK8J3ZKS3JYO6ZXv39rQG_RBWB7MVree-TpwttAEXW1vne5eehh_OnIr4SSfwCy75tV55ius582knRNpUZmqtIXdSw6Z5VZpE9QG5Ngs58mCpNbC-Vg_vA1..'
    print(tmall_parser(url))