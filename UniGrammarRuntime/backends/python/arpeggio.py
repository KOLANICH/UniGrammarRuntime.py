import typing
from collections import OrderedDict
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser

from ...DSLMetadata import DSLMetadata
from ...grammarClasses import PEG
from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend, ToolSpecificGrammarASTWalkStrategy
from ...ToolMetadata import Product, ToolMetadata
from ...utils import AttrDict, flattenDictsIntoIterable


class ArpeggioParser(IParser):
	__slots__ = ("parser",)

	def __init__(self, parser) -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s)


toolGitRepo = "https://github.com/textX/Arpeggio"


class ArpeggioParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	PARSER_CLASS = ArpeggioParser
	FORMAT = DSLMetadata(
		officialLibraryRepo=toolGitRepo + "/tree/master/examples",
		grammarExtensions=("peg",)
	)

	META = ToolMetadata(
		Product(
			name="arpeggio",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": toolGitRepo,
		},
		grammarClasses=(PEG,),
		buildsTree=None,
	)

	arpeggio = None

	@classmethod
	def ensureInitialized(cls):
		# pylint:disable=import-outside-toplevel,redefined-outer-name
		if cls.arpeggio is None:
			import arpeggio
			import arpeggio.peg

			cls.arpeggio = arpeggio

	@classmethod
	def getFirstRuleName(cls, grammarSrc: str) -> str:
		parser = cls.arpeggio.ParserPython(cls.arpeggio.peg.peggrammar, cls.arpeggio.peg.comment, reduce_tree=False)
		parsedAST = parser.parse(grammarSrc)
		for el in parsedAST:
			if el.rule_name == "rule":
				if el[0].rule_name == "rule_name":
					return el[0].flat_str()

	def compileStr(self, grammarText: str, target=None, fileName: Path = None):
		firstRuleName = self.__class__.getFirstRuleName(grammarText)
		return self.__class__.arpeggio.peg.ParserPEG(grammarText, firstRuleName, skipws=False, debug=False)

	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))


TransformedASTElT = typing.Union["arpeggio.Terminal", "TransformedASTT"]
TransformedASTT = typing.Mapping[str, TransformedASTElT]


class ArpeggioParserBackendWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		yield from lst

	def isTerminal(self, node):
		return isinstance(node, str)

	def iterateCollection(self, lst) -> typing.Any:
		yield from lst

	def isCollection(self, lst) -> bool:
		return isinstance(lst, ListNodes)


class ArpeggioParsingBackend(IParsingBackend):
	__slots__ = ("parser", "capSchema", "iterSchema")
	ITER_INTROSPECTION = False
	CAP_INTROSPECTION = False
	PARSER = ArpeggioParserFactory
	WSTR = ArpeggioParserBackendWalkStrategy

	@classmethod
	def _transformArpeggioAST(cls, node, capSchema: typing.Dict[str, typing.Dict[str, str]], iterSchema: typing.List[str]) -> TransformedASTElT:
		if node.rule_name not in iterSchema:
			newChildren = AttrDict()
			thisElMapping = None
			if node.rule_name in capSchema:
				thisElMapping = capSchema[node.rule_name]

			if not isinstance(node, cls.PARSER.arpeggio.Terminal):
				for i, child in enumerate(node):
					nameToUse = str(i)  # we cannot use just ints as keys for ListLikeDict because it also supports positional indexing
					if not isinstance(child, str):
						childProdName = child.rule_name
						newChild = cls._transformArpeggioAST(child, capSchema, iterSchema)
						if thisElMapping:
							if childProdName in thisElMapping:
								nameToUse = thisElMapping[childProdName]  # recovered name

						if isinstance(nameToUse, int):
							# we have to insert something, and in this case it's better to have prod name than just number
							nameToUse = childProdName
					else:
						newChild = child
					newChildren[nameToUse] = newChild
				return newChildren
			return node.flat_str()
		else:
			return [cls._transformArpeggioAST(child, capSchema, iterSchema) for child in node]

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		super().__init__(grammarResources)
		self.capSchema = grammarResources.capSchema
		self.iterSchema = grammarResources.iterSchema

		self.__class__.PARSER.ensureInitialized()

	def preprocessAST(self, ast):
		return self.__class__._transformArpeggioAST(ast, self.capSchema, self.iterSchema)

	def terminalNodeToStr(self, token) -> typing.Optional[str]:
		return "".join(flattenDictsIntoIterable(node))

	def getSubTreeText(self, node) -> str:
		"""Merges a tree of text tokens into a single string"""
		return "".join(flattenDictsIntoIterable(node))
