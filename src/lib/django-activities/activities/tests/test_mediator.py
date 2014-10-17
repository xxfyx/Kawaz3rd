# coding=utf-8
"""
"""
__author__ = 'Alisue <lambdalisue@hashnote.net>'
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.contenttypes.models import ContentType
from ..mediator import ActivityMediator
from ..models import Activity
from ..registry import Registry


class ActivitiesActivityMediatorTestCase(TestCase):
    @patch('activities.mediator.ContentType', spec=ContentType)
    @patch('activities.mediator.Activity', spec=Activity)
    def test__pre_delete_receiver(self, Activity, ContentType):
        ct = MagicMock()
        instance = MagicMock()
        instance.pk = 1
        activity = MagicMock()

        ContentType.objects.get_for_model.return_value = ct
        Activity.return_value = activity

        mediator = ActivityMediator()
        mediator.alter = MagicMock(return_value=activity)
        mediator._pre_delete_receiver(None, instance)

        Activity.assert_called_with(content_type=ct,
                                    object_id=instance.pk,
                                    status='deleted')
        # user defined alternation code is called
        mediator.alter.assert_called_with(instance, activity)
        # activity save method is called
        activity.save.assert_called_with()

    @patch('activities.mediator.ContentType', spec=ContentType)
    @patch('activities.mediator.Activity', spec=Activity)
    def test__post_save_receiver(self, Activity, ContentType):
        ct = MagicMock()
        instance = MagicMock()
        instance.pk = 1
        activity = MagicMock()

        ContentType.objects.get_for_model.return_value = ct
        Activity.return_value = activity

        mediator = ActivityMediator()
        mediator.alter = MagicMock(return_value=activity)
        mediator._post_save_receiver(None, instance, created=True)

        Activity.assert_called_with(content_type=ct,
                                    object_id=instance.pk,
                                    status='created')
        # user defined alternation code is called
        mediator.alter.assert_called_with(instance, activity)
        # activity save method is called
        activity.save.assert_called_with()

        mediator._post_save_receiver(None, instance, created=False)

        Activity.assert_called_with(content_type=ct,
                                    object_id=instance.pk,
                                    status='updated')
        # user defined alternation code is called
        mediator.alter.assert_called_with(instance, activity)
        # activity save method is called
        activity.save.assert_called_with()

    @patch('activities.mediator.ContentType', spec=ContentType)
    @patch('activities.mediator.Activity', spec=Activity)
    def test__m2m_changed_receiver(self, Activity, ContentType):
        ct = MagicMock()
        instance = MagicMock()
        instance.pk = 1
        activity = MagicMock()

        ContentType.objects.get_for_model.return_value = ct
        Activity.return_value = activity

        mediator = ActivityMediator()
        mediator.alter = MagicMock(return_value=activity)
        mediator._m2m_changed_receiver(None, instance, action='pre_add',
                                       reverse=False)

        # user defined alternation code is called
        mediator.alter.assert_called_with(instance, None,
                                          action='pre_add',
                                          reverse=False)
        # activity save method is called
        activity.save.assert_called_with()


    @patch('activities.mediator.post_save')
    @patch('activities.mediator.pre_delete')
    @patch('activities.mediator.m2m_changed')
    def test_connect(self, m2m_changed, pre_delete, post_save):
        model = MagicMock()
        model._meta.app_label = 'app_label'

        mediator = ActivityMediator()
        mediator.connect(model)
        self.assertEqual(mediator.model, model)
        self.assertEqual(mediator.app_label, 'app_label')

        post_save.connect.assert_called_with(mediator._post_save_receiver,
                                             sender=model,
                                             weak=False)
        pre_delete.connect.assert_called_with(mediator._pre_delete_receiver,
                                              sender=model,
                                              weak=False)
        m2m_changed.connect.assert_called_with(mediator._m2m_changed_receiver,
                                               sender=model,
                                               weak=False)

    @override_settings(
        ACTIVITIES_DEFAULT_TEMPLATE_EXTENSION='.html',
        ACTIVITIES_TEMPLATE_EXTENSIONS={},
    )
    def test_get_template_extension(self):
        mediator = ActivityMediator()
        self.assertEqual(mediator.get_template_extension(None), '.html')
        self.assertEqual(mediator.get_template_extension('?'), '.html')

        with override_settings(ACTIVITIES_DEFAULT_TEMPLATE_EXTENSION='.txt'):
            self.assertEqual(mediator.get_template_extension(None), '.txt')
            self.assertEqual(mediator.get_template_extension('?'), '.txt')

        with override_settings(ACTIVITIES_TEMPLATE_EXTENSIONS={'?': '.txt'}):
            self.assertEqual(mediator.get_template_extension(None), '.html')
            self.assertEqual(mediator.get_template_extension('?'), '.txt')

    def test_get_template_names(self):
        model = MagicMock()
        model.__name__ = MagicMock()
        model.__name__.lower = MagicMock(return_value='model')
        model._meta.app_label = 'app_label'
        activity = MagicMock()
        activity.status = 'status'

        mediator = ActivityMediator()
        mediator.get_template_extension = MagicMock(return_value='.html')
        mediator.connect(model)
        self.assertEqual(mediator.get_template_names(activity), (
                         'activities/app_label/model_status.html',
                         'activities/app_label/status.html',
                         'activities/status.html'))
        mediator.get_template_extension.assert_called_with(None)

    @override_settings(
        ACTIVITIES_DEFAULT_EXTENSION='.html',
        ACTIVITIES_TEMPLATE_EXTENSIONS={},
    )
    def test_get_template_names_with_typename(self):
        model = MagicMock()
        model.__name__ = MagicMock()
        model.__name__.lower = MagicMock(return_value='model')
        model._meta.app_label = 'app_label'
        activity = MagicMock()
        activity.status = 'status'
        typename = 'test'

        mediator = ActivityMediator()
        mediator.get_template_extension = MagicMock(return_value='.html')
        mediator.connect(model)
        self.assertEqual(mediator.get_template_names(activity, typename), (
                         'activities/app_label/model_status.test.html',
                         'activities/app_label/status.test.html',
                         'activities/status.test.html',
                         'activities/app_label/model_status.html',
                         'activities/app_label/status.html',
                         'activities/status.html'))
        mediator.get_template_extension.assert_called_with(typename)

    def test_prepare_context(self):
        activity = MagicMock()
        context = MagicMock()

        mediator = ActivityMediator()
        c = mediator.prepare_context(activity, context, typename=None)

        context.update.assert_called_with({
            'activity': activity,
            'object': activity.snapshot,
            'typename': None,
        })
        self.assertEqual(c, context)

    def test_prepare_context_with_typename(self):
        activity = MagicMock()
        context = MagicMock()
        typename = MagicMock()

        mediator = ActivityMediator()
        c = mediator.prepare_context(activity, context, typename=typename)

        context.update.assert_called_with({
            'activity': activity,
            'object': activity.snapshot,
            'typename': typename,
        })
        self.assertEqual(c, context)

    @patch('activities.mediator.select_template')
    def test_render(self, select_template):
        model = MagicMock()
        model.__name__ = MagicMock()
        model.__name__.lower = MagicMock(return_value='model')
        model._meta.app_label = 'app_label'
        activity = MagicMock()
        activity.status = 'status'
        context = MagicMock()
        rendered = MagicMock()
        template = MagicMock()
        template.render.return_value = rendered
        select_template.return_value = template

        mediator = ActivityMediator()
        mediator.connect(model)
        mediator.prepare_context = MagicMock(return_value=context.new())

        r = mediator.render(activity, context)

        select_template.assert_called_with(
            mediator.get_template_names(activity))
        mediator.prepare_context.assert_called_with(activity,
                                                    context.new(),
                                                    typename=None)
        template.render.assert_called_with(context.new())
        self.assertEqual(r, rendered)

    @patch('activities.mediator.select_template')
    def test_render_with_typename(self, select_template):
        model = MagicMock()
        model.__name__ = MagicMock()
        model.__name__.lower = MagicMock(return_value='model')
        model._meta.app_label = 'app_label'
        activity = MagicMock()
        activity.status = 'status'
        context = MagicMock()
        rendered = MagicMock()
        template = MagicMock()
        template.render.return_value = rendered
        select_template.return_value = template
        typename = 'test'

        mediator = ActivityMediator()
        mediator.connect(model)
        mediator.prepare_context = MagicMock(return_value=context.new())

        r = mediator.render(activity, context, typename=typename)

        select_template.assert_called_with(
            mediator.get_template_names(activity, typename=typename))
        mediator.prepare_context.assert_called_with(activity,
                                                    context.new(),
                                                    typename=typename)
        template.render.assert_called_with(context.new())
        self.assertEqual(r, rendered)
