import json
import urllib
from django.conf import settings
__author__ = 'giginet'

def shorten(url):
    """
    与えられたURLをgoo.glを使って短縮します
    """
    try:
        API_URL = 'https://www.googleapis.com/urlshortener/v1/url'
        data = json.dumps({'longUrl': url })
        data = data.encode('utf-8')
        request = urllib.request.Request(API_URL, data)
        request.add_header('Content-Type', 'application/json')
        r = urllib.request.urlopen(request)
        json_string = r.read().decode("utf-8")
        return json.loads(json_string)['id']
    except Exception as e:
        if settings.DEBUG:
            # デバッグ環境においては例外を発生させる
            raise e
        # 本番環境に置いてはfail silently
        return url