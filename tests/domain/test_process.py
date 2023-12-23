import pytest
from dumbo_utils.validation import ValidationError

from dumbo_runlim.domain.process import CPUAffinity, Process
from dumbo_runlim.domain.resources import Limit


def test_cpu_affinity_default_to_all():
    assert CPUAffinity().value == CPUAffinity.cpus()


def test_cpu_affinity_must_be_cpu():
    with pytest.raises(ValidationError):
        CPUAffinity.of(-1)
