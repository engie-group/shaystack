from shaystack.providers import get_provider


def test_ops():
    provider = get_provider("shaystack.providers.ping", {})
    result = provider.ops()
    assert len(result) == 12


def test_about():
    provider = get_provider("shaystack.providers.ping", {})
    result = provider.about("http://localhost")
    assert result[0]['moduleName'] == 'PingProvider'


def test_read():
    provider = get_provider("shaystack.providers.ping", {})
    result = provider.read(0, None, None, None, None)
    assert len(result) == 1
