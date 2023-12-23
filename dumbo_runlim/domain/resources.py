import dataclasses

import typeguard
from dumbo_utils import primitives


@primitives.bounded_integer(min_value=0, max_value=10**100)
class Resource:
    pass


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Limit:
    realtime: Resource = dataclasses.field(default=Resource(Resource.max_value()))
    time: Resource = dataclasses.field(default=Resource(Resource.max_value()))
    memory: Resource = dataclasses.field(default=Resource(Resource.max_value()))
    swap: Resource = dataclasses.field(default=Resource(Resource.max_value()))


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Usage:
    real: Resource = dataclasses.field(default=Resource(Resource.min_value()))
    time: Resource = dataclasses.field(default=Resource(Resource.min_value()))
    system: Resource = dataclasses.field(default=Resource(Resource.min_value()))
    rss: Resource = dataclasses.field(default=Resource(Resource.min_value()))
    swap: Resource = dataclasses.field(default=Resource(Resource.min_value()))

    def exceed_limit(self, limit: Limit) -> bool:
        return (self.real > limit.realtime or
                (self.time + self.system) > limit.time or
                (self.rss + self.swap) > limit.memory or
                self.swap > limit.swap)
