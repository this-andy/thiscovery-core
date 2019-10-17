import uuid
import json
from abc import ABC

if __name__ == "__main__":
    from api.common.utilities import now_with_tz, validate_uuid, validate_utc_datetime, DetailedValueError
else:
    from .utilities import now_with_tz, validate_uuid, validate_utc_datetime, DetailedValueError


class EntityBase(ABC):

    def __init__(self, entity_json=[], correlation_id=None):
        if 'id' in entity_json:
            try:
                self.id = validate_uuid(entity_json['id'])
            except DetailedValueError as err:
                err.add_correlation_id(correlation_id)
                raise err
        else:
            self.id = str(uuid.uuid4())

        if 'created' in entity_json:
            try:
                self.created = validate_utc_datetime(entity_json['created'])
            except DetailedValueError as err:
                err.add_correlation_id(correlation_id)
                raise err
        else:
            self.created = str(now_with_tz())

        if 'modified' in entity_json:
            try:
                self.modified = validate_utc_datetime(entity_json['modified'])
            except DetailedValueError as err:
                err.add_correlation_id(correlation_id)
                raise err
        else:
            self.modified = str(now_with_tz())

    def to_json(self):
        # https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)