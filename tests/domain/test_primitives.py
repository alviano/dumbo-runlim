import pytest
from dumbo_utils.validation import ValidationError

from dumbo_runlim.domain.process import CPUAffinity, Tag


def test_cpu_affinity_default_to_all():
    assert CPUAffinity().value == CPUAffinity.cpus()


def test_cpu_affinity_must_be_cpu():
    with pytest.raises(ValidationError):
        CPUAffinity.of(-1)


@pytest.mark.parametrize("tag", [
    "foo",
    "foo-1",
    "foo_2",
    "foo 2",
])
def test_tag_valid_values(tag):
    assert tag in str(Tag(tag))


@pytest.mark.parametrize("tag", [
    "foo'",
    "foo!",
    "foo^",
    "foo\"",
    "foo[",
    "foo]",
])
def test_tag_invalid_values(tag):
    with pytest.raises(ValidationError):
        Tag(tag)
