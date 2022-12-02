import magic
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError


@deconstructible
class FileValidator(object):
    error_messages = {
        "max_size": "Upewnij się, że rozmiar pliku nie jest większy niż %(max_size)s.",
        "min_size": "Upewnij się, że rozmiar pliku nie jest mniejszy niż %(min_size)s.",
        "content_type": "Pliki typu %(content_type)s nie są obsługiwane.",
    }

    def __init__(self, max_size=None, min_size=None, content_types=()):
        self.max_size = max_size
        self.min_size = min_size
        self.content_types = content_types

    def __call__(self, data):
        if self.max_size is not None and data.size > self.max_size:
            params = {
                "max_size": filesizeformat(self.max_size),
                "size": filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages["max_size"], "max_size", params)

        if self.min_size is not None and data.size < self.min_size:
            params = {
                "min_size": filesizeformat(self.min_size),
                "size": filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages["min_size"], "min_size", params)

        if self.content_types:
            content_type = magic.from_buffer(data.read(), mime=True)
            data.seek(0)

            if content_type not in self.content_types:
                params = {"content_type": content_type}
                raise ValidationError(
                    self.error_messages["content_type"], "content_type", params
                )

    def __eq__(self, other):
        return (
            isinstance(other, FileValidator)
            and self.max_size == other.max_size
            and self.min_size == other.min_size
            and self.content_types == other.content_types
        )
