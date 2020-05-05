import typing

from ...grammarClasses import LL
from ...IParsingBackend import IParsingBackend, ToolSpecificGrammarASTWalkStrategy
from ...ToolMetadata import Product, ToolMetadata

try:
	from antlrCompile.backends.python import ANTLRInternalClassesPython
	from antlrCompile.core import ANTLRParserFactory as ANTLRCompileANTLRParserFactory
	from antlrCompile.core import backendsPool
except ImportError:
	from warnings import warn

	antlrCompileNotInstalledErrorMessage = "antlrCompile is not installed, generation of ANTLR bundles and visualization of results is not available"
	warn(antlrCompileNotInstalledErrorMessage)

	class ANTLRDummy:
		__slots__ = ()

		def compileStr(self, *args, **kwargs):
			raise NotImplementedError(antlrCompileNotInstalledErrorMessage)

	class ANTLRCompileDummy:
		__slots__ = ()

		def __init__(self, *args, **kwargs):
			raise NotImplementedError(antlrCompileNotInstalledErrorMessage)

	ANTLR = ANTLRDummy
	ANTLRCompileVis = ANTLRCompileDummy
	ANTLRCompileANTLRParserFactory = ANTLRCompileDummy
	ANTLRInternalClassesPython = ANTLRCompileDummy


toolGithubOrg = "https://github.com/antlr"
toolRepoBase = toolGithubOrg + "/antlr4"
toolRuntimesBase = toolRepoBase + "/tree/master/runtime"

languagesRemap = {
	"python": "Python3",
	"js": "JavaScript",
	"java": "Java",
	"go": "Go",
	"c++": "Cpp",
	"c#": "CSharp",
	"swift": "Swift",
}


class ANTLRParserFactory(ANTLRCompileANTLRParserFactory):
	__slots__ = ()

	META = ToolMetadata(
		Product(
			name="antlr4",
			#website=toolRepoBase,
			website="https://codeberg.org/UniGrammar/antlr4", # temporarily till our changes are merged
		),
		runtimeLib={
			lang: (toolRuntimesBase + "/" + antlrLang) for lang, antlrLang in languagesRemap.items()
		},
		grammarClasses=(LL,),
		buildsTree=True,
	)

	def _bundleToIterable(self, backend, grammarResources: "InMemoryGrammarResources") -> typing.Iterable[typing.Any]:
		return backend._somethingToIterable(grammarResources, lambda grammarResources, role, className: grammarResources.parent.backendsPythonAST[self.__class__.PARSER_CLASS.NAME, className])

	antlr4 = None

	def fromBundle(self, grammarResources: "InMemoryGrammarResources") -> "antlrCompile.core.ANTLRParser":
		pythonBackend = backendsPool(ANTLRInternalClassesPython)
		self.__class__.antlr4 = pythonBackend.antlr4
		return self._fromAttrIterable(pythonBackend, self._bundleToIterable(pythonBackend, grammarResources))


class ANTLRWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		return node.children

	def isTerminal(self, node: "antlr4.tree.Tree.TerminalNodeImpl") -> bool:
		return isinstance(node, (str, self.parserFactory.PARSER.antlr4.tree.Tree.TerminalNode, self.parserFactory.PARSER.antlr4.Token))

	def iterateCollection(self, lst: "antlr4.ParserRuleContext.ParserRuleContext") -> typing.Any:
		if lst:
			if lst.children:
				return lst.children

		return ()

	def isCollection(self, lst: typing.Any) -> bool:
		return isinstance(lst, self.parserFactory.PARSER.antlr4.RuleContext)

	def isOptionalPresent(self, optional) -> bool:
		return optional is not None and optional.children

	def getOptional(self, optional) -> typing.Any:
		assert len(optional.children) == 1
		return optional.children[0]


class ANTLRParsingBackend(IParsingBackend):
	__slots__ = ()
	PARSER = ANTLRParserFactory
	WSTR = ANTLRWalkStrategy

	def terminalNodeToStr(self, token: typing.Union["antlr4.Token.CommonToken", "antlr4.tree.Tree.TerminalNodeImpl"]) -> typing.Optional[str]:
		if token is not None:
			if isinstance(token, str):
				return token
			if isinstance(token, self.__class__.PARSER.antlr4.Token):
				return token.text
			return token.getText()
		return None
