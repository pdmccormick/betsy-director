import json

class JsonSerializer(object):
    DEFAULT_INDENT = 4

    HELPERS = []

    @classmethod
    def dumps(cls, obj, indent=None):
        if indent is None:
            indent = cls.DEFAULT_INDENT

        return json.dumps(obj, indent=indent, default=cls._json_dumps_default)

    @classmethod
    def dump(cls, obj, fp, indent=None):
        fp.write(cls.dumps(obj, indent=indent))

    @classmethod
    def _json_dumps_default(cls, obj):
        to_object = getattr(obj, 'to_object', None)
        if to_object is not None:
            return to_object()

        for clazz, helper_func in cls.HELPERS:
            if isinstance(obj, clazz):
                return helper_func(obj)

        return unicode(obj)

    @classmethod
    def register_helper(cls, clazz, helper_func):
        cls.HELPERS.append(( clazz, helper_func ))

try:
    from netaddr import EUI, IPAddress

    JsonSerializer.register_helper(EUI, unicode)
    JsonSerializer.register_helper(IPAddress, unicode)
except ImportError:
    pass

