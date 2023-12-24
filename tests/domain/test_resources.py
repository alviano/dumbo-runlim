from unittest.mock import Mock

import pytest
from dumbo_utils.objects import Bunch
from dumbo_utils.validation import ValidationError

from dumbo_runlim.domain.resources import Limit, Usage, UsageSummary


@pytest.fixture
def process():
    res = Mock()
    res.pid = 123
    res.children = Mock(return_value=[])
    res.cpu_times = Mock(return_value=Bunch(user=9, system=1))
    res.memory_info = Mock(return_value=Bunch(rss=32 * 1024 * 1024))
    res.memory_maps = Mock(return_value=Bunch([]))
    return res


def test_limit_cannot_be_negative():
    with pytest.raises(ValidationError):
        Limit(real=-1)


def test_usage_starts_at_zero():
    assert Usage().time == 0


def test_usage_update(process):
    usage = Usage()
    usage.update(process)
    assert usage.time == 10


def test_usage_summary_starts_at_zero():
    assert UsageSummary(object()).real == 0


def test_usage_summary_starts_unterminated():
    assert not UsageSummary(object()).terminated


def test_usage_summary_starts_terminate():
    key = object()
    usage_summary = UsageSummary(key)
    usage_summary.terminate("stopped", key=key)
    assert usage_summary.terminated


def test_usage_summary_update_terminated_by_time(process):
    key = object()
    usage_summary = UsageSummary(key)
    usage_summary.update(process, 5, Limit(time=8), key=key)
    assert usage_summary.terminated


def test_usage_summary_update_terminated_by_memory(process):
    key = object()
    usage_summary = UsageSummary(key)
    usage_summary.update(process, 5, Limit(memory=16), key=key)
    assert usage_summary.terminated
