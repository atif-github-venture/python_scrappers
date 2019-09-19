from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import math

op = Options()
op.headless = True
browser = webdriver.Chrome('./chromedriver', options=op)


def get_js_soup(url, browser):
    browser.get(url)
    res_html = browser.execute_script('return document.body.innerHTML')
    soup = BeautifulSoup(res_html, 'html.parser')  # beautiful soup object to be used for parsing html content
    return soup


# tidies extracted text
def process_bio(bio):
    bio = bio.encode('ascii', errors='ignore').decode('utf-8')  # removes non-ascii characters
    bio = re.sub('\s+', ' ', bio)  # repalces repeated whitespace characters with single space
    return bio


def remove_script(soup):
    for script in soup(["script", "style"]):
        script.decompose()
    return soup


def scrape_dir_page(dir_url, browser):
    print('-' * 20, 'Scraping directory page', '-' * 20)
    profile_links = []
    home_links = []
    # execute js on webpage to load faculty listings on webpage and get ready to parse the loaded HTML

    soup = get_js_soup(dir_url, browser)
    total_result_for_default = int(soup.find('div', id='people-list-wrapper').find('p').get_text().split()[0])
    math.ceil(total_result_for_default / 10)
    # Pagination logic to crawl
    for x in range(1, math.ceil(total_result_for_default / 10 + 1)):
        print('Iterations: ' + str(x))
        for link_holder in soup.find_all('div',
                                         class_='postcard-left clearfix'):  # get list of all <div> of class 'photo nocaption'
            profile_link = link_holder.find_all('a')[0]['href']  # get the profile url
            home_link = link_holder.find_all('a')[1]['href']  # get the home url
            profile_links.append(profile_link)
            home_links.append(home_link)
        print('-' * 20, 'Found {} faculty profile urls'.format(len(profile_links)), '-' * 20)
        temp_url = 'https://ee.stanford.edu/people/faculty?page=' + str(x)
        soup = get_js_soup(temp_url, browser)

    return home_links, profile_links


dir_url = 'https://ee.stanford.edu/people/faculty'  # url of directory listings of CS faculty
home_links, profile_links = scrape_dir_page(dir_url, browser)


def scrape_faculty_page(fac_url, profile_url, browser):
    bio_url = fac_url
    bio = ''
    home_page_found = False
    exceptions = ['people', 'github', 'group']
    if any(e in fac_url for e in exceptions):
        bio_url = profile_url  # treat faculty profile page as homepage
    elif not fac_url.startswith('http'):
        bio_url = profile_url  # treat faculty profile page as homepage
    elif fac_url.endswith('.edu') or fac_url.endswith('.edu/') or fac_url.endswith('.org') or fac_url.endswith('.org/'):
        bio_url = profile_url  # treat faculty profile page as homepage
    else:
        home_page_found = True

    soup = get_js_soup(bio_url, browser)

    if 'Page not found' in soup.get_text():
        bio_url = profile_url  # treat faculty profile page as homepage
        soup = get_js_soup(bio_url, browser)

    if not home_page_found:
        # we're only interested in some parts of the profile page namely the address
        # and information listed under the Overview, Research, Publication and Awards tab
        try:
            bio = soup.find('div', class_='nav-collapse collapse').get_text(separator=' ') + ': '
            for tab in soup.find_all('div', class_='tab-pane'):
                bio += tab.get_text(separator=' ') + '. '
            bio = process_bio(bio)
        except:
            print('Could not access {}'.format(bio_url))
    else:
        bio_soup = remove_script(soup)
        bio = process_bio(bio_soup.get_text(separator=' '))

    return bio_url, bio


bio_urls, bios = [], []
tot_urls = len(home_links)
for i, h_link in enumerate(home_links):
    print('-' * 20, 'Scraping faculty url {}/{}'.format(i + 1, tot_urls), '-' * 20)
    bio_url, bio = scrape_faculty_page(h_link, profile_links[i], browser)
    bio_urls.append(bio_url)
    bios.append(bio)


def write_lst(lst, file_):
    with open(file_, 'w') as f:
        for l in lst:
            f.write(l)
            f.write('\n')


bio_urls_file = 'bio_urls.txt'
bios_file = 'bios.txt'
write_lst(bio_urls, bio_urls_file)
write_lst(bios, bios_file)
