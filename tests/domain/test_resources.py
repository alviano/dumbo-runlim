from dumbo_runlim.domain.resources import Usage, Resource, Limit


def test_resources_exceed():
    usage = Usage(
        time=Resource(10),
        system=Resource(1),
    )
    limit = Limit(
        time=Resource(10),
    )
    assert usage.exceed_limit(limit)
