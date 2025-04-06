import requests
from bs4 import BeautifulSoup
import re
import time
import io
import pandas as pd

fsrdc_keywords = ['longitudinal business database','annual business survey',  'american housing survey',
                  'annual survey of manufactures', 'american community survey','census of manufactures', 'census edited file', 'census of wholesale trade',
                  'census of services', 'current population survey', 'census of retail trade', 'decennial census',
                  'survey of business owners', 'census of mining', 'master address file extract', 'university of michigan']

dataname_to_code = {'longitudinal business database' : 'LBDREV',
                    'annual business survey' : 'ABS',
                    'annual survey of manufactures' : 'ASM',
                    'american community survey' : "ACS",
                    'american housing survey' : 'AHS',
                    'census of manufactures' : 'CMF',
                    'census of services' : 'CSR',
                    'census of retail trade' : 'CRT',
                    'census of wholesale trade' : 'CWH',
                    'census edited file' : 'CEF',
                    'current population survey' : 'CPS',
                    'decennial census' : 'CEN',
                    'survey of business owners' : 'SBO',
                    'census of mining' : 'CMI',
                    'master address file extract' : 'MAFX',
                    'university of michigan' : 'UM_CJARS',
                    }

def contains_fsrdc_keyword(text):
    """Check if the given text contains any FSRDC keyword."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in fsrdc_keywords)

def scrape_repec_papers(page_base):
    """
    Scrape the given RePEc listing pages for paper links, then follow each link
    to extract the abstract, authors, year, FSRC keywords (and codes), citations,
    and check that at least one author is in the researchers dataframe.
    """

    researchers_url = "https://raw.githubusercontent.com/dingkaihua/fsrdc-external-census-projects/master/metadata/Researchers.csv"
    try:
        response = requests.get(researchers_url, verify=False)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        # Use io.StringIO to treat the response text as a file-like object
        researchers_df = pd.read_csv(io.StringIO(response.text))
    except Exception as e:
        print("Error loading researchers CSV:", e)
        researchers_df = pd.DataFrame()  # or handle it as needed

    # print(len(researchers_df))
    
    valid_researchers = set()
    valid_researchers.update(researchers_df['PI'].dropna().tolist())
    valid_researchers.update(researchers_df['Researcher'].dropna().tolist())
    valid_researchers = {name.strip().lower() for name in valid_researchers}
    print("Valid researchers", valid_researchers)

    # Build a set of valid titles from the 'titles' column
    valid_titles = set()
    valid_titles.update(researchers_df['Title'].dropna().tolist())
    valid_titles = {title.strip().lower() for title in valid_titles}

    # Fetch the listing page
    paper_links = []
    for i in range(1, 8):
        if i == 1:
            page_url = f"{page_base}wpaper.html"
        else:
            page_url = f"{page_base}wpaper{i}.html"

        response = requests.get(page_url)
        if response.status_code != 200:
            print(f"Error fetching the page: {page_url} (Status: {response.status_code})")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = "https://ideas.repec.org"

        ul_elements = soup.find_all('ul', class_='list-group paperlist')
        for ul in ul_elements:
        # Each paper is in a <li> element with class "list-group-item downfree"
            li_elements = ul.find_all('li', class_='list-group-item downfree')
            for li in li_elements:
                # Locate the <a> tag within the <B> tag
                a_tag = li.find('a', href=True)
                if a_tag:
                    href = a_tag['href']
                    # Convert relative URLs to absolute URLs
                    if not href.startswith("http"):
                        href = base_url + href
                    title = a_tag.get_text(strip=True)
                    paper_links.append({'title': title, 'url': href})
        
    print("Total Papers Collected", len(paper_links))
    
    filtered_papers = []
    
    # Visit each paper URL to extract abstract and apply keyword filtering
    for idx, paper in enumerate(paper_links):
        paper_url = paper['url']
        paper_response = requests.get(paper_url)
        if paper_response.status_code != 200:
            print(f"Error fetching paper: {paper_url} (Status: {paper_response.status_code})")
            continue
        
        paper_soup = BeautifulSoup(paper_response.text, 'html.parser')
        abstract = ""
        
        # Look for a tag with class "abstract" 
        abstract_tag = paper_soup.find("div", id="abstract-body")
        if abstract_tag:
            abstract = abstract_tag.get_text(strip=True)
            # print(abstract)

        authors = ""
        year = ""
        citation_div = paper_soup.find("div", id="biblio-body")
        if citation_div:
            citation_text = citation_div.get_text(" ", strip=True)
            # Use a regex to extract authors and year (e.g., "Kao-Lee Liaw & William Frey, 2008")
            m = re.search(r"(.+?),\s*(\d{4})", citation_text)
            if m:
                authors = m.group(1)
                year = m.group(2)
                # print("authors", authors)
                # print("year", year)

        # Extract citations from the "cites-tab" element
        citations = "0"
        cites_tab = paper_soup.find("a", id="cites-tab")
        if cites_tab:
            cites_text = cites_tab.get_text(strip=True)
            m = re.search(r"(\d+)\s+Citations", cites_text)
            if m:
                 citations = m.group(1)
        
        # If an abstract is found and it contains any FSRDC keyword, record the paper
        if abstract and contains_fsrdc_keyword(abstract):
            # Find the first keyword that appears in the abstract
            first_match = next((keyword for keyword in fsrdc_keywords if keyword in abstract.lower()), None)
            if first_match:
                dataname = first_match
                datacode = dataname_to_code[dataname]
            
            paper_authors = [a.strip().lower().replace('.', '') for a in authors.split("&")] if authors else []
            # print("paper_authors", paper_authors)
            if not any(author in valid_researchers for author in paper_authors):
                print(f"Skipping paper '{paper['title']}' because none of its authors are in the researchers list.")
                continue

            # Check if the scraped paper title is in the set of titles.
            paper_title_lower = paper['title'].strip().lower()
            if paper_title_lower in valid_titles:
                print(f"Duplicate paper '{paper['title']}'")
                continue

            filtered_papers.append({
                'Title': paper['title'],
                'Authors': authors,
                'Abstract': abstract,
                'Year': year,
                'Dataname' : dataname,
                'Datacode' : datacode,
                'Citations': citations,
                'Url': paper_url
            })
        print(idx, len(filtered_papers))

    print(len(filtered_papers))
    return filtered_papers

# URL provided for scraping
page_base = "https://ideas.repec.org/s/cen/"

# Scrape papers from the RePEc listing and filter based on FSRDC keywords
filtered_papers = scrape_repec_papers(page_base)
df = pd.DataFrame(filtered_papers)
df.to_csv("web_scraping.csv", index=False)
