import os
import mimetypes
from django.conf import settings
from django.views.generic.detail import BaseDetailView
from django.http.response import HttpResponse, HttpResponseNotFound
from django.core.servers.basehttp import FileWrapper

from .models import Material

class MaterialDetailView(BaseDetailView):
    model = Material
    slug_field = 'slug'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            name = self.object.filename
            mime_type_guess = mimetypes.guess_type(name)
            path = os.path.join(settings.MEDIA_ROOT, self.object.content_file.name)
            # withをすると、変なタイミングでcloseされてしまって正常にアクセスできない
            file = open(path, 'rb')
            response = HttpResponse(FileWrapper(file), content_type=mime_type_guess[0])
            response['Content-Disposition'] = 'attachment; filename={}'.format(name)
            return response
        except:
            pass
        return HttpResponseNotFound()