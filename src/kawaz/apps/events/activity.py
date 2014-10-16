# coding=utf-8
"""
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from django.contrib.contenttypes.models import ContentType
from kawaz.core.personas.models import Persona
from activities.models import Activity
from activities.mediator import ActivityMediator


class EventActivityMediator(ActivityMediator):
    use_snapshot = True

    def alter(self, instance, activity, **kwargs):
        # 状態が draft の場合は通知しない
        if activity and instance.pub_state == 'draft':
            return None
        if activity and activity.status == 'updated':
            # 通知が必要な状態の変更を詳細に記録する
            if activity.previous is None:
                activity.status = 'created'
            else:
                previous = activity.previous.snapshot
                is_created = lambda x: (
                    not getattr(previous, x) and
                    getattr(instance, x)
                )
                is_updated = lambda x: (
                    getattr(previous, x) and
                    getattr(instance, x) and
                    getattr(previous, x) != getattr(instance, x)
                )
                is_deleted = lambda x: (
                    getattr(previous, x) and
                    not getattr(instance, x)
                )
                remarks = []
                attributes = (
                    'period_start',
                    'period_end',
                    'place',
                    'number_restriction',
                    'attendance_deadline',
                )
                for attribute in attributes:
                    if is_created(attribute):
                        remarks.append(attribute + '_created')
                    elif is_updated(attribute):
                        remarks.append(attribute + '_updated')
                    elif is_deleted(attribute):
                        remarks.append(attribute + '_deleted')
                if not remarks:
                    # 通知が必要な変更ではないため通知しない
                    return None
                activity.remarks = "\n".join(remarks)
        elif activity is None:
            # m2m_updated
            action = kwargs.get('action')
            model = kwargs.get('model')
            if model != Persona:
                # attendees の変化以外は通知しない
                return None
            if action not in ('post_add', 'post_remove'):
                # 追加/削除以外は通知しない
                return None
            # 追加・削除をトラックするActivityを作成
            ct = ContentType.objects.get_for_model(instance)
            status = 'user_add' if action == 'post_add' else 'user_removed'
            activity = Activity(content_type=ct,
                                object_id=instance.pk,
                                status=status)
            # snapshot を保存
            activity.snapshot = instance
            # 追加・削除されたユーザーのIDを保存
            activity.remarks = "\n".join(kwargs.get('pk_set'))
        return activity

    def prepare_context(self, activity, context):
        context = super().prepare_context(activity, context)

        if activity.status == 'updated':
            # remarks に保存された変更状態を利便のためフラグ化
            for flag in activity.remarks.split():
                context[flag] = True
        elif activity.status in ('user_add', 'user_removed'):
            # ユーザーの追加・削除状態だった場合は誰が追加されたのかを設定
            pk_set = map(int, activity.remarks.split())
            users = Persona.objects.filter(pk__in=(pk_set))
            context['users'] = users
        return context
