#! /usr/bin/env python

from os import mkdir, walk
from os.path import join, exists, splitext
from sys import argv
from textract import process

import lucene
from java.nio.file import Paths
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.document import Document, Field, FieldType

from analyzer import Analyzer


DEFAULT_DOCS_DIR =  'docs'
DEFAULT_INDEX_DIR = 'docs.index'
DOC_FORMATS = ['.txt', '.pdf', '.html', '.doc', '.docx',
               '.csv', '.json', '.pptx', '.rtf', '.xls', '.xlsx']


def build_index(docs_dir, index_dir):
    """
    Indexes files in `docs_root` recursively, placing the built index in `store_dir`
    """
    if not exists(index_dir):
        mkdir(index_dir)
    storage = SimpleFSDirectory(Paths.get(index_dir))  # index kept on disk

    config = IndexWriterConfig(Analyzer())
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)  # overwrite existing index

    writer = IndexWriter(storage, config)

    print 'Indexing documents:'
    index_docs(docs_dir, writer)

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
            name, extension = splitext(file_name)
            if extension not in DOC_FORMATS:
                continue  # skip unsupported formats

            file_path = join(directory, file_name)
            print ' ', file_path

            # Build indexed document
            doc = Document()
            doc.add(Field('name', file_name, t1))
            doc.add(Field('path', directory, t1))

            # Read file contents
            content = process(file_path, 'utf-8', method='pdfminer')
            doc.add(Field('content', content, t2))

            writer.addDocument(doc)


if __name__ == '__main__':
    docs_dir = DEFAULT_DOCS_DIR
    if len(argv) >= 2:
        docs_dir = argv[1]

    index_dir = DEFAULT_INDEX_DIR
    if len(argv) >= 3:
        index_dir = argv[2]

    lucene.initVM()
    build_index(docs_dir, index_dir)
