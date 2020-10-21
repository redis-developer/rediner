import sys
import argparse
import os
import re
import yaml

import unicodedata

# https://spacy.io/usage/models
# python -m spacy download en_core_web_sm
import spacy
nlp = spacy.load("en_core_web_sm")

include_entities = set(['PERSON','NORP','FAC','ORG','GPE','LOC','PRODUCT','EVENT','WORK_OF_ART','LAW','LANGUAGE'])

en_punctuation_symbol = set(['P','S'])
ordinal = re.compile("[0-9]+")

# This function handles punctuation and other syntax that may be in the entity
# and then it normalizes it to separate terms without the punctuation
def normalize_en(term):
   # remove possessive
   if term[-2:]=="'s":
      term = term[:-2]

   terms = []

   # split term with slashs
   for item in term.split('/'):
      words = list(filter(lambda s : len(s)>0,item.split(' ')))
      start = 0
      # check for trailing parenthesis
      # e.g. Keyhole Markup Language (
      if len(words)>0 and words[-1]=='(':
         words = words[:-1]
      # check for trailing parenthesis acronym
      # e.g. Open Geospatial Consortium (OGC
      if len(words)>0 and words[-1][0]=='(':
         terms.append(words[-1][1:])
         words = words[:-1]
      # check for strange outcomes with versus
      # versus km
      if len(words)>0 and words[0]=='versus':
         words = words[1:]

      # remove lowercase first word followed by uppercase
      # e.g. python Flask
      if len(words)>1 and unicodedata.category(words[0][0])[1]=='l' and unicodedata.category(words[1][0])[1]=='u':
         words = words[1:]


      remove = set()
      for index,word in enumerate(words):
         start_category = unicodedata.category(word[0])[0]
         if len(word)==1 and start_category in en_punctuation_symbol:
            remove.add(index)
            continue
         if start_category=='P':
            word = word[1:]
         if len(word)>0:
            end_category = unicodedata.category(word[-1])[0]
            if end_category=='P':
               word = word[:-1]
         words[index] = word

      for offset,index in enumerate(sorted(list(remove))):
         del words[index-offset]

      # add term for ordinal suffixed terms:
      # e.g. XML Prague 2014 -> XML Prague, XML Prague 2014
      if len(words)>1 and ordinal.fullmatch(words[-1]):
         terms.append(' '.join(words))
         terms.append(' '.join(words[:-1]))
      elif len(words)>0:
         normalized_term = ' '.join(words)
         if len(normalized_term)>0:
            terms.append(normalized_term)
   return terms

def extract_entities(content,include=include_entities,check_boundaries=True,strip_starting_stop_words=True):

   entities = {}
   for text in content if type(content)==list else [content]:
      doc = nlp(text)
      for entity in doc.ents:
         if entity.label_ not in include:
            continue

         if '\n' in entity.text:
            # total failure!
            continue

         if check_boundaries or strip_starting_stop_words:

            words = list(filter(lambda x: x!='',re.split(r'[ :]+',entity.text)))

            # sometimes we fail to recognize sentence boundaries
            if check_boundaries:
               invalid = False
               for word in words:
                  if word[-1]=='.':
                     invalid = True
               if invalid:
                  continue

            # strip initial stop words
            start = 0
            if strip_starting_stop_words:
               for word in words:
                  if not nlp.vocab[word.lower()].is_stop:
                     break
                  start += 1

            # rejoin the term words
            text = ' '.join(words[start:])

         else:
            text = entity.text

         terms = normalize_en(text)

         for term in terms:
            info = entities.get(term)
            if info is None:
               info = { 'count': 0, 'types': set()}
               entities[term] = info
            info['count'] += 1
            info['types'].add(entity.label_)
   return entities

if __name__ == '__main__':
   argparser = argparse.ArgumentParser(description='NER model')
   argparser.add_argument('--verbose',help='Output debugging trace',action='store_true',default=False)
   argparser.add_argument('--yaml',help='Treat input as schema.org in YAML format',action='store_true',default=False)
   argparser.add_argument('--check-boundaries',help='Check for entities across boundaries',action='store_true',default=False)
   argparser.add_argument('--strip-starting-stop-words',help='Strip starting stop works',action='store_true',default=False)
   argparser.add_argument('files',nargs='+',help='A list of text files to process')
   args = argparser.parse_args()

   for file in args.files:
      if args.yaml:
         with open(file) as yaml_source:
            article = yaml.load(yaml_source,Loader=yaml.Loader)
            for key in article.keys():
               node = article[key]
               if 'articleBody' in node:
                  text = node['articleBody']
                  break
      else:
         with open(file) as text_source:
            text = text_source.read()

      entities = extract_entities(text,check_boundaries=args.check_boundaries,strip_starting_stop_words=args.strip_starting_stop_words)

      for term in entities.keys():
         tid = 'term' + str(index)
         info = entities[term]
         print('{term} = {count}, {labels}'.format(term=term,count=info['count'],labels=', '.join(info['types'])))
