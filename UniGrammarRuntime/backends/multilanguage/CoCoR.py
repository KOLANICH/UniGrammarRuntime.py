import typing
from collections import OrderedDict
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser, IParserFactory

from ...grammarClasses import LL
from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend
from ...ToolMetadata import Product, ToolMetadata
from ...utils import ListLikeDict, ListNodesMixin, NodeWithAttrChildrenMixin


class CoCoRParser(IParser):
	NAME = "CoCo/R"
	#EXT = "CoCo/R"

	__slots__ = ("parser",)

	def __init__(self, parser) -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s)


class CoCoRParserFactory(IParserFactory):
	__slots__ = ()
	PARSER_CLASS = CoCoRParser
	META = ToolMetadata(
		Product(
			name="CoCo/R",
			website=("https://codeberg.org/KOLANICH/CoCoPy",),
		),
		runtimeLib={
			"python": None,
			"java": None,
			"c#": None,
			"c++": None,
			"basic": None,
			"pascal": None,
		},
		grammarClasses=(LL(1),),
		buildsTree=False,
	)
