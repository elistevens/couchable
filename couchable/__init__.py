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

"""
The public API of couchable consists of:
    - L{CouchableDb}: The core DB wrapper/access object.
    - L{packer}:, L{unpacker}: Extends the list of built-in or C types supported.
    - L{registerDocType}:, L{CouchableDoc}: For adding new document classes.
    - L{registerAttachmentType}:, L{CouchableAttachment}: For adding classes to store as attachments.
    - L{doGzip}:, L{doGunzip}: Helper functions for compressing attachments.
    - L{newid}: Helper function to make document IDs readable.
    
The source for couchable lives at:
    - U{http://github.com/wickedgrey/couchable}
    
For the time being, please use the github issue tracker for bugs:
    - U{http://github.com/wickedgrey/couchable/issues}

--README.txt--
"""

from core import CouchableDb
from core import registerDocType, CouchableDoc
from core import registerAttachmentType, CouchableAttachment
from core import packer, unpacker
from core import doGzip, doGunzip
from core import newid
