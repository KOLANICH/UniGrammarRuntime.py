import typing
from collections import OrderedDict
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser

from ...DSLMetadata import DSLMetadata
from ...grammarClasses import PEG
from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend, ToolSpecificGrammarASTWalkStrategy
from ...ToolMetadata import Product, ToolMetadata
from ...utils import ListLikeDict, ListNodesMixin, NodeWithAttrChildrenMixin

lark = None
NodeWithAttrChildren = None
ListNodes = None


toolGitRepo = "https://github.com/coquelicot/PyDSL"
masterBranchURI = toolGitRepo + "/tree/master"


class PyDSLParser(IParser):
	NAME = "PyDSL"

	__slots__ = ("parser", "lexer")

	def __init__(self, parser) -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s)


class PyDSLParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	PARSER_CLASS = PyDSLParser
	META = ToolMetadata(
		Product(
			name="PyDSL",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": srcURI,
		},
		grammarClasses=(None,),
		buildsTree=True,
	)

	def __init__(self) -> None:
		global DSL
		if DSL is None:
			import DSL  # pylint:disable=import-outside-toplevel,redefined-outer-name

		super().__init__()

	def compileStr(self, grammarText: str, target=None, fileName: Path = None):
		return DSL.makeDSL(grammarText)

	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))


class PyDSLParserBackendWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		raise NotImplementedError

	def isTerminal(self, node):
		raise NotImplementedError

	def iterateCollection(self, lst) -> typing.Any:
		raise NotImplementedError

	def isCollection(self, lst: typing.Any) -> bool:
		raise NotImplementedError


class PyDSLParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema")
	ITER_INTROSPECTION = True
	CAP_INTROSPECTION = True
	PARSER = PyDSLParserFactory
	WSTR = PyDSLParserBackendWalkStrategy

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		global NodeWithAttrChildren, ListNodes

		super().__init__(grammarResources)

	def terminalNodeToStr(self, token) -> typing.Optional[str]:
		raise NotImplementedError

	def getSubTreeText(self, node) -> str:
		"""Merges a tree of text tokens into a single string"""
		raise NotImplementedError
