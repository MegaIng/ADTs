from __future__ import annotations

from dataclasses import dataclass, make_dataclass, fields


def reduced_repr(self):
    return f"{self.__class__.__name__}({', '.join(repr(getattr(self, f.name)) for f in fields(self))})"


@dataclass
class _ConstructorPlaceholder:
    name: str
    fields: tuple[_ConstructorPlaceholder, ...] | dict[str, _ConstructorPlaceholder] = None

    def __call__(self, *args, **kwargs):
        assert self.fields is None, "Can't call constructor more than once"
        assert not (bool(args) and bool(kwargs)), "Can't specify both named and unnamed fields"
        self.fields = args or kwargs
        return self

    def to_typehint(self):
        assert not self.fields
        return str(self.name)

    def make_dataclass(self, bases):
        assert self.fields is not None
        if isinstance(self.fields, tuple):
            fields = [(f"f{i:}", t.to_typehint()) for i, t in enumerate(self.fields)]
            return make_dataclass(self.name, fields, bases=bases, namespace={"__repr__": reduced_repr})
        else:
            fields = list(self.fields.items())
            return make_dataclass(self.name, fields, bases=bases)


class _ConstructorDict(dict):
    def __missing__(self, key):
        if not key.startswith("_"):
            self[key] = _ConstructorPlaceholder(key)
            return self[key]
        else:
            raise KeyError


class ADTMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return _ConstructorDict()

    def __new__(mcs, name, bases, namespace, **kwds):
        if "ADT" not in name and "ADT" in bases[0].__name__:
            out_namespace = {}
            constructors = {}
            for name, value in namespace.items():
                if not isinstance(value, _ConstructorPlaceholder):
                    out_namespace[name] = value
                elif value.fields is not None:
                    constructors[name] = value
            namespace = out_namespace
            cls = super(ADTMeta, mcs).__new__(mcs, name, bases, namespace, **kwds)
            for name, cons in constructors.items():
                setattr(cls, name, cons.make_dataclass((cls,)))
        else:
            cls = super(ADTMeta, mcs).__new__(mcs, name, bases, namespace, **kwds)
        return cls


class ADT(metaclass=ADTMeta):
    pass
