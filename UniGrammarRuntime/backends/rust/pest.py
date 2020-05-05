import typing
from collections import OrderedDict
from pathlib import Path

from UniGrammarRuntimeCore.IParser import IParser, IParserFactory

from ...grammarClasses import PEG
from ...IParser import IParserFactoryFromSource
from ...IParsingBackend import IParsingBackend
from ...ToolMetadata import Product, ToolMetadata
from ...utils import ListLikeDict, ListNodesMixin, NodeWithAttrChildrenMixin


class PestParser(IParser):
	#NAME = "pest"
	#EXT = "pest"

	__slots__ = ("parser",)

	def __init__(self, parser) -> None:
		super().__init__()
		self.parser = parser

	def __call__(self, s: str):
		return self.parser.parse(s)


class PestParserFactory(IParserFactory):
	__slots__ = ()
	PARSER_CLASS = PestParser
	META = ToolMetadata(
		Product(
			name="pest",
			website=("https://github.com/pest-parser/pest",),
		),
		runtimeLib={
			"rust": None,
		},
		grammarClasses=(PEG,),
		buildsTree=False,
	)
