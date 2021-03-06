from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from activities.registry import registry
from kawaz.core.publishments.models import PublishmentManagerMixin
from kawaz.core.publishments.models import PUB_STATES


class AnnouncementManager(models.Manager, PublishmentManagerMixin):
    def published(self, user):
        """
        指定されたユーザーに対して公開されているAnnouncementインスタンスを含む
        クエリを返す。

        公開状態は指定されたユーザの所属によって変化する。
        ユーザーが認証ユーザかつ[seele, nerv, chidlren]のいずれかに属している
        場合は公開状態が `public` もしくは `protected` のものを、それ以外の場合
        は公開状態が `public` になっているものだけを含む。

        Args:
            user (User instance): DjangoのUserモデル

        Returns:
            指定されたユーザーに対して公開されているAnnouncementインスタンスを
            含むQuerySet
        """
        q = Q(pub_state='public')
        if user and user.is_authenticated():
            if user.is_member:
                # Seele, Nerv, Children can see the protected announcement
                q |= Q(pub_state='protected')
        return self.filter(q)

    def draft(self, user):
        """
        下書き状態のAnnouncementインスタンスを含むクエリを返す。

        ユーザーがスタッフの場合は全ての下書きインスタンスを含むもの、それ以外
        の場合は空のクエリを返す

        Args:
            user (User instance): DjangoのUserモデル

        Returns:
            指定されたユーザーに対して公開されているAnnouncementインスタンスを
            含むQuerySet
        """
        if user and user.is_staff:
            return self.filter(pub_state='draft')
        return self.none()


class Announcement(models.Model):
    """
    スタッフがメンバーに告知する際に使用するモデル
    """

    # 必須フィールド
    pub_state = models.CharField(_("Publish status"),
                                 max_length=10, choices=PUB_STATES,
                                 default="public")
    title = models.CharField(_('Title'), max_length=128)
    body = models.TextField(_('Body'))
    # 自動記載フィールド
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               related_name='created_announcements',
                               editable=False)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modified at'), auto_now=True)
    last_modifier = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Last modified by'),
        editable=False, null=True, related_name='last_modified_announcements')
    objects = AnnouncementManager()

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Announcement')
        verbose_name_plural = _('Announcements')
        permissions = (
            ('view_announcement', 'Can view the announcement'),
        )

    def __str__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        kwargs = dict(pk=self.pk)
        if self.pub_state == 'draft':
            return ('announcements_announcement_update', (), kwargs)
        return ('announcements_announcement_detail', (), kwargs)


from permission import add_permission_logic
from .perms import AnnouncementPermissionLogic
add_permission_logic(Announcement, AnnouncementPermissionLogic())

from .activity import AnnouncementActivityMediator
registry.register(Announcement, AnnouncementActivityMediator())
