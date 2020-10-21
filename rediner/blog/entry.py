from pyquery import PyQuery as pq
import json
import argparse
import re
import requests
import yaml
import sys
import dateparser
import os

requests.packages.urllib3.disable_warnings()


# https://stackoverflow.com/a/49146722/330558
emoji_pattern = re.compile("["
   u"\U0001F600-\U0001F64F"  # emoticons
   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
   u"\U0001F680-\U0001F6FF"  # transport & map symbols
   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
   u"\U00002702-\U000027B0"
   u"\U000024C2-\U0001F251"
   "]+", flags=re.UNICODE)
def remove_emoji(string):
   return emoji_pattern.sub(r'', string)

blogType = ['Thing','CreativeWork','Article','SocialMediaPosting','BlogPosting']
keywordType = ['Thing','Keyword']
mediaType = ['Thing','CreativeWork','MediaObject']
personType = ['Thing','Person']
profilePageType = ['Thing','CreativeWork','WebPage','ProfilePage']

def typeLabel(typePath,leaf=False):
   if leaf:
      return typePath[-1]
   else:
      return ':'.join(typePath)


def set_property(properties,name,value):
   if value is not None:
      properties[name] = value

def create_node(node_type,*args,**pairs):
   properties = { '@type' : node_type } if node_type is not None else {}
   for arg in args:
      if type(arg)==dict:
         for name, value in arg.items():
            set_property(properties,name,value)
      elif type(arg)==tuple and len(arg)==2:
         set_property(properties,arg[0],arg[1])
      else:
         raise ValueError('Unable to process argument {type} : {value}'.format(type=type(arg),value=str(arg)))
   for name,value in pairs.items():
      set_property(properties,name,value)
   return properties

def get_edges(node):
   edges = node.get('~edges')
   if edges is None:
      edges = []
      node['~edges'] = edges
   return edges

def harvest_entry(url,d,id='entry',author_indexer=None,leaf=True,verbose=False,tag_override=False,entry_containers=['article.post','article[resource]','article','body'],entry_text='p',entry_remove=['pre','code', 'section.info']):

   if verbose:
      print('Harvesting from '+url,file=sys.stderr)

   # Find the JSON-LD description
   ld_text = d('script[type="application/ld+json"]').text()
   if len(ld_text)==0:
      raise ValueError('Cannot retrieve JSON/LD from entry for {url}'.format(url=url))

   # Load it into JSON
   # TODO: This really should apply a JSON-LD processor
   try:
      ld = json.loads(ld_text)
   except json.decoder.JSONDecodeError:
      raise ValueError('Cannot decode JSON/LD from entry for {url}'.format(url=url))

   # Process all the meta[property] tags into a dictionary with array values
   properties = {}
   for meta in d('meta[property]'):
      name = meta.attrib['property']
      content = meta.attrib['content']
      values = properties.get(name,[])
      values.append(content)
      properties[name] = values

   # We may have the LD in a graph
   nodes = {}
   article = None
   if '@graph' in ld:
      webpage = None
      for item in ld['@graph']:
         oid = item['@id']
         otype = item['@type']
         nodes[oid] = item
         if otype=='Article':
            article = item
         if otype=='WebPage':
            webpage = item
      if article is None:
         article = webpage
   else:
      article = ld

   # If the JSON-LD contains no article, we don't have a blog entry described
   if article is None:
      return None

   # Either use the article:tag property values or the 'keywords' property from the JSON-LD
   keywords = properties.get('article:tag',[]) if tag_override else (article.get('keywords').split(',') if 'keywords' in article else [])
   # check for an empty string as the only keyword
   if len(keywords)==1 and keywords[0]=='':
      keywords = None

   if 'image' in article:
      image = article['image']

      # Resolve the article image into a simple URL
      if type(image)==dict:
         id = image.get('@id')
         image = image.get('url')
         if id is not None:
            image_object = nodes.get(id)
            if image_object is not None:
               image = image_object.get('url')
   else:
      # Maybe we have an image in the meta properties
      image = properties.get('og:image',[None])[0]

   # Process the content of the article

   content = None
   for entry_container in entry_containers:
      if len(d(entry_container))>0:
         for remove_spec in entry_remove:
            d(entry_container+' '+remove_spec).remove()
         content = d(entry_container+' '+entry_text).text()
         break;

   if 'name' in article and 'headline' not in article:
      article['headline'] = article['name']

   # We need to have at least a headline for the article
   if 'headline' not in article:
      return None

   articleNode = create_node(
      typeLabel(blogType,leaf=leaf),
      {
            '@id' : article.get('@id',article.get('url',url)),
            'headline' : article['headline']
      },
      url=url,
      description=article.get('description'),
      datePublished=article.get('datePublished',article.get('datepublished',None)),
      dateModified=article.get('dateModified',article.get('datemodified',None)),
      articleSection=article.get('articleSection',None),
      image=image,
      articleBody=content
   )

   # Normalize dates
   for name in ['datePublished','dateModified']:
      if name in articleNode:
         articleNode[name] = dateparser.parse(articleNode[name]).astimezone().isoformat()

   if keywords is not None:
      articleNode['keywords'] = ','.join(keywords)

   graph = {id : articleNode}

   author_index = 0
   for spec in article['author'] if type(article['author'])==list else [article['author']]:
      if '@id' in spec and '@type' not in spec:
         author = nodes.get(spec['@id'])
      else:
         author = spec
      if author is None:
         continue
      author_id = author.get('@id',author.get('name'))
      author_label, author_is_new = (id + '_author' + str(author_index), True) if author_indexer is None else author_indexer(author_id)

      if author_is_new:
         author_node = create_node(
            typeLabel(personType,leaf=leaf),
            ('@id',author_id),
            name=author.get('name'),
            image=author.get('image',{}).get('url'),
            sameAs=author.get('sameAs'),
            description=author.get('description')
         )
         graph[author_label] = author_node

      #edges = get_edges(articleNode)
      #edges.append({'~to' : author_label, '~label' : 'author'})
      authors = articleNode.get(':author',[])
      authors.append({'~to' : author_label})
      if ':author' not in articleNode:
         articleNode[':author'] = authors
      author_index += 1

   return graph
