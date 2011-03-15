Currently requires:
- Python 2.7
- CouchDB 1.0.1+ (untested on lower, 0.11 will probably work)
- http://pypi.python.org/pypi/CouchDB 0.8+ (untested on lower, 0.7 will probably work)


Source:   http://github.com/wickedgrey/couchable
Package:  http://pypi.python.org/pypi/couchable
API docs: http://packages.python.org/couchable
Blog:     http://blog.nopinch.net/tag/couchable/


Example of Use
===============

import numpy
import couchdb
import couchable

couchable.registerAttachmentType(numpy.ndarray,
        lambda obj: obj.dumps(),
        lambda data: numpy.loads(data),
        'application/octet-stream', gzip=True)

class BaseClass(object):
    def __init__(self, shape, type_=numpy.uint16):
        self.vol = numpy.zeros(shape, type_)
    # ...


class ClassA(object):
    def __init__(self, name):
        self.name = name
    # ...
couchable.registerDocType(ClassA,
        lambda obj, cdb: couchable.newid(obj, lambda x: x.name),
        lambda obj, cdb: None)


class SubClassB(BaseClass):
    def __init__(self, container):
        BaseClass.__init__(self, container.vol.shape, numpy.float32, container.pixelLength_mm)
        self.container = container
    # ...
couchable.registerDocType(SubClassB)


class Container(BaseClass):
    def __init__(self):
        BaseClass.__init__(self, (300, 400, 200), numpy.bool_)
    # ...
couchable.registerDocType(Container)


def main(options, arguments):
    cdb = couchable.CouchableDb(options.cdb_name)

    view = couchdb.design.ViewDefinition('generic', 'byclass',
        '''
        function(doc) {
            if ('couchable:' in doc) {
                info = doc['couchable:'];
                emit([info.module, info.class, doc._id], doc);
            }
        }''')
    view.sync(cdb.db)

    # ...

    viewResult = view(cdb.db, include_docs=True, startkey=['example', 'Container'], endkey=['example', 'Container', {}])
    container_list = cdb.load(viewResult.rows)

    # ...


Examples of the JSON Structure of Stored Objects
================================================

All of the object dumps are taken from Futon.

>>> import couchable
>>> cdb=couchable.CouchableDb('example')
>>> class SimpleDoc(couchable.CouchableDoc):
...     def __init__(self, **kwargs):
...         for name, value in kwargs.items():
...             setattr(self, name, value)
...
>>> a = SimpleDoc(name='AAA')
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "1-315ed02172dddb449a4ab38e54b8bb85",
   "couchable:": {
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "name": "AAA"
}

The key things to note are:
- The automatically generated id includes some hints about the type of the
    object.  It is only made if the object doesn't have an ID already.
- The object metadata is stored in "couchable:".
- Normal field names are stored at the top level of the object.


>>> a.int_ = 1234
>>> a.long_ = 1234567890L
>>> a.str_ = 'some str'
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "2-618b01362f076539f1abb481585b2f64",
   "couchable:": {
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "long_": 1234567890,
   "name": "AAA",
   "str_": "some str",
   "int_": 1234
}

Numbers, strings and lists are stored in native JSON.  Dicts with string keys
are as well, though non-string keys are disallowed by JSON, and so require
special handling (see below).


>>> del a.int_
>>> del a.long_
>>> del a.str_
>>> a.tuple_ = (1, 'two', 3.3)
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "3-a24d5422be27e8dca0f4b4375718bceb",
   "name": "AAA",
   "couchable:": {
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "tuple_": {
       "couchable:": {
           "args": [
               [
                   1,
                   "two",
                   3.3
               ]
           ],
           "class": "tuple",
           "module": "__builtin__",
           "kwargs": {
           }
       }
   }
}

Tuples do not have a native JSON representation, so they get treated much like
arbitrary objects do (note: since tuples don't have a __dict__, they need
special case support).  Here, the "args" and "kwargs" will be passed into the
constructor of the type when it's time to load this object.


>>> del a.tuple_
>>> a._implementationDetail = 'this is private'
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "5-5ac8698c7b9567642484e728e60b95b1",
   "couchable:": {
       "private": {
           "_implementationDetail": "this is private"
       },
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "name": "AAA"
}

CouchDB reserves all top-level fields that start with an underscore.  Since
python makes liberal use of underscores to denote "private" or implementation
detail fields, those end up inside of a second-level dictionary inside of the
"couchable:" dict.  During loading, these will end up back inside the object
__dict__.


>>> del a._implementationDetail
>>> a.reserved = 'couchable: reserving the string "couchable:" since 2010'
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "6-a7ef4d2ba59a68128b076cf5d5d0aaee",
   "couchable:": {
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "reserved": "couchable:append:str:couchable: reserving the string \"couchable:\" since 2010",
   "name": "AAA"
}

Any string that starts with "couchable:" is escaped, since couchable makes
heavy use of that prefix.  See below.


>>> del a.reserved
>>> a.dict_ = {'foo':'FOO', 123:'bar', (45, 67):'baz'}
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "7-4706c617a5f8900956c76ecb6f2e2daa",
   "couchable:": {
       "keys": {
           "couchable:key:tuple:(45, 67)": {
               "couchable:": {
                   "args": [[45, 67]],
                   "class": "tuple",
                   "module": "__builtin__",
                   "kwargs": {
                   }
               }
           }
       },
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "dict_": {
       "couchable:key:tuple:(45, 67)": "baz",
       "foo": "FOO",
       "couchable:repr:int:123": "bar"
   },
   "name": "AAA"
}

As we saw above, tuples are supported using similar structures to those used
by arbitrary objects.  However, JSON only supports strings as dictionary keys.
We solve this by replacing the object-as-key with a string that acts as a
pointer to the actual object, which is stored inside doc['couchable:']['keys']
as the full object.

Similarly, ints cannot be JSON dictonary keys, but we can use the int repr to
fully represent the object, and so we do so in-place (note that this wouldn't
work for tuples because tuples can contain arbitrarily complex objects, not
just the ints that we have in the example).


>>> del a.dict_
>>> a.nested = {(1,1):{(2,2):{(3,3):'four'}}}
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "10-1fe944276e27bef87259857be9d2abd3",
   "nested": {
       "couchable:key:tuple:(1, 1)": {
           "couchable:key:tuple:(2, 2)": {
               "couchable:key:tuple:(3, 3)": "four"
           }
       }
   },
   "couchable:": {
       "keys": {
           "couchable:key:tuple:(1, 1)": {
               "couchable:": {
                   "args": [[1, 1]],
                   "class": "tuple",
                   "module": "__builtin__",
                   "kwargs": {
                   }
               }
           },
           "couchable:key:tuple:(2, 2)": {
               "couchable:": {
                   "args": [[2, 2]],
                   "class": "tuple",
                   "module": "__builtin__",
                   "kwargs": {
                   }
               }
           },
           "couchable:key:tuple:(3, 3)": {
               "couchable:": {
                   "args": [[3, 3]],
                   "class": "tuple",
                   "module": "__builtin__",
                   "kwargs": {
                   }
               }
           }
       },
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "name": "AAA"
}

Here we have nested dictionaries with tuple keys, and dict values.  All of the
tuples are replaced with string pointers, and fully saved in 'keys'.  Note
that 'keys' is a *document* level construct, not an object level one.  'keys'
will never appear outside of doc['couchable:'] (at least not outside of naming
coincidences).


>>> del a.nested
>>> b=SimpleDoc(name='BBB')
>>> a.bbb = b
>>> cdb.store(a)
'main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7'

{
   "_id": "main__.SimpleDoc:2a208810-467f-4feb-a5bb-98d0beb1e5e7",
   "_rev": "11-5eccb48b99431431c9f91b5e84a4ed7b",
   "bbb": "couchable:id:main__.SimpleDoc:544a1408-d3f3-41c4-a428-9f0d2d8e2372",
   "couchable:": {
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "name": "AAA"
}

{
   "_id": "main__.SimpleDoc:544a1408-d3f3-41c4-a428-9f0d2d8e2372",
   "_rev": "1-577fefe455995539e11c992b7b46e10a",
   "couchable:": {
       "class": "SimpleDoc",
       "module": "__main__"
   },
   "name": "BBB"
}

Here, we show the behavior when storing multiple objects, each of which is
flagged as needing to be a full document.  Similar to the other string
pointers encountered already, couchable:id points to an object stored in an
entirely different document.

Known Limitations
=================

In general, couchable doesn't play well with classes that override __new__ in
odd ways.

Couchable cannot (and will probably never) store instances of the following
types:

- Tuple subclasses that override __new__ that *don't* do so in a way that is
compatible with collections.namedtuple.
- Programmatically defined classes that are not importable (they're basically
impossible to reconstruct during loading).

This list may not be exhaustive; unknown limitations may exist.
