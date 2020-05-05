import typing
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser

from ...DSLMetadata import DSLMetadata
from ...grammarClasses import GLR, LR
from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend, ToolSpecificGrammarASTWalkStrategy
from ...ToolMetadata import Product, ToolMetadata

thisDir = Path(__file__).parent

toolGitRepo = "https://github.com/igordejanovic/parglare"


class ParglareParser(IParser):
	NAME = "parglare"

	__slots__ = ("parser",)

	def __init__(self, parser: "parglare.parser.Parser") -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s)


class ParglareParserFactory(IParserFactoryFromSource):
	__slots__ = ()
	parglare = None
	PARSER_CLASS = ParglareParser
	FORMAT = DSLMetadata(
		officialLibraryRepo=toolGitRepo + "/tree/master/examples",
		grammarExtensions=("pg", "pgt"),
	)

	META = ToolMetadata(
		Product(
			name="parglare",
			website=toolGitRepo,
		),
		runtimeLib={
			"python": toolGitRepo,
		},
		grammarClasses=(LR, GLR),
		buildsTree=True,
	)

	@classmethod
	def ensureInitialized(cls):
		if cls.parglare is None:
			import parglare  # pylint:disable=import-outside-toplevel,redefined-outer-name

			cls.parglare = parglare

	def __init__(self) -> None:
		super().__init__()

	def compileStr(self, grammarText: str, target: str = None, fileName: Path = None) -> "parglare.parser.Parser":
		return self.__class__.parglare.Parser(self.__class__.parglare.Grammar.from_string(grammarText), ws="", debug=False)

	def compileFile(self, grammarFile: Path, target: str = None):
		return self.__class__.parglare.Parser(self.__class__.parglare.Grammar.from_file(grammarFile), ws="", debug=False)

	def fromInternal(self, internalRepr: str, target: str = None) -> typing.Any:
		return self.__class__.PARSER_CLASS(self.compileStr(internalRepr, target))


class ParglareParserBackendWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		if node is not None:
			for elName in node._pg_attrs:
				yield getattr(node, elName, None)

	def isTerminal(self, node: str) -> bool:
		return isinstance(node, str)

	def iterateCollection(self, lst: typing.Any) -> typing.List[typing.Any]:
		return lst

	def isCollection(self, lst: typing.Any) -> bool:
		return isinstance(lst, list)


class ParglareParsingBackend(IParsingBackend):
	__slots__ = ()
	EX_CLASS = None
	PARSER = ParglareParserFactory
	WSTR = ParglareParserBackendWalkStrategy

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		super().__init__(grammarResources)
		if self.__class__.EX_CLASS is None:
			self.__class__.EX_CLASS = self.__class__.PARSER.parglare.exceptions.ParseError

	def terminalNodeToStr(self, token: typing.Optional[typing.Any]) -> typing.Optional[typing.Any]:
		return token
