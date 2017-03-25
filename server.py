#! /usr/bin/env python

# from __future__ import unicode_literals

import lucene
from flask import Flask, render_template
from retriever import find_results, build_reader

app = Flask(__name__, template_folder='interface', static_folder='interface')
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')


lucene.initVM(vmargs=['-Djava.awt.headless=true'])

@app.route('/')
@app.route('/<query>')
def hello(query=None):

    if query:
        lucene.getVMEnv().attachCurrentThread()
        parsed_query, results = find_results(query, reader)
        return render_template('page.pug', parsed_query=parsed_query, results=results,
            tried_to_search=True, shown_fragments=4)

    return render_template('page.pug')


reader = build_reader()
app.run(debug=True)
