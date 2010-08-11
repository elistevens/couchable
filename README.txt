Currently requires:
- Python 2.7
- CouchDB 0.11+ (untested on lower)
- http://pypi.python.org/pypi/CouchDB 0.7+ (untested on lower)

>>> import couchable
>>> cdb=couchable.CouchableDb('testing')
>>> class SimpleDoc(couchable.CouchableDoc):
...     def __init__(self, **kwargs):
...         for name, value in kwargs.items():
...             setattr(self, name, value)
... 
>>> a = SimpleDoc(name='AAA')
>>> b = SimpleDoc(name='BBB', a=a)
>>> c = SimpleDoc(name='CCC', a=a)
>>> id_list = cdb.store([b, c])
>>> id_list
['main__.SimpleDoc:...', 'main__.SimpleDoc:...']
>>> b, c = cdb.load(id_list)
>>> assert b.a is c.a
>>> cdb.db[b._id]
<Document 'main__.SimpleDoc:...'@'...' {'a': 'couchable:id:main__.SimpleDoc:...', 'couchable:': {'class': 'SimpleDoc', 'module': '__main__'}, 'name': 'BBB'}>


