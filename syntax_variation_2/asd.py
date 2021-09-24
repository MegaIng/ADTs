from __future__ import annotations

import sys
from dataclasses import dataclass, make_dataclass
from typing import Any


def check_upper_frames(name: str):
    frame = sys._getframe(2)  # The frame of the class body
    assert isinstance(frame.f_locals, _ASDNamespace)
    defining_frame = frame.f_back  # The frame in which the class object get defined, not the body of the class
    try:
        return defining_frame.f_locals[name]
    except KeyError:
        pass
    try:
        return frame.f_globals[name]
    except KeyError:
        pass
    try:
        return getattr(frame.f_globals["__builtins__"], name)
    except AttributeError:
        raise KeyError(name)


@dataclass
class _Constructor:
    name: str
    fields: list[tuple[str, Any]]
    category: str = None


@dataclass
class _PlaceholderGroup:
    values: list[_Placeholder]

    def __or__(self, other):
        if isinstance(other, _Placeholder):
            return _PlaceholderGroup([*self.values, other])
        else:
            return NotImplemented


@dataclass
class _Placeholder:
    name: str
    ns: _ASDNamespace

    def __call__(self, *args, **kwargs):
        assert not (args and kwargs), "Can only specify args or kwargs for constructor"
        assert self.name not in self.ns.constructors, f"Constructor {self.name} already defined"
        if args:
            fields = [(f"f{i}", a) for i, a in enumerate(args)]
        else:
            fields = list(kwargs.items())
        self.ns.constructors[self.name] = _Constructor(self.name, fields)
        return self

    def __or__(self, other):
        if isinstance(other, _Placeholder):
            return _PlaceholderGroup([self, other])
        else:
            return NotImplemented


class _ASDNamespace:
    def __init__(self, name: str):
        self.name = name
        self.normal_vars = {}
        self.categories = {}
        self.constructors = {}

    def __getitem__(self, item):
        if item.startswith("_"):
            return self.normal_vars[item]
        try:
            return check_upper_frames(item)
        except KeyError:
            return _Placeholder(item, self)

    def __setitem__(self, key, value):
        if key.startswith("_") and key != "_":
            self.normal_vars[key] = value
        else:
            assert isinstance(value, (_Placeholder, _PlaceholderGroup))
            cons = []
            if isinstance(value, _PlaceholderGroup):
                for p in value.values:
                    assert p.name in self.constructors
                    cons.append(self.constructors[p.name])
                    cons[-1].category = key
            else:
                assert value.name in self.constructors
                cons.append(self.constructors[value.name])
                cons[-1].category = key
            self.categories[key] = cons


class ASDMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        if "ASD" in name:
            return {}
        else:
            return _ASDNamespace(name)

    def __new__(mcs, name, bases, namespace, **kwds):
        assert not kwds, kwds
        if isinstance(namespace, _ASDNamespace):
            cls = super().__new__(mcs, name, bases, namespace.normal_vars, **kwds)
            categories = {}
            for cat in namespace.categories:
                if cat != "_":
                    c = super().__new__(mcs, cat, (cls,), {
                        "__module__": cls.__module__,
                        "__qualname__": f"{cls.__qualname__}.{cat}"})
                    categories[cat] = c
                    setattr(cls, cat, c)
            for cons in namespace.constructors.values():
                base = categories[cons.category] if cons.category != "_" else cls
                c = super().__new__(mcs, cons.name, (base,), {
                    "__annotations__": dict(cons.fields),
                    "__module__": cls.__module__,
                    "__qualname__": f"{base.__qualname__}.{cons.name}"
                })
                setattr(cls, cons.name, dc := dataclass(c, frozen=True))
                if base is not cls:
                    setattr(base, cons.name, dc)
        else:
            cls = super().__new__(mcs, name, bases, namespace, **kwds)
        return cls


class ASD(metaclass=ASDMeta):
    pass
