import datetime
from django.utils import timezone
from django.test import TestCase
from .factories import RecentActivityFactory
from ..models import RecentActivity

__author__ = 'giginet'

class RecentActivityModelTestCase(TestCase):

    def test_str_returns_title(self):
        """
        str()関数はtitleの値を返す
        """
        activity = RecentActivityFactory(title='お知らせ')
        self.assertTrue(str(activity), 'お知らせ')

    def test_ordering(self):
        """
        RecentActivityは作成日順に並ぶ
        """
        standard_time = datetime.datetime(2014, 7, 1, tzinfo=timezone.utc)
        a0 = RecentActivityFactory(
            publish_at=standard_time - datetime.timedelta(3))
        a1 = RecentActivityFactory(
            publish_at=standard_time - datetime.timedelta(1))
        a2 = RecentActivityFactory(
            publish_at=standard_time - datetime.timedelta(2))
        qs = RecentActivity.objects.all()
        self.assertEqual(len(qs), 3)
        self.assertEqual(qs[0], a1)
        self.assertEqual(qs[1], a2)
        self.assertEqual(qs[2], a0)