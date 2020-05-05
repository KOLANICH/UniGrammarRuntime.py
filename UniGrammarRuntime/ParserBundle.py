import typing
from collections import defaultdict
from pathlib import Path
from warnings import warn

from transformerz import dummyTransformer
from transformerz.core import Transformer, TransformerBase
from transformerz.serialization.json import jsonFancySerializer
from transformerz.serialization.python import pythonASTFancySerializer
from transformerz.text import utf8Transformer
from urm.core import Dynamic
from urm.fields import Field0D, FieldND
from urm.mappers import ColdMapper, HotMapper
from urm.mappers.key import PrefixKeyMapper, fieldNameKeyMapper
from urm.mappers.serializer import JustReturnSerializerMapper
from urm.ProtoBundle import ProtoBundle
from urm.storers.cold import FileSaver
from urm.storers.hot import PrefixCacher

from . import backends  # pylint:disable=unused-import # Imports all the stuff this way creating classes auto-registered to the registry via a metaclass
from .benchmark import BenchmarkData, benchmark
from .IParsingBackend import backendsRegistry
from .utils import getPythonModule

#fileSaverIGR = FileSaver(Dynamic(("parent", "bundleDir")), Dynamic(("parent", "serializer", "fileExtension")))
fileSaverIGR = FileSaver(Dynamic(("parent", "bundleDir")), "json")
nameD = Dynamic("name")
ourCacher = HotMapper(fieldNameKeyMapper, PrefixCacher())


class OurTransformer(Transformer):
	registry = None


benchmarkDataNormalizer = OurTransformer("benchmarkDataNormalizer", lambda d: d.toNormalizedDict(), BenchmarkData.fromNormalizedDict, dict, BenchmarkData)


def constantParamsSerializerMapper(parent: ProtoBundle) -> TransformerBase:
	return parent.parent.serializer


def benchmarkDataSerializerMapper(parent: ProtoBundle) -> TransformerBase:
	return parent.parent.serializer + benchmarkDataNormalizer


pythonASTSerializerMapper = JustReturnSerializerMapper(utf8Transformer + pythonASTFancySerializer)


class InMemoryGrammarResources(ProtoBundle):
	__slots__ = ("parent", "name", "_backendsData", "_metrics", "_capSchema", "_iterSchema", "_wraperClass")

	capSchema = Field0D(ColdMapper(PrefixKeyMapper("schemas", "capless", nameD), fileSaverIGR, constantParamsSerializerMapper), ourCacher)
	iterSchema = Field0D(ColdMapper(PrefixKeyMapper("schemas", "iterless", nameD), fileSaverIGR, constantParamsSerializerMapper), ourCacher)

	metrics = Field0D(ColdMapper(PrefixKeyMapper("metrics", nameD), fileSaverIGR, benchmarkDataSerializerMapper), ourCacher)
	wrapperAST = Field0D(ColdMapper(PrefixKeyMapper("wrappers", nameD), FileSaver(Dynamic(("parent", "bundleDir")), "py"), pythonASTSerializerMapper))

	def __init__(self, name: str) -> None:
		self.name = name
		self.parent = None
		self._backendsData = defaultdict(dict)
		self._capSchema = None
		self._iterSchema = None
		self._wraperClass = None
		self._metrics = None

	def getWrapperModule(self):
		return getPythonModule(self.wrapperAST, self.parent.bundleDir / self.__class__.wrapperAST.strategy.cold.key.prefix[0] / (self.name + ".py"))

	@property
	def wrapperClass(self):
		res = self._wraperClass
		if res is None:
			self._wraperClass = res = self.getWrapperModule()["__MAIN_PARSER__"]
		return res

	def getWrapper(self, backendName: typing.Optional[str] = None):
		return self.wrapperClass(self.getBackend(backendName))

	#def __repr__(self):
	#	return self.__class__.__name__ + "<backends: " + repr(list(self.backendsData)) + ", iterSchema " + ("present" if self.iterSchema else "missing") + ", capSchema " + ("present" if self.capSchema else "missing") + ">"

	def getBackend(self, backendName: typing.Optional[str] = None):
		if backendName is None:
			backendName = self.getFastestBackendName()
		print(self.parent.backends[backendName])
		return self.parent.backends[backendName](self)

	def getFastestBackendName(self, criteria=None):
		fastestMetrics = self.metrics.getFastest(criteria)
		fastestBackendName = fastestMetrics[0]
		return fastestBackendName

	def benchmark(self, testData: typing.Iterable[str], backendNames: str = None, timeBudget: float = 10, benchmarkModes=None, smallCount=100):

		if isinstance(backendNames, str):
			backendNames = (backendNames,)
		elif backendNames is None:
			backendNames = tuple(self.parent.backends.keys())

		return benchmark(self, testData, backendNames, timeBudget, benchmarkModes, smallCount)

	def benchmarkAndUpdate(self, *args, **kwargs):
		metrics = self.benchmark(*args, **kwargs)
		self.metrics = metrics
		#self.save("metrics")
		return metrics

	benchmarkAndUpdate.__wraps__ = benchmark


class GrammarsCollection:
	"""Fuck that `defaultdict` that doesn't have arguments"""

	__slots__ = ("parent", "underlyingCollection",)

	def __init__(self, parent: "ParserBundle") -> None:
		self.parent = parent
		self.underlyingCollection = {}

	def __getitem__(self, k: str) -> InMemoryGrammarResources:
		res = self.underlyingCollection.get(k, None)
		if res is None:
			self[k] = res = InMemoryGrammarResources(k)

		return res

	def __setitem__(self, k: str, v: InMemoryGrammarResources) -> None:
		if v.parent is not self.parent:
			if v.parent is not None:
				warn("Changing parent. Resources are not moved automatically")
			v.parent = self.parent
		self.underlyingCollection[k] = v

	def __getattr__(self, k: str) -> typing.Callable:
		return getattr(self.underlyingCollection, k)


parseBundleCompiledKeyMapper = PrefixKeyMapper("compiled")
parseBundleCompiledParentDir = Dynamic(("bundleDir",))
compiledMapperColdSaver = FileSaver(parseBundleCompiledParentDir, None)


class ParserBundle(ProtoBundle):
	"""A class to manage components of a parser"""

	__slots__ = ("backends", "grammars", "bundleDir")

	serializer = utf8Transformer + jsonFancySerializer

	backendsBinaryData = FieldND(ColdMapper(parseBundleCompiledKeyMapper, compiledMapperColdSaver, JustReturnSerializerMapper(dummyTransformer)))
	backendsTextData = FieldND(ColdMapper(parseBundleCompiledKeyMapper, compiledMapperColdSaver, JustReturnSerializerMapper(utf8Transformer)))
	backendsPythonAST = FieldND(ColdMapper(parseBundleCompiledKeyMapper, FileSaver(parseBundleCompiledParentDir, "py"), pythonASTSerializerMapper))

	def __init__(self, path: typing.Optional[Path] = None) -> None:
		self.bundleDir = path
		self.initBackends()
		self.grammars = GrammarsCollection(self)

	def initBackends(self):
		self.backends = {b.PARSER.META.product.name: b for b in self.discoverBackends()}

	def discoverBackends(self) -> None:
		"""Used to discover backends for which parsers are present in a bundle"""
		for name in self._discoverBackends():
			if name in backendsRegistry:
				yield backendsRegistry[name]
			else:
				warn("Backend " + name + " is not in the registry, skipping")

	def _discoverBackends(self) -> None:
		"""Upstream stuff to discover backends. Must return backends names present in a bundle"""
		backendsDataDir = self.bundleDir / "compiled"
		if backendsDataDir.is_dir():
			for p in backendsDataDir.iterdir():
				if p.is_dir() and p.name[0] != "_":
					yield p.name

	def save(self, propName: typing.Optional[str] = None) -> None:
		self.bundleDir.mkdir(parents=True, exist_ok=True)
		for el in self.grammars.values():
			el.save()
		super().save(propName)
