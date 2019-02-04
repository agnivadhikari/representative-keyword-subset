import requests
import time
import wget
def read_and_download_files():
  file = "conference_details.txt" #2017,7969651,340
  details = []
  with open(file,"rb") as f:
    for i in f.readlines():
      details.append(i)
  for item in details:
    (year_str,base_number_str,total_papers_str) = item.split(",")
    base_number = int(base_number_str)
    total_papers = int(total_papers_str)
    print type(year_str),type(base_number),type(total_papers)
    print year_str,base_number,total_papers
    print '########### Downloading started for year '+year_str+' ################'
    for i in range(total_papers):
      paper_identifier = base_number + i
      request_str = 'http://ieeexplore.ieee.org/document/'+str(paper_identifier)+'/keywords'
      print request_str
      downloaded_file_name = year_str+'/'+str(paper_identifier)
      print downloaded_file_name
      wget.download(request_str,downloaded_file_name) # for web crawling and saving the files to be processed later
    print '########### Completed downloading for year '+year_str+' ################'      

def main():
  read_and_download_files()
  
if __name__=="__main__":
  main()
