import typing
from collections import OrderedDict
from weakref import ref

try:
	from math import inf
except ImportError:
	inf = float("inf")


class AttrDict(dict):
	__slots__ = ()

	def __getattr__(self, k: str) -> typing.Any:
		try:
			return self[k]
		except KeyError:
			raise AttributeError(k)

	def __dir__(self):
		return super().__dir__() + self.keys()


def flattenDictsIntoIterable(el) -> typing.Iterable:
	if isinstance(el, dict):
		for sel in el.values():
			yield from flattenDictsIntoIterable(sel)
	else:
		yield el


class ListLikeDict(OrderedDict):
	"""A very fucking redundant and limited hack."""

	__slots__ = ("_list",)

	def __init__(self, data: OrderedDict) -> None:
		super().__init__(data)
		self._list = list(super().keys())

	def __getitem__(self, k: str) -> typing.Any:
		if isinstance(k, int):
			return self[self._list[k]]
		return super().__getitem__(k)

	def __iter__(self):
		return iter(self.values())


class ListLikeAttrDict(ListLikeDict):
	__slots__ = ()

	def __getattr__(self, k: str) -> typing.Any:
		return self[k]


def getPythonModule(fileText: str, fileName: str):
	compiled = compile(fileText, fileName, "exec", optimize=2)
	globalz = {}
	eval(compiled, globalz)
	return globalz


class NodeWithAttrChildrenMixin:
	__slots__ = ()

	def __getattr__(self, k):
		try:
			return self.children[k]
		except KeyError:
			raise AttributeError(k)


class ListNodesMixin:
	__slots__ = ()

	def __iter__(self):
		return iter(self.children)


class TerminalNodeMixin:
	__slots__ = ()

	def __str__(self):
		return self.children[0]
