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
import doctest
import gc
import random
import sys
import time
import unittest

# 3rd party packages
import couchdb

# in-house
#import couchable
#import couchable.core

class TestCouchdb(unittest.TestCase):
    def setUp(self):
        self.server = couchdb.Server()
        try:
            self.server.delete('testing')
            pass
        except:
            pass
        
        self.db = self.server.create('testing')
        
        
    def tearDown(self):
        del self.db
        del self.server


    @unittest.skip('''Haven't been able to get a clean testcase repro yet.''')
    def test_wait(self):
        a = {'name':'AAA'}
        #a['_id'], a['_rev'] = self.db.save(a)
        self.db.update([a])


        time.sleep(300)
        
        b = {'name':'BBB'}
        self.db.update([b])

    
# eof
