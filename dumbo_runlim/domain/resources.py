import dataclasses

import typeguard
from dumbo_utils import primitives


MAX_VALUE = 10**100


@primitives.bounded_integer(min_value=0, max_value=MAX_VALUE)
class RealtimeUsage:
    pass


@primitives.bounded_integer(min_value=0, max_value=MAX_VALUE)
class TimeUsage:
    pass


@primitives.bounded_integer(min_value=0, max_value=MAX_VALUE)
class MemoryUsage:
    pass


@primitives.bounded_integer(min_value=0, max_value=MAX_VALUE)
class SwapUsage:
    pass


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Resources:
    realtime: RealtimeUsage = dataclasses.field(default=RealtimeUsage(MAX_VALUE))
    time: TimeUsage = dataclasses.field(default=TimeUsage(MAX_VALUE))
    memory: MemoryUsage = dataclasses.field(default=MemoryUsage(MAX_VALUE))
    swap: SwapUsage = dataclasses.field(default=SwapUsage(MAX_VALUE))

    def exceed_limit(self, limit: "Resources") -> bool:
        return (self.realtime > limit.realtime or self.time > limit.time or self.memory > limit.memory or
                self.swap > limit.swap)
