from django.conf import settings

def validate_on_save():
    """
    class decorator to enable validation when model was saved.

    Usage :
    @validate_on_save
    class Entry(models.Model):
        def clean(self):
            if self.number < 0:
                raise ValidationError('number must be positive')
    """
    def decorated(klass):
        save = klass.save
        def wrapper(self, force_insert=False, force_update=False, **kwargs):
            if not (force_insert or force_update):
                self.full_clean()
            save(force_insert, force_update, **kwargs)
        if settings.VALIDATE_ON_SAVE:
            setattr(klass, 'save', wrapper)
        return klass
    return decorated