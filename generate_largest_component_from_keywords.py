from __future__ import division
import os
import commands
import re
import regex
#from graph_tool.all import *
import json
import cairo
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import copy
import pickle
import operator
from operator import itemgetter, attrgetter
import pprint
import logging
#logging.basicConfig(filename='myProgramLog.txt', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(filename='myProgramLog.txt', level=logging.WARN, format=' %(asctime)s - %(levelname)s - %(message)s')
import StringIO

def process_html_files():
  beginning_year = 2013
  beginning_range = 5
  all_unique_conference_keywords = []
  yearly_conference_keywords_dict = {}
  yearly_filename_keywords_dict = {}  
  yearly_array_dict = {}
  yearly_graph_dict = {}
  filename_keywords_dict = {}
  yearly_keyword_count = {}
  keyword_statistics_list = []
  connected_components_dict = {}
  temp_weighted_graph_dict = {}
  for i in range(beginning_range):
    directory = '../html/'+str(beginning_year+i)+'/'
    year_str = str(beginning_year+i)
    filenames = os.listdir(directory)
    IEEE_filename_keywords_dict = {}
    weighted_graph_dict = {}
    unique_edge_tuple_list = []
    unique_vertex_list = []
    unique_taxonomy_list = []
    unique_conference_keywords = []
    for filename in filenames:
      #print '\n=========================== Processing '+filename+'============================\n'
      with open(directory+filename,"rU") as content_file:
        text = content_file.read()
      #Gets the list of keywords for the particular paper
      keywords_list = get_keywords(text)
      if keywords_list == []:
        continue
      # Populate the filename_keywords_dict 
      filename_keywords_dict[filename+' '+year_str] = keywords_list
  
  # Gets the list of unique conference keywords for all the years
  all_unique_conference_keywords = generate_conference_keyword_list(filename_keywords_dict)
  print "Number of keywords:",len(all_unique_conference_keywords)
  weighted_graph_dict = create_edge_list_with_keywords(filename_keywords_dict)
  keyword_vertices_dict = {}
  for keyword in all_unique_conference_keywords:
    vertices = []    
    for vertex in filename_keywords_dict:
      if keyword in filename_keywords_dict[vertex]:
        if vertex not in vertices:
          vertices.append(vertex)
    keyword_vertices_dict[keyword] = vertices
  for k in sorted(keyword_vertices_dict, key=lambda k: len(keyword_vertices_dict[k]), reverse=True): # Sort the dictionary based on length of the vertices list    
    keyword_vertices_dict[k].sort(key=lambda k:int(k.split()[-1])) # Sort the vertices list based on the year substring in each vertices list of each keyword
    yearly_keyword_count = {}
    for i in range(beginning_range):  
      year_str = str(beginning_year+i)
      yearwise_count = 0
      for item in keyword_vertices_dict[k]:
        if item.endswith(year_str):
          yearwise_count=yearwise_count+1
      yearly_keyword_count[year_str]=yearwise_count
    sd = np.std(yearly_keyword_count.values())
    priority = get_priority(k, filename_keywords_dict, keyword_vertices_dict)
    keyword_statistics_list.append({"keyword":k, "2013":yearly_keyword_count['2013'], "2014":yearly_keyword_count['2014'], "2015":yearly_keyword_count['2015'],"2016":yearly_keyword_count['2016'], "2017":yearly_keyword_count['2017'],"total":len(keyword_vertices_dict[k]), "priority":priority, "sd":sd})
  sorted_on_specific_parameter = sorted(sorted(keyword_statistics_list, key=lambda k: (k['priority'])),key=lambda k: (k['total']), reverse=True)
  logging.debug('starting of main portion')
  conn_keywords_index = 0
  conn_keywords_set_dict = {}
  conn_keywords_vertices_set_dict = {}
  conn_keywords_temp_dict_len_dict = {}
  conn_keywords_iteration_len_dict = {}
  list_of_largest_component_size = []
  total_vertices_count = len(filename_keywords_dict.keys())
  all_vertices_set = set()
  for vertex in filename_keywords_dict.keys():
    all_vertices_set.add(vertex)
  logging.debug('Total vertices count: '+str(total_vertices_count))
  print 'Total vertices count: '+str(total_vertices_count)
  total_obtained_vertices_count = 0
  while get_count_conn_keywords_vertices_set_dict(conn_keywords_vertices_set_dict) < total_vertices_count:
    conn_keywords_index+=1
    logging.debug('while get_count_conn_keywords_vertices_set_dict loop: conn_keywords_index: '+str(conn_keywords_index))
    (conn_keywords_set,conn_keywords_vertices_set,conn_keywords_temp_dict_len_dict,conn_keywords_iteration_len_dict,list_of_largest_component_size) = update_keywords_gist_set(filename_keywords_dict,keyword_vertices_dict,sorted_on_specific_parameter,conn_keywords_set_dict,conn_keywords_vertices_set_dict,conn_keywords_temp_dict_len_dict,conn_keywords_iteration_len_dict,list_of_largest_component_size)
    conn_keywords_set_dict[conn_keywords_index] = conn_keywords_set
    conn_keywords_vertices_set_dict[conn_keywords_index] = conn_keywords_vertices_set
    logging.debug('Run completed for component: '+str(conn_keywords_index))
    logging.debug('The set of keywords for this component is: '+str(conn_keywords_set))
    logging.debug('The set of vertices for this component is: '+str(conn_keywords_vertices_set))
    print 'The total number of vertices obtained for component: '+str(conn_keywords_index)+' is '+ str(get_count_conn_keywords_vertices_set_dict(conn_keywords_vertices_set_dict))
  pprint.pprint(conn_keywords_set_dict) 
  print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
  total_set_length = 0
  gist_vertices_set = set()
  for index in conn_keywords_set_dict:
    keywords_set = conn_keywords_set_dict[index]
    total_set_length = total_set_length+len(keywords_set)
    for keyword in keywords_set:
      vertices_list = keyword_vertices_dict[keyword]
      for vertex in vertices_list:
	gist_vertices_set.add(vertex)
    s = StringIO.StringIO()
    pprint.pprint(all_vertices_set - gist_vertices_set,s)
    logging.debug('Remaining vertices after index: '+str(index)+' is '+s.getvalue())
    pprint.pprint('Remaining vertices after index: '+str(index)+' is '+s.getvalue())

  print 'Length of minimum spanning set: '+str(total_set_length)
  print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
  print 'Statistics of temporary dictionary length for each keyword in minimum spanning set of keywords'
  temp_dict_iteration_len_list = []
  for item in conn_keywords_temp_dict_len_dict.items():
    keyword = item[0]
    temp_dict_len = conn_keywords_temp_dict_len_dict[keyword]
    iteration_len = conn_keywords_iteration_len_dict[keyword]
    list_item = (keyword, temp_dict_len)
    temp_dict_iteration_len_list.append(list_item)
  pprint.pprint(temp_dict_iteration_len_list)
  print 'list_of_largest_component_size'
  pprint.pprint(list_of_largest_component_size)

def get_keyword_index(keyword, sorted_on_specific_parameter):
  i=0
  for item in sorted_on_specific_parameter:
    i+=1
    if item["keyword"]==keyword:
      break
  return i
def update_keywords_gist_set(filename_keywords_dict,keyword_vertices_dict,sorted_on_specific_parameter,conn_keywords_set_dict,conn_keywords_vertices_set_dict,conn_keywords_temp_dict_len_dict,conn_keywords_iteration_len_dict, list_of_largest_component_size):
  logging.debug('starting of update_keywords_gist_set')
  continue_loop = True
  current_cumulative_keywords_set = set()
  current_cumulative_vertices_set = set()
  previous_item = None
  temp_vertices_dict = {}
  temp_vertices_len_dict = {}
  item_updated_in_between = False
  no_of_iterations_performed = 0
  actual_no_of_iterations_performed = 0
  previous_selected_keyword = None
  while(continue_loop):
    logging.debug('starting of while(continue_loop)')
    continue_loop = False
    item_updated_in_between = False
    for item in sorted_on_specific_parameter:
      #logging.debug('starting of for item in sorted_on_specific_parameter')
      no_of_iterations_performed += 1
      keyword = item["keyword"]
      logging.debug('current keyword: '+keyword)
      logging.debug('no_of_iterations_performed: '+str(no_of_iterations_performed))
      vertices_set = set(keyword_vertices_dict[keyword])
      conn_vertices_set = get_conn_vertices_set(conn_keywords_vertices_set_dict)
      if not current_cumulative_keywords_set:
	if check_keyword_in_gist_set(keyword, conn_keywords_set_dict) or vertices_set.issubset(conn_vertices_set.union(current_cumulative_vertices_set)):
	  logging.debug('keyword already in gist set or vertices are subset, so skip: '+keyword)
	  continue
	else:
          current_cumulative_keywords_set.add(keyword)
	  temp_list = []	
	  temp_list = keyword_vertices_dict[keyword]	
	  for temp_item in temp_list:
	    current_cumulative_vertices_set.add(temp_item)
	  logging.debug('Keyword added in empty set: '+keyword)
          list_of_largest_component_size.append(len(conn_vertices_set.union(current_cumulative_vertices_set)))
	  conn_keywords_temp_dict_len_dict[keyword] = len(temp_vertices_len_dict)
	  logging.debug('Keyword: '+keyword+', length of temp_vertices_len_dict: '+str(len(temp_vertices_len_dict)))
	  actual_no_of_iterations_performed = get_keyword_index(keyword,sorted_on_specific_parameter)
	  conn_keywords_iteration_len_dict[keyword] = actual_no_of_iterations_performed
	  logging.debug('Keyword: '+keyword+', No. of iterations performed: '+str(actual_no_of_iterations_performed))
	  previous_selected_keyword = keyword
	  continue

      if keyword in current_cumulative_keywords_set or check_keyword_in_gist_set(keyword, conn_keywords_set_dict):
        logging.debug('keyword skipped as already added: '+keyword)
        continue

      if vertices_set.issubset(conn_vertices_set.union(current_cumulative_vertices_set)):
        logging.debug('keyword skipped as subset: '+keyword)	
	continue
      if vertices_set.isdisjoint(conn_vertices_set.union(current_cumulative_vertices_set)):
        logging.debug('keyword skipped as disjoint: '+keyword)
	continue
      temp_vertices_dict[keyword] = vertices_set - current_cumulative_vertices_set
      temp_vertices_len_dict[keyword] = len(temp_vertices_dict[keyword])
      logging.debug('keyword in temp dict: '+keyword+', number of augmented nodes: '+str(len(temp_vertices_dict[keyword])))
      if previous_item is None:
	logging.debug('previous_item is None: ')
	previous_item = item
	logging.debug('Now the previous_item is: '+previous_item["keyword"]+', count: '+str(previous_item["total"]))
	continue	
      if (item["total"] < temp_vertices_len_dict[previous_item["keyword"]]):
	logging.debug('item count is less than number of augmented vertices - stop condition satisfied\nkeyword: '+item["keyword"]+'\tcount: '+str(item["total"])+'\nprevious keyword: '+previous_item["keyword"]+'\tnumber of augmented vertices: '+str(temp_vertices_len_dict[previous_item["keyword"]]))	      
	s = StringIO.StringIO()
	pprint.pprint(temp_vertices_len_dict,s)
	logging.debug('temp_vertices_len_dict: '+s.getvalue())
	max_item = max(temp_vertices_len_dict.iteritems(), key=operator.itemgetter(1))
	logging.debug('max item: '+str(max_item[0])+', count: '+str(max_item[1]))
	current_cumulative_keywords_set.add(max_item[0])
        item_updated_in_between = True
	temp_list = []
	temp_list = temp_vertices_dict[max_item[0]]
	for temp_item in temp_list:
	  current_cumulative_vertices_set.add(temp_item)
	conn_keywords_temp_dict_len_dict[max_item[0]] = len(temp_vertices_len_dict)
	logging.debug('Keyword: '+max_item[0]+', length of temp_vertices_len_dict: '+str(len(temp_vertices_len_dict)))
	actual_no_of_iterations_performed = get_keyword_index(max_item[0],sorted_on_specific_parameter) - get_keyword_index(previous_selected_keyword,sorted_on_specific_parameter)
	conn_keywords_iteration_len_dict[max_item[0]] = actual_no_of_iterations_performed
	logging.debug('Keyword: '+max_item[0]+', No. of iterations performed: '+str(actual_no_of_iterations_performed))
	previous_selected_keyword = max_item[0]
	temp_vertices_dict = {}
	temp_vertices_len_dict = {}
	previous_item = None
	no_of_iterations_performed = 0
	continue_loop = True
        logging.debug('keyword added: '+max_item[0])
        list_of_largest_component_size.append(len(conn_vertices_set.union(current_cumulative_vertices_set)))
	logging.debug('Break')	      
	break
	  
      else:
	logging.debug('Just the loop is continued')
	continue
	
    if not item_updated_in_between:
      logging.debug('After traversing the entire loop')
      s = StringIO.StringIO()
      pprint.pprint(temp_vertices_len_dict,s)
      logging.debug('temp_vertices_len_dict: '+s.getvalue())
      if not temp_vertices_len_dict:
        logging.debug('No more elements will be augmented in this run. Stopping the loop.')
        continue_loop = False
        break  
      max_item = max(temp_vertices_len_dict.iteritems(), key=operator.itemgetter(1))
      logging.debug('max item: '+str(max_item[0])+', count: '+str(max_item[1]))
      current_cumulative_keywords_set.add(max_item[0])
      temp_list = []
      temp_list = temp_vertices_dict[max_item[0]]
      for temp_item in temp_list:
        current_cumulative_vertices_set.add(temp_item)
      conn_keywords_temp_dict_len_dict[max_item[0]] = len(temp_vertices_len_dict)
      logging.debug('Keyword: '+max_item[0]+', length of temp_vertices_len_dict: '+str(len(temp_vertices_len_dict)))
      actual_no_of_iterations_performed = get_keyword_index(max_item[0],sorted_on_specific_parameter) - get_keyword_index(previous_selected_keyword,sorted_on_specific_parameter)
      conn_keywords_iteration_len_dict[max_item[0]] = actual_no_of_iterations_performed
      logging.debug('Keyword: '+max_item[0]+', No. of iterations performed: '+str(actual_no_of_iterations_performed))
      previous_selected_keyword = max_item[0]
      temp_vertices_dict = {}
      temp_vertices_len_dict = {}
      previous_item = None
      no_of_iterations_performed = 0
      continue_loop = True
      logging.debug('keyword added: '+max_item[0])
      list_of_largest_component_size.append(len(conn_vertices_set.union(current_cumulative_vertices_set)))
    if len(conn_vertices_set.union(current_cumulative_vertices_set)) == len(filename_keywords_dict.keys()):
      logging.debug('All vertices are added!!!')
      break
    
  return (current_cumulative_keywords_set, current_cumulative_vertices_set,conn_keywords_temp_dict_len_dict,conn_keywords_iteration_len_dict,list_of_largest_component_size)

def get_max_item(temp_vertices_len_dict,current_cumulative_keywords_set,current_cumulative_vertices_set,temp_vertices_dict):
  s = StringIO.StringIO()
  pprint.pprint(temp_vertices_len_dict,s)
  logging.debug('temp_vertices_dict: '+s.getvalue())
  max_item = max(temp_vertices_len_dict.iteritems(), key=operator.itemgetter(1))
  logging.debug('max item: '+str(max_item[0])+', count: '+str(max_item[1]))
  current_cumulative_keywords_set.add(max_item[0])
  #print "Keyword:",max_item[0]
  temp_list = []
  temp_list = temp_vertices_dict[max_item[0]]
  for temp_item in temp_list:
    current_cumulative_vertices_set.add(temp_item)
  temp_vertices_dict = {}
  temp_vertices_len_dict = {}
  previous_item = None
  continue_loop = True
  logging.debug('keyword added: '+max_item[0])
  logging.debug('Break')
def update_max_augmented_vertices():
  temp_vertices_dict = {}
  for key, value in conn_keywords_vertices_set_dict.items():	  
    temp_vertices_dict[key] = vertices_set - set(value)
  max_item = max(temp_vertices_dict.iteritems(), key=operator.itemgetter(1))
  
def get_conn_vertices_set(conn_keywords_vertices_set_dict):
  conn_vertices_set = set()
  for key in conn_keywords_vertices_set_dict:
    conn_vertices_set.update(conn_keywords_vertices_set_dict[key])
  return conn_vertices_set
def check_keyword_in_gist_set(keyword, conn_keywords_set_dict):
  for key in conn_keywords_set_dict:
    if keyword in conn_keywords_set_dict[key]:
      return True
  return False
def check_keyword_in_disjoint_keywords_set(keyword, disjoint_keywords_set):
  if keyword in disjoint_keywords_set:
    return True
  else:
    return False
def check_keyword_in_rejected_keywords_set(keyword, rejected_keywords_set):
  if keyword in rejected_keywords_set:
    return True
  else:
    return False
def get_count_conn_keywords_vertices_set_dict(conn_keywords_vertices_set_dict):
  count = 0
  for key in conn_keywords_vertices_set_dict.keys():
    count = count + len(conn_keywords_vertices_set_dict[key])
  return count
def get_priority(keyword, filename_keywords_dict, keyword_vertices_dict):
  priority = 0.00
  priority_list = []
  for key in filename_keywords_dict.keys():
    keyword_list = filename_keywords_dict[key]
    if keyword in keyword_list:
      priority_list.append(keyword_list.index(keyword))

  priority = sum(priority_list)/len(keyword_vertices_dict[keyword])
  return priority

    
  
def get_no_of_common_papers_consecutive_keyword(previous_keyword, current_keyword, keyword_vertices_dict):
  no_of_common_papers_consecutive_keyword = 0
  if previous_keyword =='':
    no_of_common_papers_consecutive_keyword = len(keyword_vertices_dict[current_keyword])
  else:
    previous_list = keyword_vertices_dict[previous_keyword]
    current_list = keyword_vertices_dict[current_keyword]
    for paper in previous_list:
      if paper in current_list:
        no_of_common_papers_consecutive_keyword = no_of_common_papers_consecutive_keyword + 1  
  return no_of_common_papers_consecutive_keyword
 
def pickle_unique_keyword_frequency(sorted_on_specific_parameter):
  unique_keyword_frequency_dict = {}
  for item in sorted_on_specific_parameter:
    keyword = item["keyword"]
    frequency = item["total"]
    unique_keyword_frequency_dict[keyword] = frequency

  with open('unique_keyword_frequency_dict.txt', 'wb') as handle:
    pickle.dump(unique_keyword_frequency_dict, handle)

  #with open('unique_keyword_frequency_dict.txt', 'rb') as handle:
    #temp_unique_keyword_frequency_dict = pickle.loads(handle.read())  
  
  #print temp_unique_keyword_frequency_dict

def create_graph(unique_vertex_list, keyword_graph_dict):
  unique_edge_tuple_list = keyword_graph_dict.keys()
  # Creates an undirected Graph object
  g = Graph(directed=False)
  vprop = g.new_vertex_property("string") 
  g.vertex_properties["name"]=vprop 

  eprop = g.new_edge_property("string")
  g.edge_properties["name"]=eprop
  
  # Creates vertex object i.e. node for each author
  for item in unique_vertex_list:
    vertex = g.add_vertex()
    vprop[vertex] = item

  # Creates the edges according to the unique edge tuples
  for edge_tuple in unique_edge_tuple_list:
    edge = g.add_edge(find_vertex(g, vprop, edge_tuple[0])[0],find_vertex(g, vprop, edge_tuple[1])[0])
    eprop[edge] = str(keyword_graph_dict[edge_tuple]).replace("[", "").replace("]", "").replace("'", "")
    #print edge_tuple,eprop[edge]
  return g

def  generate_conference_keyword_list(filename_keywords_dict):
  unique_conference_keywords = []
  #print filename_keywords_dict.keys()
  for key in filename_keywords_dict.keys():
    temp_keyword_list = filename_keywords_dict[key]
    for keyword in temp_keyword_list:
      if keyword not in unique_conference_keywords:
        unique_conference_keywords.append(keyword)
  return unique_conference_keywords

def create_IEEE_filename_keywords_dict(filename_keywords_dict, unique_IEEE_taxonomy_list):
  IEEE_filename_keywords_dict = {}
  
  for filename in filename_keywords_dict:
    IEEE_temp_keywords = []
    keywords = filename_keywords_dict[filename]
    for keyword in keywords:
      if keyword in unique_IEEE_taxonomy_list:
        IEEE_temp_keywords.append(keyword)
    IEEE_filename_keywords_dict[filename] = IEEE_temp_keywords
  return IEEE_filename_keywords_dict

def create_unique_vertex_list(weighted_graph_dict):
  unique_vertex_list = []
  for item in weighted_graph_dict.keys():
    filename1, filename2 = item
    if filename1 not in unique_vertex_list:
      unique_vertex_list.append(filename1)
    if filename2 not in unique_vertex_list:
      unique_vertex_list.append(filename2)
  return unique_vertex_list


def create_edge_list_with_keywords(filename_keywords_dict):
  weighted_graph_dict = {}
  unique_weighted_graph_dict = {}
  for item in filename_keywords_dict.items():
    filename, keywords = item
    for key in filename_keywords_dict.keys():
      if key == filename:
        continue
      weighted_graph_dict_key = (filename,key)      
      keywords_temp = filename_keywords_dict[key]
      for keyword in keywords:
        if keyword in keywords_temp:
          if weighted_graph_dict_key in weighted_graph_dict: 
            weighted_graph_dict[weighted_graph_dict_key].append(keyword)
          else:
            weighted_graph_dict[weighted_graph_dict_key] = []
            weighted_graph_dict[weighted_graph_dict_key].append(keyword)
  for item in weighted_graph_dict.keys():
    filename1, filename2 = item
    reverse_item = (filename2, filename1)
    if item not in unique_weighted_graph_dict:
      if reverse_item not in unique_weighted_graph_dict:
        unique_weighted_graph_dict[item] = weighted_graph_dict[item]
  
  weighted_graph_dict = unique_weighted_graph_dict
  return weighted_graph_dict

# Create graph and visualization

def create_graph_and_visualization(unique_vertex_list, weighted_graph_dict, filename):
  unique_edge_tuple_list = weighted_graph_dict.keys()
  # Creates an undirected Graph object
  g = Graph(directed=False)
  vprop = g.new_vertex_property("string") 
  g.vertex_properties["name"]=vprop 

  eprop = g.new_edge_property("string")
  g.edge_properties["name"]=eprop
  
  # Creates vertex object i.e. node for each author
  for item in unique_vertex_list:
    vertex = g.add_vertex()
    vprop[vertex] = item

  # Creates the edges according to the unique edge tuples
  for edge_tuple in unique_edge_tuple_list:
    edge = g.add_edge(find_vertex(g, vprop, edge_tuple[0])[0],find_vertex(g, vprop, edge_tuple[1])[0])
    eprop[edge] = str(weighted_graph_dict[edge_tuple]).replace("[", "").replace("]", "").replace("'", "")
    #print edge_tuple,eprop[edge]
  # Draws the graph
  graph_draw(
    g,
    vertex_text=g.vertex_properties["name"],
    edge_text=g.edge_properties["name"],
    bg_color=[1,1,1,1],
    vertex_fill_color=[1,1,1,1],
    edge_pen_width = 0.25,
    edge_text_distance = 10,
    vertex_size = 40,
    #edge_text_parallel = False,
    #vertex_text_color = "blue",
    edge_font_weight = cairo.FONT_WEIGHT_BOLD,
    edge_font_slant = cairo.FONT_SLANT_ITALIC,
    #edge_text_color = "red",
    vertex_font_size=10,
    edge_font_size=14,
    output_size=(3000, 3000), 
    output=filename
  )

def get_keywords(text):
  keywords_list = []
  match = re.search(r'(?<="IEEE Keywords","kwd":\[)[\s\S]+(?=]},{"type":"INSPEC: Controlled Indexing")',text)
  if match:
    keywords_text = match.group()
    keywords_text = keywords_text.replace('"', '')
    keywords_list = re.split(r',',keywords_text)
    keywords_list = [x.strip().lower() for x in keywords_list]
    if '' in keywords_list:
      keywords_list.remove('')
    return keywords_list 
  match = re.search(r'(?<="IEEE Keywords","kwd":\[)[\s\S]+(?=]},{"type":"Author Keywords ")',text) 
  if match:
    keywords_text = match.group()
    keywords_text = keywords_text.replace('"', '')
    keywords_list = re.split(r',',keywords_text)
    keywords_list = [x.strip().lower() for x in keywords_list]
    if '' in keywords_list:
      keywords_list.remove('')
    return keywords_list 
  else:
    keywords_list = []
  return keywords_list


def main():
  process_html_files()
if __name__=="__main__":
  main()
