from __future__ import absolute_import, print_function, unicode_literals

import re
from decimal import Decimal

# Matches 'gzip' or 'compress'
_compress_type_str = r'[a-zA-Z0-9._-]+'


# Matches either '*', 'image/*', or 'image/png'
_valid_encoding_type = re.compile(r'^(?:[a-zA-Z-]+)$')

# Matches the 'q=1.23' from the parameters of a Accept mime types
_q_match = re.compile(r'(?:^|;)\s*q=([0-9.-]+)(?:$|;)')


class _AcceptableEncoding:
    encoding_type = None
    weight = Decimal(1)
    pattern = None

    def __init__(self, raw_encoding_type):
        bits = raw_encoding_type.split(';', 1)

        encoding_type = bits[0]
        if not _valid_encoding_type.match(encoding_type):
            raise ValueError(f'"{encoding_type}" is not a valid encoding type')

        tail = ''
        if (len(bits) > 1):
            tail = bits[1]

        self.encoding_type = encoding_type
        self.weight = _get_weight(tail)
        self.pattern = re.compile('^' + re.escape(encoding_type) + '$')

    def matches(self, encoding_type):
        return self.pattern.match(encoding_type)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        display = self.encoding_type
        if self.weight != Decimal(1):
            display += '; q=%0.2f' % self.weight

        return display

    def __repr__(self):
        return '<AcceptableType {0}>'.format(self)

    def __eq__(self, other):
        if not isinstance(other, _AcceptableEncoding):
            return NotImplemented
        return (self.encoding_type, self.weight) == (other.encoding_type, other.weight)

    def __lt__(self, other):
        if not isinstance(other, _AcceptableEncoding):
            return NotImplemented
        return self.weight < other.weight


def get_best_encoding_match(header, available_encoding):
    """Find the best encoding type to respond to a request with,
    from an ``Accept-Encoding`` header and list of encoding types
    the application supports.

    .. code-block:: python

        return_data = reticulate_splines()
        return_type = get_best_encoding_match(
            request.META.get('HTTP_ACCEPT_ENCODING'),
            ['gzip', 'compress'])
        if return_type == 'compress':
            return ...
        if return_type == 'gzip':
            return ...

    :param header: The HTTP ``Accept-Encoding`` header from the request.
    :type header: str
    :param available_encoding: The response encoding types the application supports.
    :type available_encoding: List[str]
    :return: The best matching encoding type from the supported response
        encoding types, or ``None`` if there are no valid matches.
    """
    acceptable_types = _parse_header(header)

    for acceptable_type in acceptable_types:
        for available_type in available_encoding:
            if acceptable_type.matches(available_type):
                return available_type

    return None


def _parse_header(header):
    """Parse an ``Accept`` header into a sorted list of :class:`AcceptableType`
    instances.
    """
    raw_encoding_types = header.split(',')
    encoding_types = []
    for raw_encoding_type in raw_encoding_types:
        try:
            encoding_types.append(_AcceptableEncoding(raw_encoding_type.strip()))
        except ValueError:
            pass

    return sorted(encoding_types, reverse=True)


def _get_weight(tail):
    """Given the tail of a mime type header (the bit after the first ``;``),
    find the ``q`` (weight, or quality) parameter.

    If no valid ``q`` parameter is found, default to ``1``, as per the spec.
    """
    match = re.search(_q_match, tail)
    if match:
        try:
            return Decimal(match.group(1))
        except ValueError:
            pass

    # Default weight is 1
    return Decimal(1)



