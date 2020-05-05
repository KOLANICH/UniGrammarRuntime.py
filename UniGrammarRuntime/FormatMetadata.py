import typing
import warnings

from UniGrammarRuntime.ToolMetadata import Product


class FormatMetadata:
	__slots__ = ("product", "grammarExtensions")

	def __init__(self, grammarExtensions: typing.Optional[typing.Union[typing.Tuple[str, str], typing.Tuple[str]]] = None, product: typing.Optional[Product] = None) -> None:
		self.product = product
		self.grammarExtensions = grammarExtensions

	@property
	def mainExtension(self):
		if self.grammarExtensions:
			return self.grammarExtensions[0]
		else:
			warnings.warn(self.product.name + " has no well-known extension for grammar files. Using DSL name (" + self.product.name + ") instead of the extension.")
			return self.product.name
