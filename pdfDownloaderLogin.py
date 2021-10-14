import os
import sys
from progressbar import widgets
import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse
from urllib.request import urlopen
import time
import wget
import progressbar
from urllib3.exceptions import InsecureRequestWarning
from concurrent.futures import as_completed #This and FuturesSession are used to parallelize the downloading process
from requests_futures.sessions import FuturesSession
#import ssl #To avoid error: Unable to get local issuer certificate
#import certifi #Then, add intermediate certificate to file of certifi

def check_validity(req):
    try:    
        urlopen(req)
        print("Valid URL")
    except IOError:
        print ("Invalid URL")
        sys.exit()

def file_name_extractor(link):
    '''
    This function takes a link and returns 
    the file name from end of that link
    in a nice format
    '''
    file_name_loc = link.rfind('/') + 1
    if file_name_loc == 0:
        print('Invalid link...')
        return None
    return link[file_name_loc:].replace('%20',' ')

if __name__ == "__main__":

    start_time = time.time()

    #Supress warning messages in case verify=False in get and post methods
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    # all cookies received will be stored in the curession object
    with requests.Session() as curSession:
        
        curSession.verify = False #Equivalent to setting verify argument in all Session methods
        
        loginUrl = input('Please enter url of login page: ')
        username = input('Please enter your username/email (based on login page): ')
        password = input('Please enter your password: ')
        check_validity(loginUrl)
        resourceUrl = input('Enter url of webpage containing the pdfs: ')
        
        payload={'username': username,'password': password}
        # internally return your expected cookies, can use for following auth
        curSession.post(loginUrl, data=payload)
        # internally use previously generated cookies, can access the resources
        html_page = curSession.get(resourceUrl)
        pageWithPdfs = bs(html_page.text, features='html.parser')

        og_url = pageWithPdfs.find("meta",  property = "og:url")
        base = urlparse(og_url)

        pdfs_links = []
        all_a_tags = pageWithPdfs.find_all('a')

        sh_txt = 'In case there are no direct links from this page,\n' + \
                 'please enter link keywords that will help the program find ' + \
                 'links that will redirect to pdfs: '
        search_link = input(sh_txt)

        widgets = [' [', progressbar.Timer(), '] ',
                   progressbar.Bar(), ' (', progressbar.ETA(), ') ',]
        bar = progressbar.ProgressBar(maxval=len(all_a_tags), widgets=widgets).start()
        for idx, a_tag in enumerate(all_a_tags):
            current_link = a_tag.get('href')
            if current_link == None or \
              not current_link.startswith('http'):
                bar.update(idx)
                continue
            if current_link.endswith('pdf'):
                if og_url:
                    pdfs_links.append(og_url["content"] + current_link)
                else:
                    pdfs_links.append(base.scheme + "://" + base.netloc + current_link)
            elif current_link.find(search_link) != -1:
                try:
                    resource_link = curSession.get(current_link)
                except:
                    bar.update(idx)
                    continue
                if resource_link.url.endswith('pdf'):
                    pdfs_links.append(resource_link.url)
            bar.update(idx)

        folder_location = r'D:\HopeThisWorks'
        if not os.path.exists(folder_location):
                os.mkdir(folder_location)

        if pdfs_links != []:
            print('\nFound file links!\nDownloading...\n')
        bar = progressbar.ProgressBar(maxval=len(pdfs_links), widgets=widgets).start()
        for idx, pdf_link in enumerate(pdfs_links):
            r = curSession.get(pdf_link, stream=True) #stream makes .get() works with pdfs
            pdf_full_path = os.path.join(folder_location, \
                                   file_name_extractor(pdf_link))
            with open(pdf_full_path, 'wb') as f:
                f.write(r.content)
            bar.update(idx)
        
    print(f"\nDone!\nProgram run time:\n{(time.time() - start_time) / 60.0:.2f} minutes")



