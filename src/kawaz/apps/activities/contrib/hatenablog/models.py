import os
from django.db import models
from django.utils.translation import ugettext as _


class HatenablogEntry(models.Model):
    """
    はてなブログで運営されているKawaz広報ブログの各エントリーを表すモデル
    """
    def _get_upload_path(self, filename):
        basedir = os.path.join('thumbnails',
                               'activities',
                               'contrib',
                               'hatenablog')
        return os.path.join(basedir, filename)

    title = models.CharField(_('Title'), max_length=128)
    url = models.URLField(_('URL'), unique=True)
    thumbnail = models.ImageField(_('Image'),
                                  upload_to=_get_upload_path,
                                  default='')
    created_at = models.DateTimeField(_('Created at'))

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Hatenablog entry')
        verbose_name_plural = _('Hatenablog entries')
