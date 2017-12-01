from flask_uuid import UUID_RE
from six import string_types

DATASET_NAME_LEN_MIN = 1
DATASET_NAME_LEN_MAX = 100

CLASS_NAME_LEN_MIN = 1
CLASS_NAME_LEN_MAX = 100


def validate(dataset):
    """Validator for datasets.

    Dataset must have the following structure:
    {
        - name (string)
        - description (string, optional)
        - classes (list of class dicts)
            {
                - name (string)
                - description (string, optional)
                - recordings (list of UUIDs)
            }
    }

    Complete dataset must contain at least two classes with two recordings in
    each class.

    Args:
        dataset: Dataset stored in a dictionary.

    Raises:
        ValidationException: A general exception for validation errors.
        IncompleteDatasetException: Raised in cases when one of "completeness"
            requirements is not satisfied.
    """
    if not isinstance(dataset, dict):
        raise ValidationException("Dataset must be a dictionary.")
    _check_dict_structure(
        dataset,
        [
            ("name", True),
            ("description", False),
            ("classes", True),
            ("public", True),
        ],
        "dataset dictionary",
    )

    # Name
    # TODO merge with class name validation
    if not isinstance(dataset["name"], string_types):
        raise ValidationException("Field `name` must be a string.")
    if not (DATASET_NAME_LEN_MIN < len(dataset["name"]) < DATASET_NAME_LEN_MAX):
        raise ValidationException("Dataset name must be between %s and %s characters" %
                                  (DATASET_NAME_LEN_MIN, DATASET_NAME_LEN_MAX))

    # Description (optional)
    if "description" in dataset and dataset["description"] is not None:
        if not isinstance(dataset["description"], string_types):
            raise ValidationException("Value of `description` in a dataset must be a string.")

    # Classes
    _validate_classes(dataset["classes"])

    # Publicity
    if not isinstance(dataset["public"], bool):
        raise ValidationException('Value of `public` must be a boolean.')


def validate_recordings(data):
    """Validator for recordings data.

    Data must have the following structure:
    {
        - class_name (string)
        - recordings (list of UUIDs)
    }

    Args:
        data: Data stored in a dictionary.

    Raises:
        ValidationException: A general exception for validation errors.
    """
    if not isinstance(data, dict):
        raise ValidationException("Data must be a dictionary.")

    _check_dict_structure(
        data,
        [
            ("class_name", True),
            ("recordings", True)
        ],
        "recordings dictionary"
    )
    _validate_class_name("class_name", data["class_name"])
    _validate_recordings(data["recordings"], data["class_name"], allow_empty=False)


def _validate_classes(classes):
    if not isinstance(classes, list):
        raise ValidationException("Field `classes` must be a list of dictionaries.")
    for idx, cls in enumerate(classes):
        _validate_class(cls, idx)


def _validate_class(cls, idx):
    if not isinstance(cls, dict):
        raise ValidationException("Class number %s is not a dictionary. All classes "
                                  "must be dictionaries." % idx)
    _check_dict_structure(
        cls,
        [
            ("name", True),
            ("description", False),
            ("recordings", True),
        ],
        "class number %s" % idx,
    )

    # Name
    _validate_class_name("class", cls["name"], idx)

    # Description (optional)
    if "description" in cls and cls["description"] is not None:
        if not isinstance(cls["description"], string_types):
            raise ValidationException('Field `description` in class "%s" (number %s) is not a string.' %
                                      (cls["name"], idx))

    # Recordings
    _validate_recordings(cls["recordings"], cls["name"], idx)


def _validate_class_name(field, name, cls_index=None):
    message = " in the class number %s" % cls_index if cls_index is not None else ''

    if not isinstance(name, string_types):
        raise ValidationException("Field `%s`%s is not a string." % (field, message))

    if not (CLASS_NAME_LEN_MIN < len(name) < CLASS_NAME_LEN_MAX):
        raise ValidationException("Length of the `%s`%s doesn't fit the limits. "
                                  "Class name must be between %s and %s characters" %
                                  (field, message, CLASS_NAME_LEN_MIN, CLASS_NAME_LEN_MIN))


def _validate_recordings(recordings, cls_name, cls_index=None, allow_empty=True):
    message = ' in class "%s" (number %s)' % (cls_name, cls_index) if cls_index is not None else ''

    if not isinstance(recordings, list):
        raise ValidationException('Field `recordings`%s is not a list.' % message)

    if not allow_empty and len(recordings) == 0:
        raise ValidationException('Field `recordings`%s is empty.' % message)

    for recording in recordings:
        if not UUID_RE.match(recording):
            raise ValidationException('"%s" is not a valid recording MBID %s.' %
                                      (recording, message))


def _check_dict_structure(dictionary, keys, error_location):
    """Checks if dictionary contains only allowed values and, if necessary, if
    required items are missing.

    Args:
        dictionary: Dictionary that needs to be checked.
        keys: List of <name, required> tuples. `required` value must be a boolean:
            True if the field is required, False if not.
        error_location: Part of the error message that indicates where error occurs.

    Raises:
        ValidationException when dictionary structure doesn't match the requirements.
    """
    allowed_keys = [v[0] for v in keys]
    dict_keys = dictionary.keys()
    print(dict_keys)
    for k, req in keys:
        if req and k not in dict_keys:
            raise ValidationException("Field `%s` is missing from %s." % (k, error_location))
    for key in dict_keys:
        if key not in allowed_keys:
            raise ValidationException("Unexpected field `%s` in %s." % (key, error_location))


class ValidationException(Exception):
    """Base class for dataset validation exceptions."""
    pass
