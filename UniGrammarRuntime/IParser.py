import typing
from abc import abstractmethod, ABCMeta
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser
from UniGrammarRuntimeCore.IParser import IParserFactory as IParserFactoryCore
from UniGrammarRuntimeCore.IParser import IParserFactoryFromPrecompiled as IParserFactoryFromPrecompiledCore
from UniGrammarRuntimeCore.IParser import IParserFactoryFromSource as IParserFactoryFromSourceCore

from .FormatMetadata import FormatMetadata
from .ToolMetadata import Product

# pylint:disable=too-few-public-methods


class IParserFactoryMeta(ABCMeta):
	__slots__ = ()

	def __new__(cls: typing.Type["IParserFactoryCore"], className: str, parents: typing.Tuple[typing.Type, ...], attrs: typing.Dict[str, typing.Any]) -> "Tool":  # pylint:disable=arguments-differ
		
		FORMAT = attrs.get("FORMAT", None)
		META = attrs.get("META", None)
		if FORMAT is not None and META is not None:
			if FORMAT.product is None:
				FORMAT.product = META.product

		return super().__new__(cls, className, parents, attrs)


class IParserFactory(IParserFactoryCore, metaclass=IParserFactoryMeta):
	__slots__ = ()

	FORMAT = None  # type: FormatMetadata

	@abstractmethod
	def fromBundle(self, grammarResources: "InMemoryGrammarResources"):
		"""Creates an executor from the files within bundle"""
		raise NotImplementedError


class IParserFactoryFromSource(IParserFactoryFromSourceCore, metaclass=IParserFactoryMeta):  # pylint:disable=abstract-method
	__slots__ = ()

	FORMAT = None  # type: FormatMetadata

	def fromBundle(self, grammarResources: "InMemoryGrammarResources") -> IParser:
		return self.fromInternal(self.getSource(grammarResources))  # since they cannot be precompiled, for them internal repr is source text

	@classmethod
	def _getExt(cls):
		if cls.FORMAT is not None:
			return cls.FORMAT.mainExtension
		else:
			return cls.META.product.name

	def getSource(self, grammarResources: "InMemoryGrammarResources") -> str:
		"""Must return source code of the grammar in its DSL"""
		return grammarResources.parent.backendsTextData[self.__class__.META.product.name, grammarResources.name + "." + self.__class__._getExt()]


class IParserFactoryFromPrecompiled(IParserFactoryFromPrecompiledCore):  # pylint:disable=abstract-method
	__slots__ = ()

	FORMAT = FormatMetadata(
		grammarExtensions=("py",),
		product=Product(
			name="python",
			website="https://docs.python.org/3/tutorial/index.html",
		),
	)

	def fromBundle(self, grammarResources: "InMemoryGrammarResources") -> IParser:
		ctor = self.compile(self.getSource(grammarResources), grammarResources.name)
		return self.fromInternal(ctor())

	def getSource(self, grammarResources: "InMemoryGrammarResources") -> "ast.Module":
		"""Must return source code of the grammar in its DSL"""
		return grammarResources.parent.backendsPythonAST[self.__class__.META.product.name, grammarResources.name]


class IParserFactoryFromPrecompiledOrSource(IParserFactoryFromSourceCore):
	"""Hybrid between `IParserFromPrecompiled` and `IParserFromSource`:
		tries to find and use precompiled file first,
		if there is no, tries to find and use source
	"""

	PRECOMPILED = None
	SOURCE = None

	__slots__ = ("_precompiled", "_source")

	def __init__(self):
		self._precompiled = None
		self._source = None
		super().__init__()

	@property
	def precompiled(self) -> IParserFactoryFromPrecompiled:
		res = self._precompiled
		if res is None:
			self._precompiled = res = self.__class__.PRECOMPILED()
		return res

	@property
	def source(self) -> IParserFactoryFromSource:
		res = self._source
		if res is None:
			self._source = res = self.__class__.SOURCE()
		return res

	def fromBundle(self, grammarResources: "InMemoryGrammarResources"):
		"""tries to find and use precompiled file first,
		if there is no, tries to find and use source"""
		try:
			return self.precompiled.fromBundle(grammarResources)
		except FileNotFoundError:
			return self.source.fromBundle(grammarResources)

	def compileStr(self, grammarText: str, target: typing.Any = None, fileName: typing.Optional[typing.Union[Path, str]] = None):
		"""Proxies to the factory defined by `SOURCE`"""
		return self.source.compileStr(grammarText, target, fileName)

	def compileFile(self, grammarFile: Path, target: typing.Any = None):
		"""Proxies to the factory defined by `SOURCE`"""
		return self.source.compileFile(grammarFile, target)
