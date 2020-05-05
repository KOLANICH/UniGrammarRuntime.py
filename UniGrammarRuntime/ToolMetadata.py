import typing
import warnings

from .grammarClasses import GrammarClassType


class Product:
	__slots__ = ("name", "website")

	def __init__(self, name: str, website: typing.Union[typing.Tuple[str, str], str]) -> None:
		self.name = name
		self.website = website


class ToolMetadata(Product):
	__slots__ = ("product", "buildsTree", "grammarClasses", "runtimeLib")

	def __init__(self, product: typing.Optional[Product], runtimeLib: typing.Dict[str, typing.Optional[str]], buildsTree: typing.Optional[bool], grammarClasses: typing.Iterable[GrammarClassType]) -> None:
		self.product = product
		self.runtimeLib = runtimeLib
		self.buildsTree = buildsTree
		self.grammarClasses = grammarClasses
