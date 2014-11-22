# coding=utf-8
"""
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from activities.mediator import ActivityMediator


class HatenablogEntryActivityMediator(ActivityMediator):
    notifiers = (
        'twitter_kawaz_official',
    )

    def alter(self, instance, activity, **kwargs):
        if activity and activity.status == 'updated':
            # 通知が必要な状態の変更を詳細に記録する
            if activity.previous is not None:
                previous = activity.previous.snapshot
                if previous.md5 == instance.md5:
                    # Nothing have changed
                    return
        return activity
