#This python file contains functions and scripts to load and clean the 2024 dataset and perform fuzzy matching for entity 
# resolution.

#import modules
import pandas as pd
from fuzzywuzzy import fuzz
import re
from tqdm import tqdm

#define functions
def text_normalize(text):
    '''
    This function will take a string as input and remove white spaces, lower letter and remove punctuations. To make it easier 
    to fuzzy match
    '''
    #test for whether inputs are string so no errors show with string functions
    if isinstance(text, str):
        return text.strip().lower().replace('.', '').replace(',', '').replace('-','').replace(' ','')
    else:
        print('Input must be string')
        return None

def fuzzy_match(title1, title2):
    '''This function will take two string inputs(titles being compared) and perform fuzzy matching with sort ratio and return 
    the score. This score shows how much the titles match

    '''
    #test for whether inputs are string so no errors show with string functions
    if isinstance(title1, str) & isinstance(title2,str):
        score = fuzz.token_sort_ratio(title1, title2)
        return score
    else:
        print('Input must be string')
        return None

def extract_doi(paperdoi):
    '''
    This function will extract dois from the links and also match matching easy by removing dots and slashes. Removing 'http'
    portion and slashes and dots
    '''
    if isinstance(paperdoi, str):
        #remove http portion, whitespace and lower
        paperdoi.lower().strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
        #remove slasheds and dots
        paperdoi.replace('.', '').replace('/', '')
        return paperdoi
    else:
        print('Input must be string')
        return None


def extract_doiref(reference):
    '''
    This function exctracts the dois in the reference
    '''
    if isinstance(reference,str):
        doi_pattern = r"10.\d{4,9}/[-._;()/:A-Z0-9]+"
        dois = re.findall(doi_pattern,reference, re.IGNORECASE)
        if len(dois)==0:
            return None
        return dois[0] #get first doi only. paper should only have 1
    else:
        print('Input must be string')
        return None




def unique_check(webapidf,researchoutputdf):
    '''
    This function takes the webscraped, api enhanced dataframes and the research output dataset and cchecks whether there are
    matches. It returns a new dataframe of web scraped, apiu enhanced papers that are not in research outputs dataset
    '''
    #extract and normalize doi rows from both dataframes
    researchoutputdf['Doi'] = researchoutputdf['OutputBiblio'].apply(extract_doiref) #get dois from reference
    researchoutputdf['DoiExtract'] = researchoutputdf['Doi'].apply(extract_doi) #normalize doi
    webapidf['DoiExtract'] = webapidf['doi'].apply(extract_doi) #normalize doi

    #normalize titles from both dataframes
    researchoutputdf['NormTitle'] = researchoutputdf['OutputTitle'].apply(text_normalize)
    webapidf['NormTitle'] = webapidf['title'].apply(text_normalize)

    Match_type = []
    TitleScore = []
    UniquePaper = []

    #loop through every paper in webapidf and check if it is unique
    for i, paperrow in tqdm(webapidf.iterrows(),total=len(webapidf)): #loop through each row and pull out the whole row
        #get the doi and title for the paper
        paptitle = paperrow['NormTitle']
        papdoi = paperrow['DoiExtract']

        #check doi exact match first and append
        if papdoi and papdoi in researchoutputdf['DoiExtract'].values:
            Match_type.append('Doi')
            TitleScore.append(None)
            UniquePaper.append(False)
        #if no doi or doi did not match
        else: #fuzzy match title
            #get fuzzy scores against each title in researchoutputs and get max value 
            fuzzy_scores = researchoutputdf['NormTitle'].apply(lambda x: fuzzy_match(paptitle, x))
            best_fuzz = max(fuzzy_scores)
            #if highest score is above threshold, it means match
            TitleScore.append(best_fuzz)
            if best_fuzz >= 90: #set threshold at 90 since that is most is seen online a lot
                Match_type.append('Title')
                UniquePaper.append(False)
            else: #no title or doi match
                Match_type.append(None)
                UniquePaper.append(True)

    #add new columns to dataframes
    webapidf['MatchType'] = Match_type
    webapidf['Uniqueness'] = UniquePaper
    webapidf['FuzzScores'] = TitleScore

    return webapidf[webapidf['Uniqueness']==True] #return dataframe with only unique papers

'''
#Excel URLs
webapifile = ''
researchoutsfile = 'https://github.com/dingkaihua/fsrdc-external-census-projects/blob/master/ResearchOutputs.xlsx'

#Load excels
try:
    researchoutputdf = pd.read_excel(researchoutsfile)
    webapidf = pd.read_excel(webapifile)

except Exception as e:
    print(f"Error loading file(s): {e}")


#Run uniqueness check
try: 
    Uniquedf = unique_check(webapidf,researchoutputdf)

except Exception as e:
    print(f"Error with Uniquenes check: {e}")
'''

#still to add fsrdc checks functions and code