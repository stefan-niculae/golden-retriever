#! /usr/local/bin/python

from os import getcwd, mkdir, walk
from os.path import join, exists
from sys import argv

import lucene
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.document import Document, Field, FieldType

from analyzer import build_analyzer


INDEX_LOCATION = 'documents.index'


def build_index(docs_root, store_dir):
    """
    Indexes files in `docs_root` recursively, placing the built index in `store_dir`
    """
    if not exists(store_dir):
        mkdir(store_dir)
    storage = SimpleFSDirectory(Paths.get(store_dir))  # index kept on disk

    config = IndexWriterConfig(build_analyzer())
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)  # overwrite existing index

    writer = IndexWriter(storage, config)

    print 'Indexing documents:'
    index_docs(docs_root, writer)

    print 'Writing index...'
    writer.commit()
    writer.close()


def index_docs(root, writer):
    # name and path
    t1 = FieldType()
    t1.setStored(True)  # as is value
    t1.setTokenized(False)
    t1.setIndexOptions(IndexOptions.DOCS_AND_FREQS)

    # content
    t2 = FieldType()
    t2.setStored(True)  # to highlight on search results
    t2.setTokenized(True)  # tokenize words
    t2.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    for directory, _, file_names in walk(root):
        for file_name in file_names:
            if not file_name.endswith('.txt'):
                # TODO: other formats
                continue
            print ' ', file_name

            # Read file contents
            doc_path = join(directory, file_name)
            with open(doc_path) as file:
                contents = unicode(file.read(), 'utf-8')  # TODO: diacritics

            # Build indexed document
            doc = Document()
            doc.add(Field('name', file_name, t1))
            doc.add(Field('path', directory, t1))
            doc.add(Field('content', contents, t2))
            writer.addDocument(doc)


if __name__ == '__main__':
    if len(argv) < 2:
        print 'usage: indexer.py <documents-folder>'
        exit(1)

    lucene.initVM()

    build_index(docs_root=argv[1],
                store_dir=join(getcwd(), INDEX_LOCATION))
