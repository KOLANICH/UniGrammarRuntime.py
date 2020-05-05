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

parsimonious = None
NodeWithAttrChildren = None
ListNodes = None


toolGitRepo = "https://github.com/erikrose/parsimonious"


class ParsimoniousParser(IParser):
	__slots__ = ("parser",)

	def __init__(self, parser: "parsimonious.grammar.Grammar") -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str) -> "parsimonious.nodes.Node":
		return self.parser.parse(s)


class ParsimoniousParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	PARSER_CLASS = ParsimoniousParser

	FORMAT = DSLMetadata(
		officialLibraryRepo=None,
		grammarExtensions=["ppeg"]
	)

	META = ToolMetadata(
		Product(
			name="parsimonious",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": toolGitRepo,
		},
		grammarClasses=(PEG,),
		buildsTree=None,
	)

	parsimonious = None

	@classmethod
	def ensureInitialized(cls):
		if cls.parsimonious is None:
			import parsimonious  # pylint:disable=import-outside-toplevel,redefined-outer-name

			cls.parsimonious = parsimonious

	def compileStr(self, grammarText: str, target=None, fileName: Path = None) -> "parsimonious.grammar.Grammar":
		return self.__class__.parsimonious.Grammar(grammarText)

	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))


def _transformParsimoniousAST(node: typing.Union["parsimonious.nodes.Node", "parsimonious.nodes.RegexNode"], capSchema: typing.Dict[str, typing.Dict[str, str]]) -> None:
	"""Walks parsimonious AST to make it more friendly for our processing:
		1. Replaces lists of children with `ListLikeDict`s, using `expr_name`s as keys
		2. Adds `__getattr__` to the nodes looking up attrs in the dicts of children

		All of this is needed because our postprocessing is attr-based.
	"""

	if not isinstance(node, ParsimoniousParserFactory.parsimonious.nodes.RegexNode):
		if not isinstance(node.expr, ParsimoniousParserFactory.parsimonious.expressions.Quantifier): # or (node.expr.min==0 and node.expr.max==1): # in pats it handled only ZeroOrMore and OneOrMore, but when P. has abstracted a bit, they have become a Quantifier, and so become Optional, was it a mistake not to handle it here too?
			newChildren = OrderedDict()
			for child in node.children:
				childProdName = child.expr_name
				_transformParsimoniousAST(child, capSchema)
				nameToUse = None
				if node.expr_name in capSchema:
					thisElMapping = capSchema[node.expr_name]

					if childProdName in thisElMapping:
						nameToUse = thisElMapping[childProdName]  # recovered name

				if nameToUse is None:
					# we have to insert something
					nameToUse = childProdName
				newChildren[nameToUse] = child
			node.children = ListLikeDict(newChildren)
			node.__class__ = NodeWithAttrChildren
		else:
			for child in node.children:
				_transformParsimoniousAST(child, capSchema)
			node.__class__ = ListNodes


class ParsimoniousParserBackendWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		return node.children

	def isTerminal(self, node):
		return isinstance(node, self.parserFactory.parsimonious.nodes.RegexNode)

	def iterateCollection(self, lst) -> typing.Any:
		return lst.children

	def isCollection(self, lst: typing.Any) -> bool:
		return isinstance(lst.expr, (self.parserFactory.parsimonious.expressions.ZeroOrMore, self.parserFactory.parsimonious.expressions.OneOrMore))


class ParsimoniousParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema")
	ITER_INTROSPECTION = True
	CAP_INTROSPECTION = False
	PARSER = ParsimoniousParserFactory
	WSTR = ParsimoniousParserBackendWalkStrategy

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		global NodeWithAttrChildren, ListNodes

		super().__init__(grammarResources)
		self.capSchema = grammarResources.capSchema

		if NodeWithAttrChildren is None:

			class NodeWithAttrChildren(self.__class__.PARSER.parsimonious.nodes.Node, NodeWithAttrChildrenMixin):  # pylint:disable=redefined-outer-name
				__slots__ = ()

			class ListNodes(self.__class__.PARSER.parsimonious.nodes.Node, ListNodesMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()

	def preprocessAST(self, ast):
		_transformParsimoniousAST(ast, self.capSchema)
		return ast

	def terminalNodeToStr(self, token: "parsimonious.nodes.RegexNode") -> typing.Optional[str]:
		return token.text

	def getSubTreeText(self, node: "parsimonious.nodes.Node") -> str:
		"""Merges a tree of text tokens into a single string"""
		return node.text
