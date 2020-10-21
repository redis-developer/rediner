import argparse
import redis
from redisgraph import Graph

def main(call_args=None):

   argparser = argparse.ArgumentParser(description='Database Setup')
   argparser.add_argument('--host',help='Redis host',default='0.0.0.0')
   argparser.add_argument('--port',help='Redis port',type=int,default=6379)
   argparser.add_argument('--password',help='Redis password')
   argparser.add_argument('graphs',nargs='+',help='Graphs to setup')

   args = argparser.parse_args()

   r = redis.Redis(host=args.host,port=args.port,password=args.password)
   for name in args.graphs:
      g = Graph(name,r)

      g.query('CREATE INDEX ON :BlogPosting(keywords)')
      g.query('CALL db.idx.fulltext.createNodeIndex("BlogPosting","keywords")')
      g.query('CALL db.idx.fulltext.createNodeIndex("BlogPosting","headline")')
      g.query('CALL db.idx.fulltext.createNodeIndex("BlogPosting","description")')
      g.query('CALL db.idx.fulltext.createNodeIndex("BlogPosting","articleBody")')

if __name__ == '__main__':
   main()
