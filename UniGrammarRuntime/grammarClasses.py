import re
import typing
from abc import ABCMeta

# LL(1) <= LL(2) <= LL(*) <= LR <= PEG <= GLR


_grammarClassRx = None
_registry = {}
_infiniteCounts = {"*", "∞", "inf"}

GrammarClassType = typing.Union["GrammarClass", typing.Type["GrammarClass"]]


class GrammarClassMeta(ABCMeta):
	def __new__(cls: typing.Type["GrammarClassMeta"], className: str, parents: typing.Iterable[typing.Type["GrammarClass"]], attrs: typing.Dict[str, typing.Any], *args, **kwargs) -> "GrammarClass":
		res = super().__new__(cls, className, parents, attrs, *args, **kwargs)
		_registry[className] = res
		return res


class _GrammarClass(metaclass=GrammarClassMeta):
	__slots__ = ()

	@classmethod
	def __leq__(cls, other: GrammarClassType):
		return isinstance(other, cls) or issubclass(other, cls)

	@classmethod
	def fromStr(cls, s: str) -> GrammarClassType:
		return _registry[s]


class GrammarClass(_GrammarClass):
	__slots__ = ("count",)

	def __init__(self, count: typing.Optional[int]) -> None:
		self.count = count

	@classmethod
	def fromStr(cls, s: str) -> GrammarClassType:
		s = s.upper()
		m = _grammarClassRx.match(s)
		if not m:
			raise KeyError("Unknown grammar class", s, list(_registry.keys()))
		gc = super().fromStr(m.group(1))
		count = m.group(2)
		if count is not None:
			if count in _infiniteCounts:
				count = None
			else:
				count = int(count)
			return gc(count)
		return gc


class RegExp(_GrammarClass):
	__slots__ = ()


class LL(GrammarClass):
	__slots__ = ()


class LR(LL):
	__slots__ = ()


class GLR(LR):
	__slots__ = ()


class LALR(LR):
	__slots__ = ()


class PEG(LR):
	__slots__ = ()


_grammarClassRx = re.compile("(" + "|".join(_registry.keys()) + r")(?:\((\d+|\*|∞|inf)\))?")
