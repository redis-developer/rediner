from flask import Flask, g, Blueprint, send_from_directory, after_this_request, current_app, jsonify, render_template_string,request
import argparse
import functools
import gzip
import sys
import os
from io import StringIO
from urllib.parse import unquote, unquote_plus
import redis
from redisgraph import Graph
import time

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

@data.route('/distribution')
@gzipped
def distribution():
   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   graph = get_graph(dataset)
   summary = graph.query('MATCH (a)-[u:uses]->(e:NamedEntity) RETURN e.text,sum(u.count)')
   distribution = {}
   for item in summary.result_set:
      if item[1] in distribution:
         distribution[item[1]] += 1
      else:
         distribution[item[1]] = 1
   return jsonify(distribution)
   # summary = graph.query('MATCH (a)-[u:uses]->(e:NamedEntity) RETURN e.text,count(a),sum(u.count)')
   # distribution = {}
   #
   # article_count = 0
   # use_count = 0
   # article_counts = []
   # for item in summary.result_set:
   #    rate = round(item[2]/item[1])
   #    article_count += item[1]
   #    use_count += item[2]
   #    if rate in distribution:
   #       distribution[rate]['articles'] += item[1]
   #       distribution[rate]['count'] += item[2]
   #       distribution[rate]['entities'].append(item[0])
   #    else:
   #       distribution[rate] = {
   #          'rate' : rate,
   #          'articles' : item[1],
   #          'count' : item[2],
   #          'entities' : [item[0]]
   #       }
   #
   # result = []
   # for rate in sorted(distribution.keys()):
   #    info = distribution[rate]
   #    result.append(info)

   # articles = [distribution[rate]['articles'] for rate in sorted(distribution.keys()) ]
   # print((article_count,use_count,round(use_count/float(article_count))))
   # print(articles)
   # from statistics import stdev, quantiles
   # print(stdev(articles))
   # print(quantiles(articles,n=2))

   #return jsonify(result)

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
   query.write('return id(e),e.text,count(a),sum(u.count)')
   result = graph.query(query.getvalue())
   keywords = list(map(lambda item : {'id':item[0],'text':item[1],'articles':int(item[2]),'count':int(item[3])},result.result_set))
   return jsonify(keywords)

def cooccurrences_result(result,positions={},keywords=[]):
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
   return positions, keywords


@data.route('/keywords/cooccurrences')
@gzipped
def keyword_cooccurrences():

   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   graph = get_graph(dataset)
   result = graph.query('match (k1:Keyword)<-[:keyword]-(a)-[:keyword]->(k2:Keyword) where k1 <> k2 return k1.text, k2.text')

   _, keywords = cooccurrences_result(result)
   return jsonify(keywords)

@data.route('/entities/cooccurrences',methods=['GET','POST'])
@gzipped
def entity_cooccurrences():

   dataset = request.args.get('dataset')
   if dataset is None:
      dataset = current_app.config['GRAPH'][0]
   graph = get_graph(dataset)


   if request.method=='POST':
      if not request.is_json:
         return jsonify({'error' : "The data is not JSON: "+request.content_type}),400
      if type(request.json)!=list:
         return jsonify({'error' : "The data must be an array of entities."}),400
      article_count = request.args.get('count')
      same_article = request.args.get('same','false')=='true'
      positions = {}
      # entities = []
      matrix = []
      words = request.json
      for index,text in enumerate(words):
         positions[text] = index
         matrix.append([0] * len(request.json))

      batch_size = 250
      for block in [words[i:i + batch_size] for i in range(0, len(words), batch_size)]:
         query = StringIO()
         if same_article:
            query.write('MATCH (e1:NamedEntity)<-[:uses]-(a)-[:uses]->(e2:NamedEntity) WITH e1, e2, count(a) as a_count WHERE e1 <> e2 ')
            if article_count is not None:
               article_count = int(article_count)
               if article_count > 1:
                  query.write(' AND a_count>={} '.format(article_count))
         else:
            query.write('MATCH (a1)-[:uses]->(e1:NamedEntity)<-[:uses]-(a2)-[:uses]->(e2:NamedEntity)<-[:uses]-(a1) WHERE a1 <> a2 and e1 <> e2 ')
         query.write(' AND (')
         for index, text in enumerate(block):
            if index > 0:
               query.write(' OR ')
            query.write("e1.text='{}'".format(cypher_quote(text)))
         query.write(') RETURN e1.text,e2.text')

         if not same_article:
            query.write(',count(a1)')
         q = query.getvalue()
         start = time.time()
         result = graph.query(q)
         elapsed = time.time() - start
         print(elapsed)

         # TODO: do we include other words that are in the list?
         for item in result.result_set:
            row, col = positions[item[0]], positions.get(item[1],-1)
            if col<0:
               continue
               # col = len(matrix[0])
               # for r in matrix:
               #    r.append(0)
               # matrix.append([0]*(col+1))
               # words.append(word)
            matrix[row][col] = 1
            matrix[col][row] = 1

         # cooccurrences_result(result,positions=positions,keywords=entities)

      return jsonify(matrix)

   else:
      minimum = request.args.get('minimum')
      if minimum is not None:
         minimum = int(minimum)
         query = """
MATCH (a)-[u:uses]->(e) WITH e, sum(u.count) AS use_count WHERE use_count >= {minimum}
MATCH (e:NamedEntity)<-[:uses]-()-[:uses]->(e2:NamedEntity) WHERE e <> e2
RETURN e.text, e2.text""".format(minimum=minimum)
      else:
         start = request.args.get('start')
         limit = request.args.get('limit')
         query = 'MATCH (e1:NamedEntity)<-[:uses]-(a)-[:uses]->(e2:NamedEntity) WHERE e1 <> e2 return e1.text, e2.text'
         if limit is not None:
            if start is None:
               start = 0
            start = int(start)
            limit = int(limit)
            query += ' ORDER BY e1.text SKIP {start} LIMIT {limit}'.format(start=start,limit=limit)

      result = graph.query(query)

      _, entities = cooccurrences_result(result)
      return jsonify(entities)

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

def from_env(name,default_value,dtype=str,action=lambda x : x):
   return action(dtype(os.environ[name]) if name in os.environ else default_value)

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
      app.config['REDIS_HOST'] = from_env('REDIS_HOST',host)
   if 'REDIS_PORT' not in app.config:
      app.config['REDIS_PORT'] = from_env('REDIS_PORT',port,dtype=int)
   if 'REDIS_PASSWORD' not in app.config:
      app.config['REDIS_PASSWORD'] = from_env('REDIS_PASSWORD',password)
   if 'GRAPH' not in app.config:
      app.config['GRAPH'] = from_env('GRAPH',graph,action=lambda x : x.split(',') if type(x)==str else x)
   return app

class Config(object):
   DEBUG=True
   REDIS_HOST = from_env('REDIS_HOST','0.0.0.0')
   REDIS_PORT = from_env('REDIS_PORT',6379,dtype=int)
   REDIS_PASSWORD = from_env('REDIS_PASSWORD',None)
   GRAPH = from_env('GRAPH',['test'],action=lambda x : x.split(',') if type(x)==str else x)

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
