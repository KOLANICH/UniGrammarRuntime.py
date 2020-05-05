from .DSLMetadata import DSLMetadata
from .ToolMetadata import Product

packrat = DSLMetadata(
	officialLibraryRepo=None,
	grammarExtensions=("peg",),
	product=Product(
		name="packrat",
		website="https://bford.info/pub/lang/packrat-icfp02/",
	),
)
