# Copyright (c) 2010 Eli Stevens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# stdlib
import collections
import copy
import cPickle as pickle
import datetime
import doctest
import gc
import random
import re
import sys
import time
import unittest

# 3rd party packages
import couchdb

from nose.plugins.attrib import attr

# in-house
import couchable
import couchable.core

#def dumpcdb(func):
#    def test_dumpcdb_(self):
#        try:
#            func(self)
#        except:
#            for _id in sorted(self.cdb.db):
#                print _id
#                doc = self.cdb.db[_id]
#                for key in sorted(doc):
#                    print '{:>15}: {}'.format(key, doc[key])
#
#            raise
#
#    return test_dumpcdb_

class Simple(object):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
            
    def __repr__(self):
        return repr(self.__dict__)

class SimpleKey(Simple):
    def __eq__(self, other):
        return hash(self) == hash(other)
        #frozenset(self.__dict__.keys()) == frozenset(other.__dict__.keys())
    def __hash__(self):
        return hash(frozenset(self.__dict__.keys()))


class SimplePickle(Simple):
    pass

couchable.registerPickleType(SimplePickle)

class SimpleDoc(couchable.CouchableDoc):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

class SimpleAttachment(couchable.CouchableAttachment):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

class AftermarketDoc(object):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

couchable.registerDocType(AftermarketDoc,
        lambda obj, cdb: couchable.newid(obj, lambda x: '-'.join(sorted(x.__dict__.keys()))),
        lambda obj, cdb: None)

class AftermarketAttachment(object):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

couchable.registerAttachmentType(AftermarketAttachment,
        serialize_func=(lambda obj: pickle.dumps(obj)),
        deserialize_func=(lambda data: pickle.loads(data)),
        content_type='application/octet-stream', gzip=True)

class DictSubclass(dict):
    def __iter__(self):
        return iter('foo')
    def __getitem__(self, key):
        return 'foo'

class ListSubclass(list):
    def __iter__(self):
        return iter('foo')
    def __getitem__(self, key):
        return 'foo'

NamedTupleABC = collections.namedtuple('NamedTupleABC', 'a,b,c')

class TupleSubclass(tuple):
    pass

# FIXME: need to support this...
#class TupleSubclassNew(tuple):
#    def __new__(...):
#        ...


class TestCouchable(unittest.TestCase):
    def setUp(self):
        self.seq = range(10)

        self.server = couchdb.Server()
        try:
            self.server.delete('testing_couchable')
            pass
        except:
            pass

        self.cdb = couchable.CouchableDb('testing_couchable')

        self.simple_dict = {
            'int': 1,
            'float': 2.0,
            'str': 'sss',
            'unicode': u'uuu\u2603',
            'set': set(['a', 'b']),
            'frozenset': frozenset(['a', 'b']),
            'list': [1, 2.0, 's', u'u'],
        }

        self.simple_dict['simple_dict'] = copy.deepcopy(self.simple_dict)

    def tearDown(self):
        del self.simple_dict

    #@unittest.skip('''Playing with ouput''')
    @attr('couchable')
    def test_docs(self):
        # doctest returns a tuple of (failed, attempted)
        self.assertEqual(doctest.testmod(couchable.core,
                optionflags=(doctest.REPORT_CDIFF | doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS))[0], 0)

    @attr('couchable')
    def test_2_baseTypeSubclasses_1(self):
        obj = Simple(d=DictSubclass(a=1, b=2), l=ListSubclass([1,2,3]))

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEqual(type(obj.d), DictSubclass)
        self.assertEqual(type(obj.l), ListSubclass)

    @attr('couchable')
    def test_2_baseTypeSubclasses_2(self):
        obj = DictSubclass(d=DictSubclass(a=1, b=2), l=ListSubclass([DictSubclass(e=5, f=6),1,2,3]))
        obj.x = 4

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        print obj
        print obj.__dict__

        self.assertEqual(obj.x, 4)
        self.assertEqual(type(obj), DictSubclass)
        self.assertEqual(type(dict.__getitem__(obj, 'd')), DictSubclass)
        self.assertEqual(type(dict.__getitem__(obj, 'l')), ListSubclass)

        l = dict.__getitem__(obj, 'l')
        #list.__getitem__(l, 0)

        self.assertEqual(type(list.__getitem__(l, 0)), DictSubclass)
        #assert False

    @attr('couchable')
    def test_2_binaryStrings_1(self):
        s = 'abc\xaa\xbb\xcc this is the tricky part: \\xddd'
        obj = Simple(s=s)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEquals(obj.s, s)

    @attr('couchable')
    def test_2_binaryStrings_2(self):
        #s = 'abc\xaa\xbb\xcc this is the tricky part: \\xddd'
        s = ''.join([chr(x) for x in range(256)])
        obj = Simple(s=s)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEquals(obj.s, s)

    @attr('couchable')
    def test_2_binaryStrings_3(self):
        #s = 'abc\xaa\xbb\xcc this is the tricky part: \\xddd'
        s = ''.join([chr(x) for x in range(127)])
        obj = Simple(s=s)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEquals(obj.s, s)

    @attr('couchable')
    def test_2_nullStrings(self):
        s = '\x00abc\xaa\xbb\xcc this is the tricky part: \\xddd'
        obj = Simple(s=s)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEquals(obj.s, s)


    @attr('couchable')
    def test_1_simple(self):
        obj = Simple(**self.simple_dict)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEqual(obj.__class__, Simple)
        for key, value in self.simple_dict.items():
            self.assertEqual(getattr(obj, key), value)

    @attr('couchable')
    def test_3_namedtuple(self):
        obj = Simple(abc=NamedTupleABC(1,2,3), ts=TupleSubclass([1,2,3,4,5]))

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEqual(type(obj.abc), NamedTupleABC)
        self.assertEqual(obj.abc.a, 1)

        self.assertEqual(type(obj.ts), TupleSubclass)
        self.assertEqual(obj.ts[3], 4)

    @attr('couchable')
    def test_31_odict(self):
        limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(100)


            kv_list = [(chr(ord('a') + i), i) for i in range(10)]
            od = collections.OrderedDict()
            for k,v in kv_list:
                od[k] = v

            obj = Simple(od=od)

            _id = self.cdb.store(obj)

            del obj
            gc.collect()
            self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

            obj = self.cdb.load(_id)

            self.assertEqual(type(obj.od), collections.OrderedDict)
            self.assertEqual(list(obj.od.items()), kv_list)

        finally:
            sys.setrecursionlimit(limit)

    @attr('couchable', 'elis')
    def test_32_types(self):
        obj = Simple(int=int)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        obj = self.cdb.load(_id)

        self.assertEqual(type(obj.int), type)
        self.assertEqual(obj.int, int)


    @attr('couchable')
    def test_40_external_edits(self):
        obj = Simple(i=1)
        _id = self.cdb.store(obj)
        
        doc = self.cdb.db.get(_id)
        doc['i'] = 2
        self.cdb.db.save(doc)

        self.assertEqual(obj.i, 1)

        obj = self.cdb.load(_id)
        self.assertEqual(obj.i, 2)
        
        #assert False
        
        
    @attr('couchable', 'elis')
    def test_40_nested_docs_with_tuples(self):
        nt = NamedTupleABC(1,2,3)
        
        targetobj = Simple(aaa=nt, target={nt: 'bbb'}, zzz=nt, _foo=1)
        obj = Simple(sub={nt: targetobj}, abc2={nt: 'abc2'}, _foo=1)
        
        #subobj.o = obj

        self.cdb.store(targetobj)
        _id = self.cdb.store(obj)
        
        
        target_id = targetobj._id

        del obj
        del targetobj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        #obj = self.cdb.load(_id)
        
        doc = self.cdb.db[target_id]
        
        self.assertIn('keys', doc['couchable:'])
        
        #self.assertEqual(type(obj.sub.abc), NamedTupleABC)
        #self.assertEqual(obj.sub.abc.a, 1)
        #
        #self.assertEqual(type(obj.sub.ts), TupleSubclass)
        #self.assertEqual(obj.sub.ts[3], 4)
        
        #assert False


    @attr('couchable', 'elis')
    def test_40_pickles(self):
        pk = SimplePickle(a=1, b=2, c=3)
        
        obj = Simple(d={'pk': pk})
        
        _id = self.cdb.store(obj)

        del obj
        del pk
        gc.collect()

        #for v in self.cdb._obj_by_id.values():
        #    print v
        #    print gc.get_referrers(v)
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        obj = self.cdb.load(_id)
        
        self.assertEqual(obj.d['pk'].a, 1)
        
        #assert False


    @attr('couchable', 'elis')
    def test_nonStrKeys(self):
        d = {1234:'ints', (1,2,3,4):'tuples', frozenset([1,1,2,2,3,3]): 'frozenset', None: 'none', SimpleKey(this_is_a_key=True):'truth'}

        obj = Simple(d=d)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEqual(type(obj), Simple)

        for key, value in d.items():
            self.assertIn(key, obj.d)
            self.assertEqual(obj.d[key], value)


    @attr('couchable')
    def test_private(self):
        a = SimpleDoc(name='AAA', _implementationDetail='foo', b=Simple(_morePrivate='bbb'), _inst=Simple(i='j'))

        a_id = self.cdb.store(a)

        del a
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        a = self.cdb.load(a_id)

        self.assertEqual(type(a), SimpleDoc)
        self.assertTrue(hasattr(a, '_implementationDetail'))
        self.assertTrue(hasattr(a.b, '_morePrivate'))

        self.assertEqual(type(a._inst), Simple)

        a_id = self.cdb.store(a)

    @attr('couchable')
    def test_couchablePrefix(self):
        obj = Simple(s='couchable:foo', u=u'couchable:bar')

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEqual(obj.s, 'couchable:foo')
        self.assertEqual(obj.u, u'couchable:bar')

    @attr('couchable')
    def test_moduleStorage(self):
        import os.path

        obj = Simple(p=os.path)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        self.assertEqual(obj.p, os.path)



    @attr('couchable')
    def test_multidoc(self):
        a = SimpleDoc(name='AAA', s=Simple(sss='SSS'))
        b = SimpleDoc(name='BBB', a=a)
        c = SimpleDoc(name='CCC', a=a)

        id_list = self.cdb.store([b, c])

        del a
        del b
        del c
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        b, c = self.cdb.load(id_list)

        self.assertIs(b.a, c.a)

    @attr('couchable')
    def test_viewLoading3(self):
        a = SimpleDoc(name='AAA', s=Simple(sss='SSS'))
        b = SimpleDoc(name='BBB', a=a)
        c = SimpleDoc(name='CCC', a=a)

        id_list = self.cdb.store([b, c])

        del a
        del b
        del c
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        fullName = self.cdb.addClassView(SimpleDoc, 'name', ['name'])

        #self.cdb.db.view()

        x = self.cdb.load(self.cdb.db.view('couchable/' + fullName, include_docs=True, startkey=['AAA'], endkey=['BBB', {}]).rows)

        print x

        a, b = x

        self.assertEqual(a.name, 'AAA')
        self.assertEqual(b.name, 'BBB')
        self.assertEqual(a.s.sss, 'SSS')
        self.assertIs(a, b.a)

    @attr('couchable')
    def test_viewLoading2(self):
        a = SimpleDoc(name='AAA', s=Simple(sss='SSS'))
        b = SimpleDoc(name='BBB', a=a)
        c = SimpleDoc(name='CCC', a=a)

        id_list = self.cdb.store([b, c])

        del a
        del b
        del c
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        fullName = self.cdb.addClassView(SimpleDoc, 'name', ['name'])

        x = self.cdb.load(id_list, self.cdb.db.view('couchable/' + fullName, include_docs=True, startkey=['BBB'], endkey=['CCC', {}]).rows)

        print x

        b, c = x

        self.assertEqual(b.a.name, 'AAA')
        self.assertEqual(b.name, 'BBB')
        self.assertEqual(b.a.s.sss, 'SSS')
        self.assertIs(b.a, c.a)



    @attr('slow', 'couchable')
    def test_simpleAttachments(self):
        b = SimpleDoc(name='BBB', attach=SimpleAttachment(b=1, bb=2))
        c = SimpleDoc(name='CCC', attach=SimpleAttachment(c=1, cc=2), bb=b)
        a = SimpleDoc(name='AAA', attach=SimpleAttachment(a=1, aa=2), bb=b,
                dt=datetime.datetime.now(),
                td=datetime.timedelta(seconds=0.5),
                regex=re.compile('[a-z]+'),
            )

        _id = self.cdb.store(c)
        _id = self.cdb.store(a)

        del a
        del b
        del c
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        self.assertIn('self.attach', self.cdb.db[_id]['_attachments'])

        a = self.cdb.load(_id)

        self.assertEqual(a.attach.a, 1)
        self.assertEqual(a.attach.aa, 2)

        a.foo = 'bar'
        self.cdb.store(a)
        a.foo = 'baz'
        self.cdb.store(a)
        self.cdb.store(a)

        #print self.cdb.db[_id]

        self.assertNotIn('_attachments', self.cdb.db[_id]['couchable:'].get('private', {}))
        #assert False

        self.assertLess(a.dt, datetime.datetime.now())
        self.assertGreater(a.dt + a.td, datetime.datetime.now())
        time.sleep(1)
        self.assertLess(a.dt + a.td, datetime.datetime.now())

        self.assertTrue(a.regex.match('abcd'))
        self.assertEqual(a.regex.match('1234'), None)

    @attr('slow', 'couchable', 'elis')
    def test_aftermarketAttachments(self):
        b = AftermarketDoc(name='BBB', attach=AftermarketAttachment(b=1, bb=2))
        c = AftermarketDoc(name='CCC', attach=AftermarketAttachment(c=1, cc=2), bb=b)
        a = AftermarketDoc(name='AAA', attach=AftermarketAttachment(a=1, aa=2), bb=b,
                dt=datetime.datetime.now(),
                td=datetime.timedelta(seconds=0.5),
                regex=re.compile('[a-z]+'),
            )

        _id = self.cdb.store(c)
        _id = self.cdb.store(a)

        del a
        del b
        del c
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

        self.assertIn('self.attach', self.cdb.db[_id]['_attachments'])

        a = self.cdb.load(_id)

        self.assertEqual(a.attach.a, 1)
        self.assertEqual(a.attach.aa, 2)

        a.foo = 'bar'
        self.cdb.store(a)
        a.foo = 'baz'
        self.cdb.store(a)
        self.cdb.store(a)

        #print self.cdb.db[_id]

        self.assertNotIn('_attachments', self.cdb.db[_id]['couchable:'].get('private', {}))
        #assert False

        self.assertLess(a.dt, datetime.datetime.now())
        self.assertGreater(a.dt + a.td, datetime.datetime.now())
        time.sleep(1)
        self.assertLess(a.dt + a.td, datetime.datetime.now())

        self.assertTrue(a.regex.match('abcd'))
        self.assertEqual(a.regex.match('1234'), None)

        del a
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


    @attr('couchable')
    def test_docCycles(self):
        limit = sys.getrecursionlimit()
        try:
            # This number might need to get tweaked if this test is failing; that's fine
            sys.setrecursionlimit(100)

            a = SimpleDoc(name='AAA')
            b = SimpleDoc(name='BBB', a=a)
            c = SimpleDoc(name='CCC', a=a)
            a.b = b

            a_id = self.cdb.store(a)
            b_id = self.cdb.store(b)
            c_id = self.cdb.store(c)

            del b
            del c
            del a
            gc.collect()
            self.assertFalse(self.cdb._obj_by_id, str(self.cdb._obj_by_id.items()))

            a = self.cdb.load(a_id)
            b = self.cdb.load(b_id)
            c = self.cdb.load(c_id)

            self.assertIs(c.a, a)
            self.assertIs(b.a, a)
            self.assertIs(b, a.b)

        finally:
            sys.setrecursionlimit(limit)

    @unittest.expectedFailure
    @attr('slow', 'couchable')
    def test_uncouchable(self):
        self.cdb.store(self.cdb)

    @attr('couchable')
    def test_cdbCopy(self):
        obj = Simple(**self.simple_dict)

        _id = self.cdb.store(obj)

        del obj
        gc.collect()
        self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))


        obj = self.cdb.load(_id)

        cdbCopy = copy.deepcopy(self.cdb)

        self.assertIs(obj, cdbCopy.load(_id))


    @unittest.skip("""This fails intermittently.  I suspect a problem with the base couchdb library, but I can't pin it down yet.""")
    @attr('couchable')
    def test_wait(self):
        a = SimpleDoc(name='AAA')
        a_id = self.cdb.store(a)

        time.sleep(300)

        b = SimpleDoc(name='BBB', a=a)
        b_id = self.cdb.store(b)


    @unittest.skip("""still implementing tests for this feature...""")
    @attr('couchable')
    def test_aftermarket(self):
        pass

    @unittest.skip("""still implementing tests for this feature...""")
    @attr('couchable')
    def test_loadFromView(self):
        pass



    #@unittest.skip("""cycles don't work ATM""")
    @unittest.expectedFailure
    @attr('couchable')
    def test_cycles(self):
        limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(50)

            a = Simple(name='AAA')
            b = Simple(name='BBB', a=a)
            c = Simple(name='CCC', a=a)
            a.b = b

            a_id = self.cdb.store(a)
            b_id = self.cdb.store(b)
            c_id = self.cdb.store(c)

            del a
            del b
            del c
            gc.collect()
            self.assertFalse(self.cdb._obj_by_id, repr(self.cdb._obj_by_id.items()))

            a = self.cdb.load(a_id)
            b = self.cdb.load(b_id)
            c = self.cdb.load(c_id)

            self.assertIs(c.a, a)
            self.assertIs(b.a, a)
            self.assertIs(b, a.b)

        finally:
            sys.setrecursionlimit(limit)

# eof
