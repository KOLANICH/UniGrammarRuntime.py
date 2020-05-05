import typing
from collections import OrderedDict, defaultdict
from functools import partial
from math import sqrt


class _BenchmarkMode:
	__all__ = ()


class BenchmarkModeMeta(type):
	__slots__ = ()

	def __new__(cls: typing.Type["BenchmarkModeMeta"], className: str, parents: typing.Tuple[type, ...], attrs: typing.Dict[str, typing.Any], *args, **kwargs) -> typing.Type["BenchmarkMode"]:
		attrs = type(attrs)(attrs)
		attrs["__all__"] = parents[0].__all__ + tuple(v for k, v in attrs.items() if k[0] != "_")
		res = super().__new__(cls, className, parents, attrs, *args, **kwargs)
		return res


StatementIncompleteFuncT = typing.Callable[[typing.Any], None]
SetupFuncT = typing.Callable[[], typing.Any]
CriteriaFuncRetT = typing.Tuple[StatementIncompleteFuncT, SetupFuncT]
CriteriaFuncT = typing.Callable[["InMemoryGrammarResources", str], CriteriaFuncRetT]
CriteriaT = typing.Union[str, CriteriaFuncT]


class BenchmarkMode(_BenchmarkMode, metaclass=BenchmarkModeMeta):
	"""All the methods are static, but we cannot use @classmethod and @staticmethod because they cause problems with __name__
	also pylint considers first arg as `self`, so we disable `no-member`
	"""

	# pylint:disable=no-self-argument,no-member

	def parseRaw(grammarData: "InMemoryGrammarResources", backendName: str) -> CriteriaFuncRetT:
		b = grammarData.getBackend(backendName)
		return b.parse, lambda s: s

	def preprocess(grammarData: "InMemoryGrammarResources", backendName: str) -> CriteriaFuncRetT:
		b = grammarData.getBackend(backendName)
		return b.preprocessAST, b.parse

	def wrapper(grammarData: "InMemoryGrammarResources", backendName: str) -> CriteriaFuncRetT:
		w = grammarData.getWrapper(backendName)
		return w.__MAIN_PRODUCTION__, lambda s: w.backend.preprocessAST(w.backend.parse(s))


def normalizeCriteria(criteria: typing.Iterable[CriteriaT]) -> typing.Tuple[typing.Iterable[str], typing.Iterable[CriteriaFuncT]]:
	criteriaStr = []
	criteriaFunc = []
	for c in criteria:
		if isinstance(c, str):
			criteriaStr.append(c)
			criteriaFunc.append(getattr(BenchmarkMode, c))
		else:
			criteriaStr.append(c.__name__)
			criteriaFunc.append(c)
	return tuple(criteriaStr), tuple(criteriaFunc)


class _BenchmarkRecords:
	__slots__ = ("root",)

	NAME = None
	DOWNSTREAM = None

	def __init__(self, root):
		self.root = root

	def getIndexer(self):
		return getattr(self.root, self.__class__.NAME)

	def _getIndex(self, k):
		return self.getIndexer()[k]

	def _getItem(self, idx):
		return self.__class__.DOWNSTREAM(self.root, self, idx)

	def __getitem__(self, k):
		return self._getItem(self._getIndex(k))

	def __len__(self):
		return len(self.getIndexer())

	def __iter__(self):
		return self.keys()

	def items(self):
		for k, idx in self.getIndexer().items():
			yield k, self._getItem(idx)

	def keys(self):
		return iter(self.getIndexer().keys())

	def values(self):
		for idx in self.getIndexer().values():
			yield self._getItem(idx)


class RecordsLayer(_BenchmarkRecords):
	__slots__ = ("parent", "index")

	def __init__(self, root, parent, index):
		super().__init__(root)
		self.parent = parent
		self.index = index

	@property
	def denormMatrix(self):
		return self.parent.denormMatrix[self.index]


class LastLayer(RecordsLayer):
	def _getItem(self, idx):
		return self.denormMatrix[idx]


class BenchmarkStatistics:
	__slots__ = ("min", "max", "mean", "std", "iters", "repeats")

	def __init__(self, min: float, max: float, mean: float, std: float, iters: int, repeats: int):  # pylint:disable=redefined-builtin
		self.min = min
		self.max = max
		self.mean = mean
		self.std = std
		self.iters = iters
		self.repeats = repeats

	def __iter__(self):
		for k in __class__.__slots__:  # pylint:disable=undefined-variable
			yield getattr(self, k)

	def toTuple(self):
		return tuple(self)

	def __repr__(self):
		return self.__class__.__name__ + "(" + ", ".join(k + "=" + repr(getattr(self, k)) for k in __class__.__slots__) + ")"  # pylint:disable=undefined-variable

	@classmethod
	def fromSamples(cls, samples: typing.Iterable[float], iters: int) -> "BenchmarkStatistics":
		repeats = len(samples)
		mi = min(samples) / iters
		ma = max(samples) / iters
		me = sum(samples) / repeats
		vari = sum(bt * bt for bt in samples) / repeats - me * me
		std = sqrt(vari) / iters
		me /= iters
		return cls(mi, ma, me, std, iters, repeats)


class BenchmarksPerCriteria(LastLayer):
	__slots__ = ()
	NAME = "criteria"

	def _getItem(self, idx):
		return BenchmarkStatistics(*super()._getItem(idx))


class BenchmarksPerBackends(RecordsLayer):
	__slots__ = ()
	NAME = "backends"
	DOWNSTREAM = BenchmarksPerCriteria


class BenchmarkData(_BenchmarkRecords):
	__slots__ = ("criteria", "backends", "testData", "denormMatrix")
	NAME = "testData"
	DOWNSTREAM = BenchmarksPerBackends

	def __init__(self, criteria, backends: typing.Iterable[str], testData: typing.Iterable[str], denormMatrix: typing.Optional[typing.List[typing.List[typing.List[float]]]] = None) -> None:
		self.criteria = OrderedDict((k, i) for i, k in enumerate(criteria))
		self.backends = OrderedDict((k, i) for i, k in enumerate(backends))
		self.testData = OrderedDict((k, i) for i, k in enumerate(testData))
		if denormMatrix is None:
			denormMatrix = [
				[
					[None for i in range(len(self.criteria))]
					for j in range(len(self.backends))
				]
				for k in range(len(self.testData))
			]
		self.denormMatrix = denormMatrix
		super().__init__(self)

	def toNormalizedDict(self) -> typing.Mapping[str, typing.Any]:
		return {
			"criteria": tuple(self.criteria.keys()),
			"backends": tuple(self.backends.keys()),
			"testData": tuple(self.testData.keys()),
			"matrix": self.denormMatrix
		}

	def aggregateMetrics(self, criteria: typing.Optional[str] = None, stat: str = "min"):
		res = defaultdict(float)

		for dPMetrics in self.values():
			for backendName, backendMetricsPerCriteria in dPMetrics.items():
				if criteria is not None:
					res[backendName] += getattr(backendMetricsPerCriteria[criteria], stat)
				else:
					res[backendName] += sum(getattr(stats, stat) for stats in backendMetricsPerCriteria.values())
			return tuple(res.items())

	def getFastest(self, criteria: typing.Optional[str] = None):
		return min(self.aggregateMetrics(criteria, stat="min"), key=lambda it: it[1])  # 1 is for value

	def getSorted(self, criteria: typing.Optional[str] = None, reverse: bool = False):
		return sorted(self.aggregateMetrics(criteria, stat="min"), reverse=reverse, key=lambda it: it[1])  # 1 is for value

	@classmethod
	def fromNormalizedDict(cls, d: typing.Mapping[str, typing.Any]) -> "BenchmarkData":
		return cls(criteria=d["criteria"], backends=d["backends"], testData=d["testData"], denormMatrix=d["matrix"])


def _benchmarkSingle(Timer, stmtIncomplete, setup, dataPiece, smallCount, timeBudget) -> BenchmarkStatistics:
	stmtArg = setup(dataPiece)
	stmt = partial(stmtIncomplete, stmtArg)

	stmt()  # to test that works and to warm-up

	t = Timer(stmt=stmt)

	smallTime = t.timeit(number=smallCount)
	timePerIterPrelim = smallTime / smallCount
	restItersCount = round((timeBudget - smallTime) / timePerIterPrelim)

	iters = round(sqrt(restItersCount))
	repeats = restItersCount // iters

	bigTimes = t.repeat(repeat=repeats, number=iters)

	return BenchmarkStatistics.fromSamples(bigTimes, iters)


def _reBenchmark(res, grammarData, smallCount, timeBudget, testData, backendNames, benchmarkModesFuncs):
	from timeit import Timer  # pylint:disable=import-outside-toplevel

	for backendIndex, backendName in enumerate(backendNames):
		for modeIndex, benchmarkMode in enumerate(benchmarkModesFuncs):
			stmtIncomplete, setup = benchmarkMode(grammarData, backendName)

			for dataIndex, dataPiece in enumerate(testData):
				res.denormMatrix[dataIndex][backendIndex][modeIndex] = _benchmarkSingle(Timer, stmtIncomplete, setup, dataPiece, smallCount, timeBudget).toTuple()


def benchmark(grammarData: "InMemoryGrammarResources", testData: typing.Iterable[str], backendNames: typing.Iterable[str], timeBudget: float, benchmarkModes: typing.Iterable[CriteriaT], smallCount, prevRes=None):
	if isinstance(testData, str):
		testData = (testData,)
	if benchmarkModes is None:
		benchmarkModes = BenchmarkMode.__all__
	elif callable(benchmarkModes) or isinstance(benchmarkModes, str):
		benchmarkModes = (benchmarkModes,)

	benchmarkModesStrs, benchmarkModesFuncs = normalizeCriteria(benchmarkModes)

	if prevRes is None:
		res = BenchmarkData(benchmarkModesStrs, backendNames, testData)
	else:
		raise NotImplementedError("Currently editing is not implemented")

	_reBenchmark(res, grammarData, smallCount, timeBudget, testData, backendNames, benchmarkModesFuncs)

	return res
