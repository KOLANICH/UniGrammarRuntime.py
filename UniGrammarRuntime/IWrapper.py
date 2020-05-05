import typing
from abc import ABC

# pylint:disable=too-few-public-methods


class IParseResult:
	__slots__ = ()

	def __repr__(self):
		return "".join(
			(
				self.__class__.__name__,
				"<",
				", ".join(
					"=".join((k, repr(getattr(self, k))))
					for k in self.__class__.__slots__
				),
				">",
			)
		)


class IWrapper(ABC):
	__slots__ = ("backend",)

	__MAIN_PRODUCTION__ = None

	def __init__(self, backend):
		self.backend = backend

	def __call__(self, s: str) -> typing.Union[typing.Iterable[IParseResult], IParseResult]:
		preprocessed = self.backend.preprocessAST(self.backend.parse(s))
		return self.__MAIN_PRODUCTION__(preprocessed)
