from dumbo_runlim.domain.resources import Resources, RealtimeUsage


def test_resources_exceed():
    resources = Resources(
        realtime=RealtimeUsage(10),
    )
    limit = Resources(
        realtime=RealtimeUsage(5),
    )
    assert resources.exceed_limit(limit)
    assert not limit.exceed_limit(resources)
