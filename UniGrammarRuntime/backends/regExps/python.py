import re
import typing
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser

from ...DSLMetadata import DSLMetadata
from ...grammarClasses import RegExp
from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend, ToolSpecificGrammarASTWalkStrategy
from ...ToolMetadata import Product, ToolMetadata

thisDir = Path(__file__).parent

parglare = None


toolGitRepo = "https://github.com/python/cpython"


class PythonRegExpParser(IParser):
	NAME = "python_re"

	__slots__ = ("parser",)

	def __init__(self, parser: "_sre.SRE_Pattern") -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.exec(s)


class PythonRegExpParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	PARSER_CLASS = PythonRegExpParser
	FORMAT = DSLMetadata(
		grammarExtensions=(),
	)

	META = ToolMetadata(
		Product(
			name="py_re",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": toolGitRepo,
		},
		grammarClasses=(RegExp),
		buildsTree=True,
	)

	def compileStr(self, grammarText: str, target: str = None, fileName: Path = None) -> "_sre.SRE_Pattern":
		return re.compile(grammarText)

	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))


class PythonRegExpParserBackendWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		raise NotImplementedError

	def isTerminal(self, node):
		raise NotImplementedError

	def iterateCollection(self, lst) -> typing.Any:
		raise NotImplementedError

	def isCollection(self, lst: typing.Any) -> bool:
		raise NotImplementedError


# copied from parglare, not yet implemented
class PythonRegExpParsingBackend(IParsingBackend):
	__slots__ = ()
	EX_CLASS = None
	PARSER = PythonRegExpParserFactory
	WSTR = PythonRegExpParserBackendWalkStrategy

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		super().__init__(grammarResources)
		raise NotImplementedError

	def terminalNodeToStr(self, token: typing.Optional[typing.Any]) -> typing.Optional[typing.Any]:
		raise NotImplementedError
		#return token
