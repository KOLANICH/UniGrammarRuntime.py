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


toolGitRepo = "https://github.com/lark-parser/lark"
masterBranchURI = toolGitRepo + "/tree/master"
srcURI = masterBranchURI + "/src"


class LarkParser(IParser):
	NAME = "lark"
	#EXT = "lark"

	__slots__ = ("parser",)

	def __init__(self, parser) -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s)


class LarkParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	PARSER_CLASS = LarkParser
	META = ToolMetadata(
		Product(
			name="lark",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": srcURI,
		},
		grammarClasses=(PEG,),
		buildsTree=True,
	)

	def __init__(self) -> None:
		global lark

		if lark is None:
			import lark  # pylint:disable=import-outside-toplevel,redefined-outer-name

		super().__init__()

	def compileStr(self, grammarText: str, target=None, fileName: Path = None):
		return lark.Lark(grammarText, parser="lalr", lexer="auto")

	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))


class LarkParserBackendWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		raise NotImplementedError

	def isTerminal(self, node):
		raise NotImplementedError

	def iterateCollection(self, lst) -> typing.Any:
		raise NotImplementedError

	def isCollection(self, lst: typing.Any) -> bool:
		raise NotImplementedError


class LarkParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema")
	ITER_INTROSPECTION = True
	CAP_INTROSPECTION = True
	PARSER = LarkParserFactory
	WSTR = LarkParserBackendWalkStrategy

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		global NodeWithAttrChildren, ListNodes

		super().__init__(grammarResources)

	def terminalNodeToStr(self, token: "lark.nodes.RegexNode") -> typing.Optional[str]:
		raise NotImplementedError

	def getSubTreeText(self, node: "lark.nodes.Node") -> str:
		"""Merges a tree of text tokens into a single string"""
		raise NotImplementedError
