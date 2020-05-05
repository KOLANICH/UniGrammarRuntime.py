import typing

from ...grammarClasses import LL
from ...IParsingBackend import IParsingBackend, ToolSpecificGrammarASTWalkStrategy
from ...ToolMetadata import Product, ToolMetadata

antlr4 = None

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
			website=toolRepoBase,
		),
		runtimeLib={
			lang: (toolRuntimesBase + "/" + antlrLang) for lang, antlrLang in languagesRemap.items()
		},
		grammarClasses=(LL,),
		buildsTree=True,
	)

	def _bundleToIterable(self, backend, grammarResources: "InMemoryGrammarResources") -> typing.Iterable[typing.Any]:
		return backend._somethingToIterable(grammarResources, lambda grammarResources, role, className: grammarResources.parent.backendsPythonAST[self.__class__.PARSER_CLASS.NAME, className])

	def fromBundle(self, grammarResources: "InMemoryGrammarResources") -> "antlrCompile.core.ANTLRParser":
		global antlr4
		pythonBackend = backendsPool(ANTLRInternalClassesPython)
		antlr4 = pythonBackend.antlr4
		return self._fromAttrIterable(pythonBackend, self._bundleToIterable(pythonBackend, grammarResources))


class ANTLRWalkStrategy(ToolSpecificGrammarASTWalkStrategy):
	__slots__ = ()

	def iterateChildren(self, node):
		return node.children

	def isTerminal(self, node: "antlr4.tree.Tree.TerminalNodeImpl") -> bool:
		return isinstance(node, (str, self.parserFactory.antlr4.tree.Tree.TerminalNode, self.parserFactory.antlr4.Token))

	def iterateCollection(self, lst: "antlr4.ParserRuleContext.ParserRuleContext") -> typing.Any:
		if lst:
			if lst.children:
				return lst.children

		return ()

	def isCollection(self, lst: typing.Any) -> bool:
		return isinstance(lst, self.parserFactory.antlr4.RuleContext)


class ANTLRParsingBackend(IParsingBackend):
	__slots__ = ()
	PARSER = ANTLRParserFactory
	WSTR = ANTLRWalkStrategy

	def terminalNodeToStr(self, token: typing.Union["antlr4.Token.CommonToken", "antlr4.tree.Tree.TerminalNodeImpl"]) -> typing.Optional[str]:
		if token is not None:
			if isinstance(token, str):
				return token
			if isinstance(token, antlr4.Token):
				return token.text
			return token.getText()
		return None
