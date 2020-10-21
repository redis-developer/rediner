import argparse
import yaml
import os
import sys
import itertools

from .ner import extract_entities

def indexer(prefix):
   counter = itertools.count()
   for count in counter:
      yield prefix + str(count)


def apply_ner_to_file(file,is_yaml=False,source_indexer=indexer('source'),term_indexer=indexer('term'),output=sys.stdout,**kwargs):
   sid = None
   if yaml:
      with open(file) as yaml_source:
         article = yaml.load(yaml_source,Loader=yaml.Loader)
         for key in article.keys():
            node = article[key]
            if 'articleBody' in node:
               sid = node.get('@id')
               text = node['articleBody']
               break
   else:
      with open(file) as text_source:
         text = text_source.read()

   entities = extract_entities(text,**kwargs)

   if len(entities)==0:
      return

   graph = {}
   snode = None
   if sid is not None:
      snode = {
         '@id' : sid,
         ':uses' : []
      }
      graph[next(source_indexer)] = snode

   for term in entities.keys():
      tid = next(term_indexer)
      info = entities[term]
      graph[tid] = {
         '~label' : 'NamedEntity',
         'text' : term,
         'types' : ','.join(info['types'])
      }
      if snode is not None:
         snode[':uses'].append({
            '~to' : tid,
            'count' : info['count'],
         })

   print(yaml.dump(graph),file=output)

      #print('{term} = {count}, {labels}'.format(term=term,count=info['count'],labels=', '.join(info['types'])))

def enumerate_files(files,extension='txt',recurse=False):
   for file in files:
      if os.path.isdir(file):
         if recurse:
            prefix_len = len(file)
            for root, dirs, files in os.walk(file):
               for item in files:
                  current_path = root[prefix_len:]
                  if len(current_path)>0:
                     current_path += os.sep

                  fparts = item.rsplit('.',1)
                  if fparts[-1]==args.extension:
                     yield root + os.sep + item
         else:
            for item in os.listdir(file):
               fparts = item.rsplit('.',1)
               if fparts[-1]==args.extension:
                  yield file + os.sep + item
      else:
         yield file

schema = \
"""
~schema: |
  (:NamedEntity {text})
"""

if __name__ == '__main__':
   argparser = argparse.ArgumentParser(description='NER model')
   argparser.add_argument('--verbose',help='Output debugging trace',action='store_true',default=False)
   argparser.add_argument('--yaml',help='Treat input as schema.org in YAML format',action='store_true',default=False)
   argparser.add_argument('--check-boundaries',help='Check for entities across boundaries',action='store_true',default=False)
   argparser.add_argument('--strip-starting-stop-words',help='Strip starting stop works',action='store_true',default=False)
   argparser.add_argument('--extension',nargs='?',help='The file extension search for in the directory')
   argparser.add_argument('-r','--recurse',help='Recurse through the directories',action='store_true',default=False)
   argparser.add_argument('--host',help='Redis host',default='0.0.0.0')
   argparser.add_argument('--port',help='Redis port',type=int,default=6379)
   argparser.add_argument('--password',help='Redis password')
   argparser.add_argument('--graph',help='The graph name',default='test')
   argparser.add_argument('action',help='The action to perform',choices=['ner', 'load'])
   argparser.add_argument('files',nargs='+',help='A list of text files or directories to process')
   args = argparser.parse_args()


   if args.action=='ner':
      if args.extension is None:
         args.extension = 'yaml' if args.yaml else 'txt'
      source_indexer = indexer('source')
      term_indexer = indexer('term')
      def apply_ner(file):
         apply_ner_to_file(
            file,
            is_yaml=args.yaml,
            source_indexer=source_indexer,
            term_indexer=term_indexer,
            check_boundaries=args.check_boundaries,
            strip_starting_stop_words=args.strip_starting_stop_words)
      action = apply_ner
      print(schema)
   elif args.action=='load':
      if args.extension is None:
         args.extension = 'yaml'
      import redis
      from redisgraph import Graph
      from propgraph import read_graph, cypher_for_item
      r = redis.Redis(host=args.host,port=args.port,password=args.password)
      graph = Graph(args.graph,r)
      def load_file(file):
         with open(file,'r') as input:
            for item in read_graph(input,format='yaml',infer=True):
               query = cypher_for_item(item)
               if query is None:
                  continue
               try:
                  graph.query(query)
               except redis.exceptions.ResponseError as err:
                  print('Failed query:',file=sys.stderr)
                  print(query,file=sys.stderr)
                  raise err
      action = load_file

   for file in enumerate_files(args.files,extension=args.extension,recurse=args.recurse):
      action(file)
