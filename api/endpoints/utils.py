import uuid

if 'api.endpoints' in __name__:
    from .common.utilities import DetailedValueError
else:
    from common.utilities import DetailedValueError

def validate_uuid_DNU(s):
    try:
        uuid.UUID(s, version=4)
        if uuid.UUID(s).version != 4:
            errorjson = {'uuid': s}
            raise DetailedValueError('uuid is not version 4', errorjson)
        return s
    except ValueError:
        errorjson = {'uuid': s}
        raise DetailedValueError('invalid uuid', errorjson)