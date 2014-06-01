import os
from django.db import models
from django.utils.translation import ugettext as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from markupfield.fields import MarkupField
from thumbnailfield.fields import ThumbnailField
from kawaz.core.db.decorators import validate_on_save
from kawaz.core.personas.models import Persona
from kawaz.apps.projects.models import Project


class Platform(models.Model):
    """
    プロダクトがサポートしているプラットフォームを表すモデル

    e.g. Windows, Mac, Browser, iOS, PS Vita など
    """
    def _get_upload_path(self, filename):
        basedir = os.path.join('icons', 'platforms', self.label.lower())
        return os.path.join(basedir, filename)

    label = models.CharField(_('Label'), max_length=32, unique=True)
    icon = models.ImageField(_('Icon'), upload_to=_get_upload_path)

    class Meta:
        # TODO: 並び替えが可能なように ordering 要素をもたせる
        ordering = ('label',)
        verbose_name = _('Platform')
        verbose_name_plural = _('Platforms')

    def __str__(self):
        return self.label


class Category(models.Model):
    """
    プロダクトが所属するカテゴリーを表すモデル

    e.g. ACT, STG, ADV など
    """
    label = models.CharField(_('Label'), max_length=32, unique=True)
    description = models.CharField(_('Description'), max_length=128)

    class Meta:
        # TODO: 並び替えが可能なように ordering 要素をもたせる
        ordering = ('pk',)
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.label


@validate_on_save
class Product(models.Model):
    """
    完成したプロダクトを表すモデル

    メンバーであれば誰でも作成・管理可能
    """
    def _get_advertisement_image_upload_path(self, filename):
        basedir = os.path.join('products', self.slug, 'advertisement_images')
        return os.path.join(basedir, filename)

    def _get_thumbnail_upload_path(self, filename):
        basedir = os.path.join('products', self.slug, 'thumbnails')
        return os.path.join(basedir, filename)

    DISPLAY_MODES = (
        ('featured', _('Featured')),
        ('tiled', _('Tiled')),
        ('normal', _('Normal')),
    )

    # 必須フィールド
    title = models.CharField(_('Title'), max_length=128, unique=True)
    slug = models.SlugField(_('Product slug'), unique=True,
                            help_text=_("It will be used on the url of the "
                                        "product thus it only allow "
                                        "alphabetical or numeric "
                                        "characters, underbar ('_'), and "
                                        "hyphen ('-'). "
                                        "Additionally this value cannot be "
                                        "modified for preventing the URL "
                                        "changes."))
    thumbnail = ThumbnailField(
        _('Thumbnail'),
        upload_to=_get_thumbnail_upload_path,
        patterns=settings.PRODUCT_THUMBNAIL_SIZE_PATTERNS,
        help_text=_("This would be used as a product thumbnail image. "
                    "The aspect ratio of the image should be 16:9."))
    description = MarkupField(_('Description'), max_length=4096,
                              markup_type='markdown')

    # 省略可能フィールド
    advertisement_image = ThumbnailField(
        _('Advertisement Image'),
        null=True, blank=True,
        upload_to=_get_advertisement_image_upload_path,
        patterns=settings.ADVERTISEMENT_IMAGE_SIZE_PATTERNS,
        help_text=_("This would be used in the top page. "
                    "The aspect ratio of the image should be 16:9"))
    trailer = models.URLField(
        _('Trailer'), null=True, blank=True,
        help_text=_("Enter URL of your trailer movie on the YouTube. "
                    "The movie would be embeded to the product page."))
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                null=True, blank=True)
    platforms = models.ManyToManyField(Platform, verbose_name=_('Platforms'))
    categories = models.ManyToManyField(Category, verbose_name=_('Categories'))
    publish_at = models.DateField(_('Publish at'))

    # 編集不可
    administrators = models.ManyToManyField(Persona, editable=False,
                                            verbose_name=_('Administrators'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    #
    # Productの表示順番を制御する値です。Formsでexclude設定されるため通常
    # ユーザーからは変更できません（adminサイトでの修正）
    #
    # featured: トップページのカルーセル + トップページにタイル表示されます。
    #           設定するにはadvertisement_imageの設定が必要です
    # tiled : トップページにタイル表示されます。
    #         タイル表示は thumbnails が使われます
    # normal : トップページには表示されず、see more内でのみタイル表示されます
    #
    display_mode = models.CharField(
        _('Display mode'),
        max_length=10, choices=DISPLAY_MODES, default='normal',
        help_text=_("How the product displayed on the site top. "
                    "To use `featured`, it require `advertisement_image`."))

    class Meta:
        ordering = ('display_mode', '-publish_at',)
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        permissions = (
            ('join_product', 'Can join to the product'),
            ('quit_product', 'Can quit from the product'),
        )

    def __str__(self):
        return self.title

    def clean(self):
        if not self.advertisement_image and self.display_mode == 'featured':
            # advertisement_imageがセットされていないときは
            # display_modeをfeaturedに設定できない
            raise ValidationError(_("`feature` display mode require "
                                    "`advertisement_image`."))

    def join(self, user, save=True):
        """
        指定されたユーザーを管理者にする

        ユーザーに参加権限がない場合は `PermissionDenied` を投げる
        """
        if not user.has_perm('products.join_product', self):
            raise PermissionDenied
        self.administrators.add(user)
        if save:
            self.save()

    def quit(self, user, save=True):
        """
        指定されたユーザーを管理者から外す

        ユーザーに脱退権限がない場合は `PermissionDenied` を投げる
        """
        if not user.has_perm('products.quit_product', self):
            raise PermissionDenied
        self.administrators.remove(user)
        if save:
            self.save()

    @models.permalink
    def get_absolute_url(self):
        return ('products_product_detail', (), {
            'slug': self.slug
        })


class AbstractRelease(models.Model):
    """
    リリース形態のアブストラクトモデル
    """
    label = models.CharField(_('Label'), max_length=32)
    platform = models.ForeignKey(Platform, verbose_name=_('Platform'))
    version = models.CharField(_('Version'), max_length=32)
    product = models.ForeignKey(Product, verbose_name=_('Product'),
                                related_name='%(class)ss')
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        abstract = True
        ordering = ('platform__pk', 'product__pk')

    def __str__(self):
        return "{}({})".format(str(self.product), str(self.platform))


class PackageRelease(AbstractRelease):
    """
    ファイル添付形式でのリリースモデル
    """
    def _get_upload_path(self, filename):
        basedir = os.path.join('products', self.product.slug, 'releases')
        return os.path.join(basedir, filename)

    file_content = models.FileField(_('File'), upload_to=_get_upload_path)
    downloads = models.PositiveIntegerField(
        _('Downloads'), default=0,
        editable=False,
        help_text=_("The number of downloads"))

    class Meta(AbstractRelease.Meta):
        verbose_name = _('Package release')
        verbose_name_plural = _('Package releases')


class URLRelease(AbstractRelease):
    """
    URL指定形式でのリリースモデル。主に外部ホスティングでのリリース用

    e.g. iTunes App Store, Google Play, Vector など
    """
    url = models.URLField(_('URL'))
    pageview = models.PositiveIntegerField(
        _('Page view'), default=0,
        editable=False,
        help_text=_("The number of page views"))

    class Meta(AbstractRelease.Meta):
        verbose_name = _('URL release')
        verbose_name_plural = _('URL releases')

    @property
    def is_appstore(self):
        """App Store の URL か否か"""
        # ProductページにApp Storeのバッジを置いたりするのに使います
        return self.url.startswith('https://itunes.apple.com')

    @property
    def is_googleplay(self):
        """Google Play の URL か否か"""
        # ProductページにGoogle Playのバッジを置いたりするのに使います
        return self.url.startswith('https://play.google.com')


class Screenshot(models.Model):
    """
    プロダクトのスクリーンショットモデル

    プロダクト管理者は何枚でもプロダクトに関連付けることが出来る
    """
    def _get_upload_path(self, filename):
        basedir = os.path.join('products', self.product.slug, 'screenshots')
        return os.path.join(basedir, filename)

    image = ThumbnailField(
        _('Image'), upload_to=_get_upload_path,
        patterns=settings.SCREENSHOT_IMAGE_SIZE_PATTERNS)
    product = models.ForeignKey(Product, verbose_name=_('Product'))

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Screen shot')
        verbose_name_plural = _('Screen shots')

    def __str__(self):
        return '{}({})'.format(self.image.name, self.product.title)


from permission import add_permission_logic
from .perms import ProductPermissionLogic
from kawaz.core.personas.perms import ChildrenPermissionLogic
add_permission_logic(Product, ChildrenPermissionLogic(
    add_permission=True,
    change_permission=False,
    delete_permission=False
))
add_permission_logic(Product, ProductPermissionLogic())