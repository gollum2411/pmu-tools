#Base classes for different metrics

print_error = lambda msg: False

class MetricBase(object):
    # Derived classes can override these
    level = -1
    server = False
    htoff = False
    sample = []
    sibling = None
    metricgroup = []

    def __init__(self):
        self.errcount = 0

    def compute(self, EV):
         try:
             self.val = self._compute(EV)
             self.thresh = self.val > 0
         except ZeroDivisionError:
             print_error("{0} zero division".format(self.__class__.__name__))
             self.errcount += 1
             self.val = 0
             self.thresh = False
         return self.val

    def _compute(self, EV):
        raise NotImplementedError()

class FrontendBound(MetricBase):
    level = 1
    name = "Frontend_Bound"
    domain = ""
    desc = ("\n"
            "This category reflects slots where the Frontend of the\n"
            "processor undersupplies its Backend.")
    metricgroup = ['TopDownL1']

class FrontendLatency(MetricBase):
    level = 2
    name = "Frontend_Latency"
    domain = "Slots"
    area = "FE"
    desc = ("\n"
            "This metric represents slots fraction the CPU was stalled\n"
            "due to Frontend latency issues.  For example; instruction-\n"
            "cache misses; iTLB misses or fetch stalls after a branch\n"
            "misprediction are categorized under Frontend Latency. In\n"
            "such cases; the Frontend eventually delivers no uops for\n"
            "some period.")
    htoff = False
    sample = []
    errcount = 0
    sibling = None
    server = False
    metricgroup = ['Frontend_Bound', 'TopDownL2']

class BadSpeculation(MetricBase):
    level = 1
    name = "Bad_Speculation"
    domain = "Slots"
    area = "BAD"
    desc = ("\n"
            "This category represents slots fraction wasted due to\n"
            "incorrect speculations. This includes slots used to issue\n"
            "uops that do not eventually get retired and slots for which\n"
            "the issue-pipeline was blocked due to recovery from earlier\n"
            "incorrect speculation. For example; wasted work due to miss-\n"
            "predicted branches are categorized under Bad Speculation\n"
            "category. Incorrect data speculation followed by Memory\n"
            "Ordering Nukes is another example.")
    metricgroup = ['Bad_Speculation', 'TopDownL1']

class Retiring(MetricBase):
    level = 1
    name = "Retiring"
    domain = "Slots"
    area = "RET"
    desc = ("\n"
            "This category represents slots fraction utilized by useful\n"
            "work i.e. issued uops that eventually get retired. Ideally;"
            "all pipeline slots would be attributed to the Retiring\n"
            "category.  Retiring of 100% would indicate the maximum 4\n"
            "uops retired per cycle has been achieved.  Maximizing\n"
            "Retiring typically increases the Instruction-Per-Cycle\n"
            "metric. Note that a high Retiring value does not necessary\n"
            "mean there is no room for more performance.  For example;\n"
            "Microcode assists are categorized under Retiring. They hurt\n"
            "performance and can often be avoided. . A high Retiring\n"
            "value for non-vectorized code may be a good hint for\n"
            "programmer to consider vectorizing his code.  Doing so\n"
            "essentially lets more computations be done without\n"
            "significantly increasing number of instructions thus\n"
            "improving the performance.")
    metricgroup = ['TopDownL1']

class BackendBound(MetricBase):
    level = 1
    name = "Backend_Bound"
    domain = "Slots"
    area = "BE"
    desc = ("\n"
            "This category represents slots fraction where no uops are\n"
            "being delivered due to a lack of required resources for\n"
            "accepting new uops in the Backend. Backend is the portion of\n"
            "the processor core where the out-of-order scheduler\n"
            "dispatches ready uops into their respective execution units;\n"
            "and once completed these uops get retired according to\n"
            "program order. For example; stalls due to data-cache misses\n"
            "or stalls due to the divider unit being overloaded are both\n"
            "categorized under Backend Bound. Backend Bound is further\n"
            "divided into two main categories: Memory Bound and Core\n"
            "Bound.")
    metricgroup = ['TopDownL1']

