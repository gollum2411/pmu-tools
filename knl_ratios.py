version = "1.0"

import metrics
import slm_ratios as slm

smt_enabled = False

PIPELINE_WIDTH = 4

def slots(ev, level):
    return PIPELINE_WIDTH * core_clks(ev, level)

def clks(ev, level):
    return ev("CPU_CLK_UNHALTED.THREAD", level)

def core_clks(ev, level):
    if smt_enabled:
        return ev("CPU_CLK_UNHALTED.THREAD", level) / 4

    return clks(ev, level)

def frontend_latency_cycles(ev, level):
    fn = lambda _ev, _level : min(_ev("CPU_CLK_UNHALTED.THREAD", level), _ev("NO_ALLOC_CYCLES.RAT_STALL", level))
    return ev(fn, level)

# Decorate _compute() methods to check that all required references are set
def check_refs(fn):
    def wrapped(self, *args, **kwargs):
        if not hasattr(self, "required_refs"):
            raise Exception("Missing refs object")
        refs = self.required_refs

        missing_refs = [ref for ref in self.required_refs
                        if not hasattr(self, ref)]
        if missing_refs:
            raise Exception("Missing references")

        fn(self, *args, **kwargs)

    wrapped.__name__ = fn.__name__
    return wrapped

# Decorator class to declare which reference dependecies between classes
class requires(object):
    def __init__(self, *required_refs):
        self.required_refs = required_refs

    def __call__(self, cls):
        setattr(cls, "required_refs", self.required_refs)
        return cls

def add_references(node, **refs):
    for name, obj in refs.items():
        setattr(node, name, obj)

class FrontendBound(metrics.FrontendBound):
    server = True
    def _compute(self, ev):
        return ev("NO_ALLOC_CYCLES.NOT_DELIVERED", 1) / clks(ev, self.level)

class FrontendLatency(metrics.FrontendLatency):
    server = True
    def _compute(self, ev):
        return PIPELINE_WIDTH * \
               frontend_latency_cycles(ev, self.level) / slots(ev, self.level)

class BadSpeculation(metrics.BadSpeculation):
    server = True
    def _compute(self, ev):
        return ev("NO_ALLOC_CYCLES.MISPREDICTS", 1) / clks(ev, self.level)

class Retiring(metrics.Retiring):
    server = True
    def _compute(self, ev):
        return ev("UOPS_RETIRED.ALL", 1) / (2 * clks(ev, self.level))

@requires("retiring", "bad_speculation", "frontend_bound")
class BackendBound(metrics.BackendBound):
    server = True
    def __init__(self, **kwargs):
        # initialize required references if passed in kwargs,
        # default to None
        for reqd in BackendBound.required_refs:
            setattr(self, reqd, kwargs.get(reqd, None))

    @check_refs
    def _compute(self, ev):
        return 1 - (self.retiring.compute(ev) +
                    self.bad_speculation.compute(ev) +
                    self.frontend_bound.compute(ev))

def add_parent(parent, nodes):
    for node in nodes:
        node.parent = parent

class Setup:
    def __init__(self, runner):
        # L1 objects
        frontend = FrontendBound()
        backend = BackendBound()
        bad_speculation = BadSpeculation()
        retiring = Retiring()

        # L2 objects
        frontend_latency = FrontendLatency()

        # Gather MetricBase objects in the local scope
        knl_metrics = [obj for obj in locals().values()
                if issubclass(obj.__class__, metrics.MetricBase)]

        # Sort them based on their level attribute
        level = lambda m : m.level
        knl_metrics = sorted(knl_metrics, key=level)

        # Add parent to L1 objects - None
        add_parent(None, [obj for obj in knl_metrics
                          if obj.level == 1])

        # Add parents to L2 objects
        add_parent(frontend,
                  (frontend_latency,))

        # References required between objects
        add_references(backend,
            retiring=retiring, bad_speculation=bad_speculation,
            frontend_bound=frontend)

        # pass to runner
        map(lambda m : runner.run(m), knl_metrics)

        # User visible metrics
        user_metrics = (
            slm.Metric_IPC(),
            slm.Metric_CPI(),
            slm.Metric_TurboUtilization(),
            slm.Metric_CLKS(),
            slm.Metric_Time(),
        )

        # Pass metrics to runner
        map(lambda m : runner.metric(m), user_metrics)

