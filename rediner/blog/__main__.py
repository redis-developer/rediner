import argparse
import yaml
import sys
import os
import lxml


from .reader import blog_entry_pages, get_document

from .entry import harvest_entry

def same_page(url,document):
   return document

def load_page(url,document):
   return get_document(url)

authors = {}
author_count = 0

def author_indexer(author_id):
   global authors
   global author_count
   label = authors.get(author_id)
   if label is not None:
      return label, False
   label = 'author' + str(author_count)
   authors[author_id] = label
   author_count += 1
   return label, True

if __name__ == '__main__':
   argparser = argparse.ArgumentParser(description='Article importer')
   argparser.add_argument('--verbose',help='Output debugging trace',action='store_true',default=False)
   argparser.add_argument('--entry',action='append',help='A pattern for find the blog entry on the page.')
   argparser.add_argument('--next',action='append',help='A pattern for find the next entry link on the page.')
   argparser.add_argument('--url-only',help='Output a list of urls of entry pages instead of entries.',action='store_true',default=False)
   argparser.add_argument('--same',help='The article is on the same page.',action='store_true',default=False)
   argparser.add_argument('--entry-container',action='append',nargs='?',help='The pattern to find the articleBody')
   argparser.add_argument('--remove',action='append',nargs='?',help='A pattern of elements to remove from content')
   argparser.add_argument('--include-body',help='Include the article body in the cypher',action='store_true',default=False)
   argparser.add_argument('--full-types',help='Output all the type labels',action='store_true',default=False)
   argparser.add_argument('--extension',nargs='?',help='The output file extension',default='yaml')
   argparser.add_argument('--stub',nargs='?',help='The output file stub',default='article')
   argparser.add_argument('--dir',nargs='?',help='The output directory')
   argparser.add_argument('--store',help='Store the output in separate files',action='store_true',default=False)
   argparser.add_argument('urls',nargs='*',help='A list of starting urls',default=['https://redislabs.com/company-blog/','https://redislabs.com/tech-blog/'])
   args = argparser.parse_args()

   kwargs = {}
   if args.entry is not None:
      kwargs['entries'] = args.entry
   if args.next is not None:
      kwargs['next'] = args.next

   if args.same:
      kwargs['action'] = same_page
   elif not args.url_only:
      kwargs['action'] = load_page

   harvest_kwargs = {}
   if args.entry_container is not None and len(args.entry_container)>0:
      harvest_kwargs['entry_containers'] = args.entry_container
   if args.remove is not None and len(args.remove)>0:
      harvest_kwargs['entry_remove'] = args.remove

   if not args.store:
      harvest_kwargs['author_indexer'] = author_indexer


   count = 0
   for url, document in blog_entry_pages(*args.urls,verbose=args.verbose,**kwargs):
      if args.url_only:
         print(url)
      else:
         try:
            entry = harvest_entry(url,document,leaf=not args.full_types,verbose=args.verbose,id='entry'+str(count+1),**harvest_kwargs)
            count += 1
         except lxml.etree.ParserError:
            print('Cannot parse: '+url,file=sys.stderr)
            continue
         if entry is None:
            print('No entry found: '+url,file=sys.stderr)
            continue

         if not args.store:
            output = sys.stdout
         else:
            file = args.stub + str(count) + '.' + args.extension
            if args.dir is not None:
               if args.dir[-1]==os.sep:
                  file = args.dir + file
               else:
                  file = args.dir + os.sep + file
            output = open(file,'w')
            if args.verbose:
               print(url + ' → ' + file,file=sys.stderr)

         print(yaml.dump(entry),file=output)

         if args.store:
            output.close()
