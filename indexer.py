#! /usr/bin/env python

from __future__ import unicode_literals

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


DEFAULT_DOCS_DIR  = 'docs'
DEFAULT_INDEX_DIR = 'docs.index'
DOC_FORMATS = ['.txt', '.pdf', '.html', '.doc', '.docx',
               '.csv', '.json', '.pptx', '.rtf', '.xls', '.xlsx']
MAX_ABSTRACT_LENGTH = 500  # characters


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


def extract_abstract(content):
    """
    Abstract is considered the first paragraph (capped to a maximum length)
    
    >>> extract_abstract('aaa\\nb')
    u'aaa'
    >>> extract_abstract('aaa\\nbbb\\nccc')  # multiple newlines
    u'aaa'
    >>> extract_abstract('aaa')  # no newline
    u'aaa'
    >>> len(extract_abstract('a' * (2 * MAX_ABSTRACT_LENGTH) + ' \\nb')) == MAX_ABSTRACT_LENGTH  # capped length 
    True
    >>> extract_abstract('\\n\\naaa\\nb')  # starts with newlines
    """
    content = unicode(content.strip(), encoding='utf-8')

    first_newline = content.find('\n')
    if first_newline == -1:  # no newlines
        first_newline = len(content)  # up to the end

    abstract = content[:first_newline]
    return abstract[:MAX_ABSTRACT_LENGTH]


def index_docs(root, writer):
    # metadata: name and path
    metadata = FieldType()
    metadata.setStored(True)  # as is value
    metadata.setTokenized(False)
    metadata.setIndexOptions(IndexOptions.DOCS_AND_FREQS)

    # content: abstract and body
    content_type = FieldType()
    content_type.setStored(True)  # to highlight on search results
    content_type.setTokenized(True)  # tokenize words
    content_type.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    for directory, _, file_names in walk(root):
        for file_name in file_names:
            name, extension = splitext(file_name)
            if extension not in DOC_FORMATS:
                continue  # skip unsupported formats

            file_path = join(directory, file_name)
            print ' ', file_path

            # Build indexed document
            doc = Document()
            doc.add(Field('name', file_name, metadata))
            doc.add(Field('path', directory, metadata))

            # Read file contents
            content = process(file_path, 'utf-8', method='pdfminer')
            abstract = extract_abstract(content)
            doc.add(Field('content',  content,  content_type))
            doc.add(Field('abstract', abstract, content_type))

            writer.addDocument(doc)


def main():
    docs_dir = DEFAULT_DOCS_DIR
    if len(argv) >= 2:
        docs_dir = argv[1]

    index_dir = DEFAULT_INDEX_DIR
    if len(argv) >= 3:
        index_dir = argv[2]

    lucene.initVM()
    build_index(docs_dir, index_dir)


if __name__ == '__main__':
    #import doctest; doctest.testmod(); exit(0)
    main()
