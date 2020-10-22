from flask import Flask, g, Blueprint, send_from_directory, after_this_request, current_app, jsonify, render_template_string,request
import argparse
import functools
import gzip
import sys
from io import StringIO
from urllib.parse import unquote, unquote_plus
import redis
from redisgraph import Graph

def cypher_quote(value):
   return value.replace('\n',r'\n').replace("'",r"\'")

def gzipped(f):
   @functools.wraps(f)
   def view_func(*args, **kwargs):
      @after_this_request
      def zipper(response):
         if not current_app.config.get('COMPRESS'):
            return response

         accept_encoding = request.headers.get('Accept-Encoding', '')

         if 'gzip' not in accept_encoding.lower():
            return response

         response.direct_passthrough = False

         if (response.status_code < 200 or
             response.status_code >= 300 or
             'Content-Encoding' in response.headers):
            return response
         gzip_buffer = BytesIO()
         gzip_file = gzip.GzipFile(mode='wb',
                                   fileobj=gzip_buffer)
         gzip_file.write(response.data)
         gzip_file.close()

         response.data = gzip_buffer.getvalue()
         response.headers['Content-Encoding'] = 'gzip'
         response.headers['Vary'] = 'Accept-Encoding'
         response.headers['Content-Length'] = len(response.data)

         return response

      return f(*args, **kwargs)

   return view_func

def get_graph(name):
   if 'graphs' not in g:
      g.graphs = {}
   if name not in g.graphs:
      r = redis.Redis(host=current_app.config['REDIS_HOST'],port=int(current_app.config['REDIS_PORT']),password=current_app.config.get('REDIS_PASSWORD'))
      g.graphs[name] = Graph(name,r)
   return g.graphs[name]

assets = Blueprint('viewer_assets',__name__)
@assets.route('/<path:path>')
@gzipped
def send_asset(path):
   dir = current_app.config.get('ASSETS')
   if dir is None:
      last = __file__.rfind('/')
      dir = (__file__[:last] if last>=0 else '.') + '/assets/'
   return send_from_directory(dir, path)

def generate_template(config,base):
   options = config.get('TEMPLATE_OPTIONS')
   output = StringIO()
   output.write('{{% extends "{}" %}}\n'.format(base))
   if options is not None:
      for name in options:
         output.write('{{% block {} %}}\n'.format(name))
         output.write(options[name])
         output.write('\n{% endblock %}\n')
   return output.getvalue()

viewer = Blueprint('viewer',__name__,template_folder='templates')

@viewer.route('/')
@gzipped
def index():
   return render_template_string(
         generate_template(current_app.config,'base.html'))

data = Blueprint('data',__name__,template_folder='templates')

@data.route('/datasets')
@gzipped
def datasets():
   return jsonify(current_app.config['GRAPH'])

@data.route('/articles')
@gzipped
def articles():
   articles = []
   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   word = request.args.get('word')
   types = request.args.getlist('type')
   if types is None or len(types)==0:
      types = set(['keyword','entity'])
   else:
      types = set(types)
   year = request.args.get('year')
   graph = get_graph(dataset)
   if year is None and word is not None:
      if 'keyword' in types:
         keyword_articles = graph.query("match (a)-[:keyword]->(k:Keyword {{text: '{word}'}}) return a.url,a.headline,a.datePublished,a.description".format(word=cypher_quote(word)))
      else:
         keyword_articles = []
      if 'entity' in types:
         entity_articles = graph.query("match (a)-[:uses]->(e:NamedEntity {{text: '{word}'}}) return a.url,a.headline,a.datePublished,a.description".format(word=cypher_quote(word)))
      else:
         entity_articles = []
      articles = list(map(lambda item : {'url':item[0],'headline': item[1],'datePublished' : item[2],'description' : item[3]},keyword_articles.result_set + entity_articles.result_set))
   if year is not None:
      if keyword is None:
         pass
      else:
         pass
   return jsonify(articles)

@data.route('/keywords')
@gzipped
def keywords():

   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   start = request.args.get('start')
   end = request.args.get('end')
   in_year = request.args.get('in')

   graph = get_graph(dataset)
   query = StringIO()
   query.write('match (a)-[:keyword]->(k:Keyword)\n')
   clause = 'where'
   if start is not None:
      query.write("{clause} a.datePublished >= '{start}'\n".format(clause=clause,start=start))
      clause = 'and'
   if end is not None:
      query.write("{clause} a.datePublished <= '{end}'\n".format(clause=clause,end=end))
      clause = 'and'
   if in_year is not None:
      query.write("{clause} a.datePublished starts with '{in_year}'\n".format(clause=clause,in_year=in_year))
      clause = 'and'
   query.write('return k.text,count(a)')
   result = graph.query(query.getvalue())
   keywords = list(map(lambda item : {'text':item[0],'count':int(item[1])},result.result_set))
   return jsonify(keywords)

@data.route('/entities')
@gzipped
def entities():

   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]

   start = request.args.get('start')
   end = request.args.get('end')
   in_year = request.args.get('in')

   graph = get_graph(dataset)
   query = StringIO()
   query.write('match (a)-[u:uses]->(e:NamedEntity)\n')
   clause = 'where'
   if start is not None:
      query.write("{clause} a.datePublished >= '{start}'\n".format(clause=clause,start=start))
      clause = 'and'
   if end is not None:
      query.write("{clause} a.datePublished <= '{end}'\n".format(clause=clause,end=end))
      clause = 'and'
   if in_year is not None:
      query.write("{clause} a.datePublished starts with '{in_year}'\n".format(clause=clause,in_year=in_year))
      clause = 'and'
   query.write('return e.text,count(a),sum(u.count)')
   result = graph.query(query.getvalue())
   keywords = list(map(lambda item : {'text':item[0],'articles':int(item[1]),'count':int(item[2])},result.result_set))
   return jsonify(keywords)

def cooccurrences_result(result):
   positions = {}
   keywords = []
   for item in result.result_set:
      first_pos = positions.get(item[0],-1)
      if first_pos<0:
         first_pos = len(keywords)
         keywords.append({'name':item[0],'index':first_pos,'occurs_with':[]})
         positions[item[0]] = first_pos
      second_pos = positions.get(item[1],-1)
      if second_pos<0:
         second_pos = len(keywords)
         keywords.append({'name':item[1],'index':second_pos,'occurs_with':[]})
         positions[item[1]] = second_pos
      try:
         keywords[first_pos]['occurs_with'].index(second_pos)
      except ValueError:
         keywords[first_pos]['occurs_with'].append(second_pos)
      try:
         keywords[second_pos]['occurs_with'].index(first_pos)
      except ValueError:
         keywords[second_pos]['occurs_with'].append(first_pos)
   return jsonify(keywords)


@data.route('/keywords/cooccurrences')
@gzipped
def keyword_cooccurrences():

   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   graph = get_graph(dataset)
   result = graph.query('match (k1:Keyword)<-[:keyword]-(a)-[:keyword]->(k2:Keyword) where k1 <> k2 return k1.text, k2.text')

   return cooccurrences_result(result)

@data.route('/entities/cooccurrences')
@gzipped
def entity_cooccurrences():

   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   graph = get_graph(dataset)
   result = graph.query('match (e1:NamedEntity)<-[:uses]-(a)-[:uses]->(e2:NamedEntity) where e1 <> e2 return e1.text, e2.text')

   return cooccurrences_result(result)

@data.route('/search')
@gzipped
def search():
   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   graph = get_graph(dataset)
   q = request.args.get('q')

   if q is None:
      return jsonify({'error' : "Missing required 'q' parameter."}),400

   query = """
CALL db.idx.fulltext.queryNodes('BlogPosting', '{query}') YIELD node
RETURN node.url,node.headline,node.datePublished,node.description
""".format(query=cypher_quote(q))

   result = graph.query(query)
   articles = list(map(lambda item : {'url':item[0],'headline': item[1],'datePublished' : item[2],'description' : item[3]},result.result_set))

   query = """
CALL db.idx.fulltext.queryNodes('BlogPosting', '{query}') YIELD node
MATCH (node)-[u:uses]->(e:NamedEntity)
RETURN e.text,count(node),sum(u.count)
""".format(query=cypher_quote(q))

   result = graph.query(query)
   entities = list(map(lambda item : {'text':item[0],'articles':int(item[1]),'count':int(item[2])},result.result_set))

   return jsonify({'articles' : articles, 'entities' : entities})


def create_app(host='0.0.0.0',port=6379,graph='test',password=None,app=None,config=None):
   if app is None:
      app = Flask(__name__)
   if password is not None and len(password)==0:
      password = None
   app.register_blueprint(viewer)
   app.register_blueprint(assets,url_prefix='/assets')
   app.register_blueprint(data,url_prefix='/data')
   if config is not None:
      import os
      app.config.from_pyfile(os.path.abspath(config))
   if 'REDIS_HOST' not in app.config:
      app.config['REDIS_HOST'] = host
   if 'REDIS_PORT' not in app.config:
      app.config['REDIS_PORT'] = port
   if 'REDIS_PASSWORD' not in app.config:
      app.config['REDIS_PASSWORD'] = password
   if 'GRAPH' not in app.config:
      app.config['GRAPH'] = graph
   return app

def main(call_args=None):
   argparser = argparse.ArgumentParser(description='Web')
   argparser.add_argument('--host',help='Redis host',default='0.0.0.0')
   argparser.add_argument('--port',help='Redis port',type=int,default=6379)
   argparser.add_argument('--password',help='Redis password')
   argparser.add_argument('--config',help='configuration file')
   argparser.add_argument('--debug',help='Turns on debug',action='store_true',default=False)
   argparser.add_argument('graph',nargs='+',help='The graph name')
   args = argparser.parse_args(call_args if call_args is not None else sys.argv[1:])

   app = create_app(host=args.host,port=args.port,password=args.password,graph=args.graph,config=args.config)
   if args.debug:
      app.config['DEBUG'] = True
   app.run(host='0.0.0.0')

if __name__ == '__main__':
   main()
