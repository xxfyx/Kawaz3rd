#! -*- coding: utf-8 -*-
#
# created by giginet on 2014/6/29
#
from bs4 import BeautifulSoup
import urllib
import datetime
from datetime import timezone
from django.utils.timezone import make_naive
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from .models import RecentActivity

__author__ = 'giginet'

FEED_URL = settings.RECENT_ACTIVITY_FEED_URL
# RSS2のpubDateのフォーマット
PUBDATE_FORMAT = '%a, %d %b %Y %H:%M:%S %z'


class RecentActivityScraper(object):
    def __init__(self, url=FEED_URL, verbose=False):
        self.url = url
        self.verbose = verbose

    def fetch(self):
        try:
            feed = urllib.request.urlopen(self.url).read()
        except:
            raise Exception("Feed URL {} is not found.".format(self.url))
        self.soup = BeautifulSoup(feed)
        items = self.soup.find_all('item')
        for item in items:
            title = item.title.string
            link = item.link.string

            if self.verbose:
                # コマンドから実行したときのみ出す
                print('Fetching entry {}'.format(title))

            pub_date = item.pubdate.string
            publish_at = datetime.datetime.strptime(pub_date, PUBDATE_FORMAT)

            image_url = self._fetch_thumbnail(link)
            filename = image_url.split('/')[-1]
            try:
                image_data = urllib.request.urlopen(image_url).read()
            except:
                raise Exception("Image URL {} is not found.".format(image_url))

            image = SimpleUploadedFile(filename, image_data)
            try:
                RecentActivity.objects.get(url=link)
            except:
                RecentActivity.objects.create(title=title,
                                              url=link,
                                              publish_at=publish_at,
                                              thumbnail=image)

    def _fetch_thumbnail(self, link):
        """
        はてなブログのエントリURLからサムネイルURLを取り出します
        サムネイルはFeedには埋まってなくて、各ページのOpen Graph Protocolとして埋まっているので
        ページごとにfetchします
        """
        try:
            entry = urllib.request.urlopen(link).read()
        except:
            raise Exception("Entry URL {} is not found".format(link))
        soup = BeautifulSoup(entry)
        for meta in soup.find_all('meta'):
            property = meta.get('property', None)
            if property == 'og:image':
                return meta.get('content')
