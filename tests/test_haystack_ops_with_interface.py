from shaystack.providers import get_provider


def test_ops_without_implementation():
    # GIVEN
    provider = get_provider('tests.tstprovider_no_implementation', {})

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 2


def test_ops_with_readonly():
    # GIVEN
    provider = get_provider('tests.tstprovider_readonly', {})

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 4
    assert ops[2]['name'] == 'read'
    assert ops[3]['name'] == 'hisRead'


def test_ops_with_writeonly():
    # GIVEN
    provider = get_provider('tests.tstprovider_write', {})

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 4
    assert ops[2]['name'] == 'pointWrite'
    assert ops[3]['name'] == 'hisWrite'


def test_ops_with_subscribe():
    # GIVEN
    provider = get_provider('tests.tstprovider_subscribe', {})

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 5
    assert ops[2]['name'] == 'watchSub'
    assert ops[3]['name'] == 'watchUnsub'
    assert ops[4]['name'] == 'watchPoll'


def test_ops_with_invoke_action():
    # GIVEN
    provider = get_provider('tests.tstprovider_invokeaction', {})

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 3
    assert ops[2]['name'] == 'invokeAction'


def test_ops_with_nav():
    # GIVEN
    provider = get_provider('tests.tstprovider_nav', {})

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 3
    assert ops[2]['name'] == 'nav'
