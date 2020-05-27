import pytest

from http_tools import get_best_encoding_match


def test_accept_encoding_simple():
    # WHEN
    encoding = get_best_encoding_match("gzip,compress",["gzip","compress"])

    # GIVEN
    assert encoding == "gzip"


def test_accept_encoding_unknown():
    # WHEN
    encoding = get_best_encoding_match("gzip", ["compress"])

    # GIVEN
    assert encoding == None

def test_accept_encoding_complex():
    # WHEN
    encoding = get_best_encoding_match("gzip;q=0.8, compress", ["compress"])

    # GIVEN
    assert encoding == "compress"