import typing
from abc import ABCMeta, abstractmethod

backendsRegistry = {}


class ParserNotFoundException(Exception):
	"""Means that not all parser components have been found"""


class IParsingBackendMeta(ABCMeta):
	__slots__ = ()

	def __new__(cls: typing.Type["TemplateMeta"], className: str, parents: typing.Tuple[typing.Type, ...], attrs: typing.Dict[str, typing.Any]) -> "Template":  # pylint:disable=arguments-differ
		res = super().__new__(cls, className, parents, attrs)

		parserFactoryClass = attrs.get("PARSER", None)
		if parserFactoryClass is not None:
			parserClass = getattr(parserFactoryClass, "PARSER_CLASS", None)
			if parserClass is not None and parserFactoryClass.META is not None:
				backendsRegistry[parserFactoryClass.META.product.name] = res

		return res


class ToolSpecificGrammarASTWalkStrategy:
	"""Very generic methods to walk either
		* ASTs of tool-specific grammars themselves;
		* ASTs **parsed using tool-specific grammars.

	They are in the same class because often tools have similar interfaces for them. Very often the nodes of tools grammars are parsed with the tools themselves.
	"""

	__slots__ = ("parserFactory",)

	def __init__(self, parserFactory):
		self.parserFactory = parserFactory

	def iterateChildren(self, node):
		"""Gets an iterable of children nodes of tool-specific AST node"""
		raise NotImplementedError

	def isTerminal(self, node):
		"""Returns if a node is a terminal that should not be further iterated"""
		raise NotImplementedError

	def iterateCollection(self, lst) -> typing.Any:
		"""Gets an iterable of children nodes of tool-specific AST node"""
		raise NotImplementedError

	def isCollection(self, lst: typing.Any) -> bool:
		"""Gets an iterable of children nodes of tool-specific collection AST node"""
		raise NotImplementedError

	def enterOptional(self, optional: typing.Any, childProcessor) -> bool:
		"""Gets an iterable of children nodes of tool-specific collection AST node"""
		raise NotImplementedError

	def isOptionalPresent(self, optional) -> bool:
		return optional is not None

	def getOptional(self, optional) -> typing.Any:
		return optional


class IParsingBackend(metaclass=IParsingBackendMeta):
	"""A class commanding the parsing. Calls the generated parser and postprocesses its output"""

	__slots__ = ("parser", "wstr")

	PARSER = None
	WSTR = None  # type: typing.Type[ToolSpecificGrammarASTWalkStrategy]

	@property
	@classmethod
	def NAME(cls):
		return cls.PARSER.NAME

	EX_CLASS = Exception
	ITER_INTROSPECTION = True
	CAP_INTROSPECTION = True

	def __init__(self, grammarResources: "InMemoryGrammarResources") -> None:
		self.parser = self.__class__.PARSER().fromBundle(grammarResources)
		self.wstr = self.__class__.WSTR(self.__class__)

	def _getSubTreeText(self, lst: typing.Any) -> typing.Iterator[str]:
		if self.wstr.isCollection(lst):
			for t in self.wstr.iterateCollection(lst):
				yield from self._getSubTreeText(t)
		elif self.wstr.isTerminal(lst):
			yield self.terminalNodeToStr(lst)
		else:
			for t in self.wstr.iterateChildren(lst):
				yield from self._getSubTreeText(t)

	def enterOptional(self, optional: typing.Any, childProcessor) -> bool:
		"""Gets an iterable of children nodes of tool-specific collection AST node"""
		if self.wstr.isOptionalPresent(optional):
			return childProcessor(self.wstr.getOptional(optional))

		return None

	def getSubTreeText(self, node: typing.Any) -> str:
		"""Merges a tree of text tokens into a single string"""
		return "".join(self._getSubTreeText(node))

	#@abstractmethod
	#def isCollection(self, lst):
	#	raise NotImplementedError()

	def preprocessAST(self, ast: typing.Any) -> typing.Any:
		return ast

	def parse(self, s: str) -> typing.Any:
		return self.parser(s)

	def terminalNodeToStr(self, token: typing.Optional[typing.Any]) -> typing.Optional[typing.Any]:
		return token
