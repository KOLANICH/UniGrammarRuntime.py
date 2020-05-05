import typing
from collections import OrderedDict

from UniGrammarRuntimeCore.IParser import IParser

from ...grammarClasses import PEG
from ...IParser import IParserFactoryFromPrecompiled
from ...IParsingBackend import IParsingBackend, ToolSpecificGrammarASTWalkStrategy
from ...ToolMetadata import Product, ToolMetadata
from ...utils import ListLikeDict, ListNodesMixin, NodeWithAttrChildrenMixin, TerminalNodeMixin

waxeye = None


toolGitRepo = "https://github.com/waxeye-org/waxeye"
masterBranchURI = toolGitRepo + "/tree/master"
srcURI = masterBranchURI + "/src"


def decapitalizeFirst(s: str) -> str:
	return "".join((s[0].lower(), s[1:]))


def capitalizeFirst(s: str) -> str:
	return "".join((s[0].upper(), s[1:]))


class WaxeyeParser(IParser):
	NAME = "waxeye"

	__slots__ = ("parser",)

	def __init__(self, parser):
		super().__init__()
		self.parser = parser

	def __call__(self, s: str) -> "waxeye.AST":
		print("self.parser", self.parser)
		return self.parser.parse(s)


class WaxeyeParserFactory(IParserFactoryFromPrecompiled):
	__slots__ = ()
	PARSER_CLASS = WaxeyeParser
	META = ToolMetadata(
		Product(
			name="waxeye",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": srcURI + "/python",
			"js": srcURI + "/javascript",
			"java": srcURI + "/java",
			"c++": srcURI + "/c",
			"racket": srcURI + "/racket",
			"ruby": srcURI + "/ruby",
			"sml": srcURI + "/sml",
		},
		grammarClasses=(PEG,),
		buildsTree=True,
	)

	NodeWithAttrChildren = None
	ListNodes = None
	TerminalNode = None

	def processEvaledGlobals(self, globalz: dict, grammarName: str):
		return globalz[grammarName.capitalize() + "Parser"]

	def getSource(self, grammarResources: "InMemoryGrammarResources") -> "ast.Module":
		return grammarResources.parent.backendsPythonAST[self.__class__.META.product.name, grammarResources.name + "_parser"]

	def __init__(self) -> None:
		global waxeye
		if waxeye is None:
			import waxeye  # pylint:disable=import-outside-toplevel,redefined-outer-name

			class NodeWithAttrChildren(waxeye.AST, NodeWithAttrChildrenMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()
			self.__class__.NodeWithAttrChildren = NodeWithAttrChildren

			class ListNodes(waxeye.AST, ListNodesMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()
			self.__class__.ListNodes = ListNodes

			class TerminalNode(waxeye.AST, TerminalNodeMixin):  # pylint:disable=redefined-outer-name,unused-variable
				__slots__ = ()
			self.__class__.TerminalNode = TerminalNode

		super().__init__()


class WaxeyeParserBackendWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		return node.children

	def isTerminal(self, node):
		return isinstance(node, (str, WaxeyeParserFactory.TerminalNode))

	def iterateCollection(self, lst):
		return lst

	def isCollection(self, lst: typing.Union["waxeye.AST", str]) -> bool:
		return isinstance(lst, WaxeyeParserFactory.ListNodes)


class WaxeyeParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema", "iterSchema")

	PARSER = WaxeyeParserFactory
	WSTR = WaxeyeParserBackendWalkStrategy
	ITER_INTROSPECTION = False
	CAP_INTROSPECTION = False

	#EX_CLASS = waxeye.ParseError # not an Exception

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		super().__init__(grammarResources)

		self.capSchema = grammarResources.capSchema  # type: typing.Dict[str, typing.Dict[str, str]]
		self.iterSchema = grammarResources.iterSchema  # type: typing.List[str]

	def _transformWaxeyeAST(self, node: "waxeye.AST") -> None:
		"""
		Fucking waxeye decapitalizes all the identifiers, destroying uniformity between backends. So we have 2 lookups instead of one. It is definitely a bug in waxeye.
		"""
		capitalizedType = capitalizeFirst(node.type)

		if node.type not in self.iterSchema and capitalizedType not in self.iterSchema:
			newChildren = OrderedDict()
			thisElMapping = None
			if node.type in self.capSchema:
				thisElMapping = self.capSchema[node.type]
			elif capitalizedType in self.capSchema:
				thisElMapping = self.capSchema[capitalizedType]

			for i, child in enumerate(node.children):
				nameToUse = str(i)  # we cannot use just ints as keys for ListLikeDict because it also supports positional indexing
				if not isinstance(child, str):
					childProdName = child.type
					self._transformWaxeyeAST(child)
					if thisElMapping:
						childProdNameCapitalized = capitalizeFirst(childProdName)

						if childProdName in thisElMapping:
							nameToUse = thisElMapping[childProdName]  # recovered name
						elif childProdNameCapitalized in thisElMapping:
							nameToUse = thisElMapping[childProdNameCapitalized]  # recovered name

					if isinstance(nameToUse, int):
						# we have to insert something, and in this case it's better to have prod name than just number
						nameToUse = childProdName
				newChildren[nameToUse] = child
			node.children = ListLikeDict(newChildren)

			if len(node.children) == 1 and isinstance(node.children[0], str):
				node.__class__ = self.__class__.PARSER.TerminalNode
			else:
				node.__class__ = self.__class__.PARSER.NodeWithAttrChildren
		else:
			for child in node.children:
				self._transformWaxeyeAST(child)
			node.__class__ = self.__class__.PARSER.ListNodes

	def parse(self, s: str) -> "waxeye.AST":
		import waxeye

		res = self.parser(s)
		if isinstance(res, waxeye.ParseError):
			raise ValueError(res)

		return res

	def preprocessAST(self, ast):
		self._transformWaxeyeAST(ast)
		return ast

	def terminalNodeToStr(self, token: typing.Union[str, "waxeye.AST"]) -> str:
		return str(token)
