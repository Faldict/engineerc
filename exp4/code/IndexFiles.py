#!/usr/bin/env python

INDEX_DIR = "IndexFiles.index"

import jieba
import sys, os, lucene, threading, time
from datetime import datetime
import BeautifulSoup

from java.io import File
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

"""
This class is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.IndexFiles.  It will take a directory as an argument
and will index all of the files in that directory and downward recursively.
It will index on the file path, the file name and the file contents.  The
resulting Lucene index will be placed in the current directory and called
'index'.
"""

def analysis(s):
    return ' '.join(jieba.cut(s))

class Ticker(object):

    def __init__(self):
        self.tick = True

    def run(self):
        while self.tick:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.0)

class IndexFiles(object):
    """Usage: python IndexFiles <doc_directory>"""

    def __init__(self, dialog, root, storeDir, analyzer):

        if not os.path.exists(storeDir):
            os.mkdir(storeDir)

        store = SimpleFSDirectory(File(storeDir))
        analyzer = LimitTokenCountAnalyzer(analyzer, 1048576)
        config = IndexWriterConfig(Version.LUCENE_CURRENT, analyzer)
        config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
        writer = IndexWriter(store, config)

        self.indexDocs(dialog, root, writer)
        ticker = Ticker()
        print 'commit index',
        threading.Thread(target=ticker.run).start()
        writer.commit()
        writer.close()
        ticker.tick = False
        print 'done'

    def indexDocs(self, dialog, root, writer):

        t1 = FieldType()
        t1.setIndexed(True)
        t1.setStored(True)
        t1.setTokenized(False)
        t1.setIndexOptions(FieldInfo.IndexOptions.DOCS_AND_FREQS)

        t2 = FieldType()
        t2.setIndexed(True)
        t2.setStored(False)
        t2.setTokenized(True)
        t2.setIndexOptions(FieldInfo.IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

        f = open(dialog)
        lines = f.readlines()
        for line in lines:
            info = line.split('\t')
            url = info[0]
            filename = info[1]
            title = info[2]
            print "adding", filename
            try:
                path = os.path.join(root, filename)
                file = open(path)
                contents = unicode(file.read(), 'utf-8')
                file.close()
                doc = Document()
                doc.add(Field('name', filename, t1))
                doc.add(Field('path', path, t1))
                doc.add(Field('url', url, Field.Store.YES, Field.Index.NOT_ANALYZED))
                if len(contents)>0:
                    soup=BeautifulSoup(contents)
                    try:
                        title = soup.title.text
                        doc.add(Field('title', title, Field.Store.YES, Field.Index.ANALYZED))
                    except Exception, e:
                        doc.add(Field('title', 'none', Field.Store.YES, Field.Index.ANALYZED))
                    contents = ''.join(soup.findAll(text=True))                       
                    doc.add(Field("contents", analysis(contents), t2))
                else:
                    print "warning: no content in %s" % filename
                writer.addDocument(doc)
            except Exception, e:
                print "Failed in indexDocs:", e

if __name__ == '__main__':
    """
    if len(sys.argv) < 2:
        print IndexFiles.__doc__
        sys.exit(1)
    """
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    print 'lucene', lucene.VERSION
    start = datetime.now()
    try:
        """
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        IndexFiles(sys.argv[1], os.path.join(base_dir, INDEX_DIR),
                   StandardAnalyzer(Version.LUCENE_CURRENT))
                   """
        analyzer = WhitespaceAnalyzer(Version.LUCENE_CURRENT)
        IndexFiles('index.txt', "html", "index", analyzer)
        end = datetime.now()
        print end - start
    except Exception, e:
        print "Failed: ", e
        raise e
