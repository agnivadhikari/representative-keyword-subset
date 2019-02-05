from nltk.corpus import brown
import re
import pickle
# Gensim
import gensim
from gensim import models, corpora
from gensim.utils import simple_preprocess
from gensim.models import CoherenceModel
from gensim.test.utils import datapath
from nltk import word_tokenize
from nltk.corpus import stopwords
import os
import commands
import re
import regex
import pprint
import logging
import numpy as np
import pandas as pd
# spacy for lemmatization
import spacy
import io
from string import punctuation
# Plotting tools
import pyLDAvis
import pyLDAvis.gensim  
import matplotlib.pyplot as plt
logging.basicConfig(filename='myProgramLog-final-run-01022019.txt', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)
stop_words = stopwords.words('english') + list(punctuation)
nlp = spacy.load('en', disable=['parser', 'ner'])

def topicmodel():
  NUM_TOPICS = 50
  beginning_year = 2013
  beginning_range = 4
  filename_abstract_dict = {}
  filename_tokenized_data_dict = {}
  tokenized_data = []
  lemmatized_data = []  
  for i in range(beginning_range):
    directory = '../text/'+str(beginning_year+i)+'/'
    year_str = str(beginning_year+i)
    filenames = os.listdir(directory)
    IEEE_filename_keywords_dict = {}
    weighted_graph_dict = {}
    unique_edge_tuple_list = []
    unique_vertex_list = []
    unique_taxonomy_list = []
    unique_conference_keywords = []
    no_of_papers_without_abstract = 0
    filename_abstract_dict = {}
    filename_wordlist_dict = {}
    filename_tf_dict = {}

    for filename in filenames:
      #print '\n=========================== Processing '+directory+filename+'============================\n'
      with open(directory+filename,"rU") as content_file:
        file_content = content_file.read()
        text = re.sub(r'\W+', ' ', file_content)
      #Gets the list of keywords for the particular paper
      abstract = get_abstract(text)
      if abstract == 'N/A':
	no_of_papers_without_abstract+=1
	continue
      filename_abstract_dict[filename]=abstract
    size_of_document_corpus = len(filename_abstract_dict)
    logging.debug('size_of_document_corpus: '+str(len(filename_abstract_dict)))
    for filename in filename_abstract_dict:
      abstract = filename_abstract_dict[filename]
      all_words = tokenize(abstract,stop_words)
      words = []
      for word in all_words:
        if len(word) < 3:
          #logging.debug("Small words not added: "+word)
          continue
        if re.match(r'^[0-9]', word):
          #logging.debug("Words staring with number not added: "+word)
          continue
        words.append(word)
      filename_tokenized_data_dict[filename]=words
  for item in filename_tokenized_data_dict:
    words = filename_tokenized_data_dict[item]
    for word in words:
      tokenized_data.append(unicode(word))

  logging.debug('Started lemmatization')
  lemmatized_data = lemmatization(tokenized_data, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])
  logging.debug('Length of lemmatized data: '+str(len(lemmatized_data)))
  logging.debug('Lemmatization done')

  with open('lemmatized_data.pkl', 'wb') as f:
    pickle.dump(lemmatized_data, f)
  
  with open('lemmatized_data.pkl', 'rb') as f:
    lemmatized_data = pickle.load(f)
  # Build a Dictionary - association word to numeric id
  id2word = corpora.Dictionary(lemmatized_data)
  logging.debug('id2word done')

  # Transform the collection of texts to a numerical form
  corpus = [id2word.doc2bow(text) for text in lemmatized_data]
  logging.debug('corpus done')

  # Build the LDA model

  lda_model = models.LdaModel(	corpus=corpus, 
				id2word=id2word, 
				num_topics=NUM_TOPICS)
  
  logging.debug('LdaModel creation done')
				
  print("LDA Model:")
  
  for idx in range(NUM_TOPICS):
      # Print the first 50 most representative topics
      print("Topic #%s:" % idx, lda_model.print_topic(idx, 10))
  
  print("=" * 20)
  
  #datapath = ./anaconda2/lib/python2.7/site-packages/gensim/test/test_data/
  temp_file = datapath("saved-model")
  lda_model.save(temp_file)

  saved_lda_model = models.LdaModel.load(temp_file)

  print("Saved LDA Model:")
  
  for idx in range(NUM_TOPICS):
      # Print the first 50 most representative topics
      print("Topic #%s:" % idx, saved_lda_model.print_topic(idx, 5))
  
  print("=" * 20)

  # Compute Coherence Score
  coherence_model_lda = CoherenceModel(model=saved_lda_model, texts=lemmatized_data, dictionary=id2word, coherence='c_v')
  coherence_lda = coherence_model_lda.get_coherence()
  print('\nCoherence Score: ', coherence_lda)

  beginning_year = 2017
  beginning_range = 1
  target_filename_content_dict = {}
  target_filename_keywords_dict = {}
  target_filename_keywords_probabilities_dict = {}
  for i in range(beginning_range):
    directory = '../text/'+str(beginning_year+i)+'/'
    year_str = str(beginning_year+i)
    filenames = os.listdir(directory)
    for filename in filenames:
      logging.debug('\n=========================== Processing '+directory+filename+'============================\n')
      with open(directory+filename,"rU") as content_file:
        file_content = content_file.read()
        text = re.sub(r'\W+', ' ', file_content)        
      #Gets the list of keywords for the particular paper
      content = get_abstract(text)
      logging.debug('filename: '+filename+' '+year_str)
      all_words = tokenize(content,stop_words)
      words = []
      for word in all_words:
        if len(word) < 3:
          #logging.debug("Small words not added: "+word)
          continue
        if re.match(r'^[0-9]', word):
          #logging.debug("Words staring with number not added: "+word)
          continue
        words.append(word)
      bow = id2word.doc2bow(words)
      sorted_topic_list = sorted(saved_lda_model[bow], key=lambda x: x[1], reverse=True)
      top_topic = sorted_topic_list[:1]
      (idx,value) = top_topic[0]
      top_topic_str = str(saved_lda_model.print_topic(idx, 5))
      top_topic_keywords = re.findall(r'"([^"]*)"', top_topic_str)
      top_topic_probabilities = re.findall("\d+\.\d+", top_topic_str)
      target_filename_keywords_dict[filename+' '+year_str] = top_topic_keywords
      target_filename_keywords_probabilities_dict[filename+' '+year_str] = top_topic_probabilities
  pprint.pprint('target_filename_keywords_dict')
  pprint.pprint(target_filename_keywords_dict)
  pprint.pprint('target_filename_keywords_probabilities_dict')
  pprint.pprint(target_filename_keywords_probabilities_dict)  
  logging.debug('Run completed for number of topics: '+str(NUM_TOPICS))
  all_unique_conference_keywords = generate_conference_keyword_list(target_filename_keywords_dict)
  pprint.pprint('all_unique_conference_keywords')
  pprint.pprint(all_unique_conference_keywords)  

def tokenize(text, stop_words):
    words = word_tokenize(text)
    words = [w.lower() for w in words]
    return [w for w in words if w not in stop_words and not w.isdigit()]  

def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    i = 0
    """https://spacy.io/api/annotation"""
    texts_out = []
    #print 'In lemmatization'
    #print texts
    for word in texts:
        doc = nlp(word)
        #print 'Docs'
        #print doc
        texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
	i+=1
	logging.debug(str(i))
    return texts_out
  
def compute_coherence_values(id2word, corpus, texts, limit, start=2, step=3):
    coherence_values = []
    model_list = []
    for num_topics in range(start, limit, step):
	model = models.LdaModel(corpus=corpus, 
				id2word=id2word, 
				num_topics=num_topics)
        model_list.append(model)
        coherencemodel = CoherenceModel(model=model, texts=texts, dictionary=id2word, coherence='c_v')
        coherence_values.append(coherencemodel.get_coherence())
	print 'For number of topics = ', str(num_topics)  	
	print("=" * 20)
  	for idx in range(num_topics):
      	  print("Topic #%s:" % idx, model.print_topic(idx, 10))

    return model_list, coherence_values


def get_abstract(text):
  abstract = 'N/A'
  match = re.search(r'(?<=(ABSTRACT|Abstract))[\s\S]*(?=(REFERENCE|REFERENCES))',text)
  if match:
    abstract = match.group()
  return abstract
def get_keyword_index(keyword, sorted_on_specific_parameter):
  i=0
  for item in sorted_on_specific_parameter:
    i+=1
    if item["keyword"]==keyword:
      break
  return i

def  generate_conference_keyword_list(filename_keywords_dict):
  unique_conference_keywords = []
  for key in filename_keywords_dict.keys():
    temp_keyword_list = filename_keywords_dict[key]
    for keyword in temp_keyword_list:
      if keyword not in unique_conference_keywords:
        unique_conference_keywords.append(keyword)
  return unique_conference_keywords

def main():
  topicmodel()
if __name__=="__main__":
  main()
