#! /usr/bin/env python

import lucene
from flask import Flask, render_template
from retriever import find_results, build_searcher

app = Flask(__name__, template_folder='interface', static_folder='interface')
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')


lucene.initVM(vmargs=['-Djava.awt.headless=true'])

@app.route('/')
@app.route('/<query>')
def hello(query=None):

    if query:
        lucene.getVMEnv().attachCurrentThread()
        parsed_query, results = find_results(query, searcher)
        parsed_query = unicode(parsed_query).replace('content:', '')
        return render_template('page.pug', parsed_query=parsed_query, results=results, tried_to_search=True)

    return render_template('page.pug')



searcher = build_searcher()
app.run(debug=True)
