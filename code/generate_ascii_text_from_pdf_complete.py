import os
import commands
import re
import regex
import pprint
import io
import unicodedata
import codecs

def generate_ascii_text_from_pdf():
  beginning_year = 2013
  beginning_range = 5
  filename_abstract_dict = {}
  filename_tokenized_data_dict = {}
  for i in range(beginning_range):
    input_directory = 'pdf_'+str(beginning_year+i)+'/'
    output_directory = 'unicode_'+str(beginning_year+i)+'/'
    year_str = str(beginning_year+i)
    filenames = os.listdir(input_directory)
    for filename in filenames:
      print '=========================== Processing '+input_directory+filename+'============================'
      cmd = 'java -jar pdfbox-app-2.0.6.jar ExtractText '+input_directory + filename + ' '+output_directory + filename[1:-4]
      #print cmd
      (status, output) = commands.getstatusoutput(cmd)
      if status!=0:
        print cmd

  for i in range(beginning_range):
    input_directory = 'unicode_'+str(beginning_year+i)+'/'
    output_directory = str(beginning_year+i)+'/'
    year_str = str(beginning_year+i)
    filenames = os.listdir(input_directory)
    for filename in filenames:
      print '=========================== Processing ' + input_directory + filename + '============================'
      infile = codecs.open(input_directory+filename,'r',encoding='utf-8',errors='ignore')
      outfile = codecs.open(output_directory+filename,'w',encoding='ascii',errors='ignore')
      for line in infile.readlines():
        for word in line.split():
          outfile.write(word+" ")
      outfile.write("\n")
      infile.close()
      outfile.close()

def main():
  generate_ascii_text_from_pdf()
if __name__=="__main__":
  main()
