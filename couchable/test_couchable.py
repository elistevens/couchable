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

class SimpleKey(Simple):
    def __eq__(self, other):
        return hash(self) == hash(other)
        #frozenset(self.__dict__.keys()) == frozenset(other.__dict__.keys())
    def __hash__(self):
        return hash(frozenset(self.__dict__.keys()))

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
        lambda obj, cdb: couchable.newid(obj, lambda x: str(sorted(x.__dict__.keys()))),
        lambda obj, cdb: None)

class AftermarketAttachment(object):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

couchable.registerAttachmentType(AftermarketAttachment,
        serialize_func=(lambda obj: pickle.dumps(obj)),
        deserialize_func=(lambda data: pickle.loads(data)),
        content_type='application/octet-stream', gzip=True)


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
            'unicode': u'uuu',
            'set': set(['a', 'b']),
            'frozenset': frozenset(['a', 'b']),
            'list': [1, 2.0, 's', u'u'],
        }

        self.simple_dict['simple_dict'] = copy.deepcopy(self.simple_dict)

    def tearDown(self):
        del self.simple_dict

    #@unittest.skip('''Playing with ouput''')
    def test_docs(self):
        # doctest returns a tuple of (failed, attempted)
        self.assertEqual(doctest.testmod(couchable.core,
                optionflags=(doctest.REPORT_CDIFF | doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS))[0], 0)



    def test_simple(self):
        obj = Simple(**self.simple_dict)

        _id = self.cdb.store(obj)

        del obj
        self.assertFalse(self.cdb._obj_by_id)

        obj = self.cdb.load(_id)

        self.assertEqual(obj.__class__, Simple)
        for key, value in self.simple_dict.items():
            self.assertEqual(getattr(obj, key), value)


    def test_nonStrKeys(self):
        d = {1234:'ints', (1,2,3,4):'tuples', frozenset([1,1,2,2,3,3]): 'frozenset', None: 'none', SimpleKey(this_is_a_key=True):'truth'}

        obj = Simple(d=d)

        _id = self.cdb.store(obj)

        del obj
        self.assertFalse(self.cdb._obj_by_id)

        obj = self.cdb.load(_id)

        self.assertEqual(type(obj), Simple)

        for key, value in d.items():
            self.assertIn(key, obj.d)
            self.assertEqual(obj.d[key], value)


    def test_private(self):
        a = SimpleDoc(name='AAA', _implementationDetail='foo', b=Simple(_morePrivate='bbb'))

        a_id = self.cdb.store(a)

        del a
        self.assertFalse(self.cdb._obj_by_id)

        a = self.cdb.load(a_id)

        self.assertEqual(type(a), SimpleDoc)
        self.assertTrue(hasattr(a, '_implementationDetail'))
        self.assertTrue(hasattr(a.b, '_morePrivate'))

        a_id = self.cdb.store(a)

    def test_couchablePrefix(self):
        obj = Simple(s='couchable:foo', u=u'couchable:bar')

        _id = self.cdb.store(obj)

        del obj
        self.assertFalse(self.cdb._obj_by_id)

        obj = self.cdb.load(_id)

        self.assertEqual(obj.s, 'couchable:foo')
        self.assertEqual(obj.u, u'couchable:bar')

    def test_moduleStorage(self):
        import os.path

        obj = Simple(p=os.path)

        _id = self.cdb.store(obj)

        del obj
        self.assertFalse(self.cdb._obj_by_id)

        obj = self.cdb.load(_id)

        self.assertEqual(obj.p, os.path)



    def test_multidoc(self):
        a = SimpleDoc(name='AAA', s=Simple(sss='SSS'))
        b = SimpleDoc(name='BBB', a=a)
        c = SimpleDoc(name='CCC', a=a)

        id_list = self.cdb.store([b, c])

        del a
        del b
        del c
        self.assertFalse(self.cdb._obj_by_id)

        b, c = self.cdb.load(id_list)

        self.assertIs(b.a, c.a)

    def test_viewLoading3(self):
        a = SimpleDoc(name='AAA', s=Simple(sss='SSS'))
        b = SimpleDoc(name='BBB', a=a)
        c = SimpleDoc(name='CCC', a=a)

        id_list = self.cdb.store([b, c])

        del a
        del b
        del c
        self.assertFalse(self.cdb._obj_by_id)

        fullName = self.cdb.addClassView(SimpleDoc, 'name', ['name'])

        #self.cdb.db.view()

        x = self.cdb.load(self.cdb.db.view('couchable/' + fullName, include_docs=True, startkey=['AAA'], endkey=['BBB', {}]).rows)

        print x

        a, b = x

        self.assertEqual(a.name, 'AAA')
        self.assertEqual(b.name, 'BBB')
        self.assertEqual(a.s.sss, 'SSS')
        self.assertIs(a, b.a)

    def test_viewLoading2(self):
        a = SimpleDoc(name='AAA', s=Simple(sss='SSS'))
        b = SimpleDoc(name='BBB', a=a)
        c = SimpleDoc(name='CCC', a=a)

        id_list = self.cdb.store([b, c])

        del a
        del b
        del c
        self.assertFalse(self.cdb._obj_by_id)

        fullName = self.cdb.addClassView(SimpleDoc, 'name', ['name'])

        x = self.cdb.load(id_list, self.cdb.db.view('couchable/' + fullName, include_docs=True, startkey=['BBB'], endkey=['CCC', {}]).rows)

        print x

        b, c = x

        self.assertEqual(b.a.name, 'AAA')
        self.assertEqual(b.name, 'BBB')
        self.assertEqual(b.a.s.sss, 'SSS')
        self.assertIs(b.a, c.a)



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
        self.assertFalse(self.cdb._obj_by_id)

        self.assertIn('.attach', self.cdb.db[_id]['_attachments'])

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
        self.assertFalse(self.cdb._obj_by_id)

        self.assertIn('.attach', self.cdb.db[_id]['_attachments'])

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
    def test_uncouchable(self):
        self.cdb.store(self.cdb)

    def test_cdbCopy(self):
        obj = Simple(**self.simple_dict)

        _id = self.cdb.store(obj)

        del obj
        self.assertFalse(self.cdb._obj_by_id)

        obj = self.cdb.load(_id)

        cdbCopy = copy.deepcopy(self.cdb)

        self.assertIs(obj, cdbCopy.load(_id))


    @unittest.skip("""This fails intermittently.  I suspect a problem with the base couchdb library, but I can't pin it down yet.""")
    def test_wait(self):
        a = SimpleDoc(name='AAA')
        a_id = self.cdb.store(a)

        time.sleep(300)

        b = SimpleDoc(name='BBB', a=a)
        b_id = self.cdb.store(b)


    @unittest.skip("""still implementing tests for this feature...""")
    def test_aftermarket(self):
        pass

    @unittest.skip("""still implementing tests for this feature...""")
    def test_loadFromView(self):
        pass



    @unittest.skip("""cycles don't work ATM""")
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
            self.assertFalse(self.cdb._obj_by_id)

            a = self.cdb.load(a_id)
            b = self.cdb.load(b_id)
            c = self.cdb.load(c_id)

            self.assertIs(c.a, a)
            self.assertIs(b.a, a)
            self.assertIs(b, a.b)

        finally:
            sys.setrecursionlimit(limit)

# eof
