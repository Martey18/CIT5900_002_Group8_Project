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


def fsrdc_check(text):
    """
    This function checks whether the paper is fsrdc related. It will be applied to ,ultiple columns like abstract and affiliations
    """
    keywords = ['Census Bureau','FSRDC','RDC','Census','IRS','BEA']
    datanames = ["Annual Survey of Manufactures","Auxiliary Establishment - ES9200","Census of Construction Industries","Census of Finance, Insurance, and Real Estate","Census of Manufactures","Census of Mining","Census of Retail Trade","Census of Services","Census of Transportation, Communications, and Utilities","Census of Wholesale Trade","Enterprise Summary Report - ES9100 (large company)","Standard Statistical Establishment Listing","Standard Statistical Establishment List - non Name and Address File","Decennial Census","Decennial Employer-Employee Database","Longitudinal Business Database - No Revenue","Non-Employer Business Register","Manufacturing Energy Consumption Survey","Survey of Pollution Abatement Costs and Expenditures","Medical Expenditure Panel Survey - Insurance Component: AHRQ Version","Current Population Survey March Supplement","Commodity Flow Survey","Medical Expenditure Panel Survey - Insurance Component","Medicaid Eligibility Database System - California","Unemployment Insurance-Base Wage File -- California","Survey of Manufacturing Technology","National Crime Victimization Survey","American Housing Survey","BLS - National Longitudinal Survey (Original Cohorts Geocode)","Survey of Industrial Research and Development","American Community Survey","Survey of Plant Capacity Utilization","Survey of Income and Program Participation - Longitudinal","Survey of Income and Program Participation (SIPP) Panels","Quarterly Financial Report","Survey of Business Owners","Annual Capital Expenditures Survey","National Survey of Homeless Assistance Providers and clients","Business Expenditures Survey","Compustat-SSEL Bridge","Ownership Change Database","SIPP Public-Use Crosswalk","CPS Crosswalk","LEHD Business Register Bridge (BRB) - 2004","LEHD Employer Characteristics File (ECF) - 2004","LEHD Quarterly Workforce Indicators (QWI) - 2008","National Employer Survey","LEHD Geocoded Address List (GAL) - 2004","Exporter Database","Foreign Trade Data - Export","Foreign Trade Data - Import","American Community Survey Unedited Microdata","LEHD Employer Characteristics File (ECF) - 2008","LEHD Employment History File (EHF) - 2008","LEHD Individual Characteristics File (ICF) - 2008","LEHD Unit-to-Worker (U2W) - 2008","Characteristics of Business Owners-Firms and Owners Extract","Quarterly Financial Report Census Years","LEHD Business Register Bridge (BRB) - 2008","Service Annual Survey","Economic Census of Puerto Rico","LEHD Geocoded Address List (GAL) - 2008","Form 5500 Bridge File","Integrated Longitudinal Business Database","Quarterly Survey of Plant Capacity Utilization (formerly known as PCU)","LEHD Employer Characteristics File (ECF) - 2011","LEHD Employment History File (EHF) - 2011","LEHD Individual Characteristics File (ICF) - 2011","LEHD Unit-to-Worker (U2W) - 2011","Longitudinal Foreign Trade Transactions Database","BOC PIK Crosswalk Survey of Income and Program Participation (SIPP)","SSA Detailed Earnings Record (DER) SIPP Extract","SSA Master Beneficiary Record (MBR) SIPP Extract","SSA 831 Disability File SIPP Extract","SSA Summary Earnings Record (SER) SIPP Extract","LEHD Successor-Predecessor File (SPF) - 2008","Public Patent Data - No PII","Longitudinal Business Database - With EIN and Revenue","BOC PIK Crosswalk Census Unedited File (CUF)","Kauffman Firm Survey","Business Enterprise Research and Development Survey (BERD)","BOC PIK Crosswalk Transunion Credit File","Transunion Credit File","Annual Retail Trade Survey","Current Industrial Reports","NBER-CES Manufacturing Industry Database (Public Use Dataset)","National Longitudinal Mortality Study","Manufacturers' Shipments, Inventories, and Orders","BOC Consolidated PIK Crosswalk Current Population Survey (CPS)","BOC PIK Crosswalk American Community Survey (ACS)","BOC PIK Crosswalk Current Population Survey-ASEC (CPS)","LEHD Business Register Bridge (BRB) - 2011","LEHD Employer Characteristics File (ECF) T26 Components - 2011","LEHD Individual Characteristics File (ICF) T26 Components - 2011","LEHD Quarterly Workforce Indicators (QWI) - 2011","Annual Wholesale Trade Survey","BOC Master Address File Auxiliary Reference File (MAFARF)","Master Address File Extract","LEHD Individual Characteristics File (ICF) T26 Components - 2008","LEHD Geocoded Address List (GAL) - 2011","LEHD Employer Characteristics File (ECF) - 2014","LEHD Employment History File (EHF) - 2014","LEHD Geocoded Address List (GAL) - 2014","LEHD Individual Characteristics File (ICF) - 2014","LEHD Quarterly Workforce Indicators (QWI) - 2014","LEHD Unit-to-Worker (U2W) - 2014","LEHD Employer Characteristics File (ECF) T26 Components - 2014","LEHD Individual Characteristics File (ICF) T26 Components - 2014","Survey of Water Use in Manufacturing [Mineral Industries]","CMS Medicaid Statistical Information System (MSIS)","LEHD Person-Level Demographics (Workers Only; ICF demographics)","LEHD Job-Level Files (EHF, JHF)","Disclosure Avoidance Population Tables","BOC Census Numident (CNUM)","Current Population Survey Food Security Supplement","Annual Business Survey","Census Edited File","BOC Consolidated PIK Crosswalk Survey of Income and Program Participation (SIPP)","Supplementary Public Data - Geographic Codes","Intellectual Property Public Patent Data PIK Crosswalk","Intellectual Property Public Patent Data - No PII","LEHD Employer-Level Files (ECF, SPF, QWI; non-T26)","LEHD Employer-Level File T26 (ECF; T26)","National Survey of College Graduates","National Survey of College Graduates Crosswalk","Survey of Doctoral Recipients","BOC PIK Xwalk Srvy Earned Doctorates (SED) and Srvy Doctoral Recipients (SDR)","Survey of Earned Doctorates","Supplementary Public Data - Price Indices","UMETRICS University Research Data","Police-Public Contact Survey","Harmonized Decennial Census","Current Population Survey Voting and Registration Supplement","Supplementary Public Data - Economic Indicators and Other Industry Metrics","LEHD Person-Level Residence (Workers Only; ICF Residence)","CMS Medicare Enrollment Database (EDB)","Supplementary Public Data - Industry and Product Codes","Supplementary Public Data - International and Trade Data","ReDFAR Special Extract for Project 1518","Monthly Retail Trade Survey","Monthly Wholesale Trade Survey","Decennial Census Content Reinterview Survey","LEHD Successor-Predecessor File (SPF) - 2014","SIPP Event History Calendar (EHC)","National Compensation Survey All Benefits Quarterly","LEHD Geocoded Address List (GAL) T26 Components - 2014","LEHD Quarterly Workforce Indicators (QWI) Public Use Files - 2011","Census Coverage Measurement","Commercial Experian End-Dated Records (EDR)","Census Unedited File","Annual Survey of Entrepreneurs","BOC Crosswalk 1940 IPUMS Research","CMS Transformed Medicaid Statistical Information System (TMSIS)","1940 IPUMS Research","Mortality Disparities in American Communities","Current Population Survey Computer and Internet Use Supplement","Current Population Survey Tobacco Use Supplement","Commercial Columbia University Deeds","Texas A&M University - Hand-collected Individual-level Demogr Data","Current Population Survey Volunteering and Civic Life Supplement","Current Population Survey Volunteer Supplement","Supplementary Public Data - County Characteristics","Annual Integrated Economic Survey","Business Trends and Outlook Survey","Census Household Composition Key File","Household Pulse Survey","Small Business Pulse Survey","SSA Detailed Earnings Record (DER) CPS Extract","Department of the Treasury State Small Business Credit Initiative","SSA Payment History Update System (PHUS) SIPP Extract","SSA Supplemental Security Record (SSR) SIPP Extract","State - Education - University of Central Florida, MIMFI","State - Education - University of California, Irvine (UCI) Criminal Justice (CJ)","University of Chicago - New Mexico Corrections Department (NMCD)","University of Michigan - CJARS","Commercial CoreLogic Automated Value Model (AVM)","Commercial CoreLogic Buildings","Commercial CoreLogic Property Deeds","Commercial CoreLogic Foreclosure (FC)","Commercial Corelogic Home Owner Association (HOA)","Commercial CoreLogic Multiple Listing Services (MLS)","Commercial CoreLogic Multiple Listing Services (MLS) Basement","Commercial CoreLogic Open Liens (OLS)","Commercial CoreLogic Tax","Commercial CoreLogic Tax History","Rental Housing Finance Survey","USDA Rural Establishment Innovation Survey (REIS)","National Survey of Children's Health","SSA 831 Disability File CPS Extract","SSA Summary Earnings Record (SER) CPS Extract","SSA Supplemental Security Record (SSR) CPS Extract","HUD Moving to Opportunity","HUD Moving to Opportunity (Restricted - DOB)","University of Chicago - of L2 National Voter File (L2)","CPS Civic Engagement Supplement","SBA Loan Program 7A","State - SNAP and TANF - Connecticut","State - SNAP and TANF - Iowa","State - SNAP and TANF - Idaho","State - SNAP and TANF - Mississippi","State - SNAP and TANF - North Dakota","State - SNAP and TANF - South Carolina","State - SNAP and TANF - Utah","State - Supplemental Nutrition Assistance Program (SNAP) - Arizona","State - Supplemental Nutrition Assistance Program (SNAP) - Indiana","State - Supplemental Nutrition Assistance Program (SNAP) - Michigan","State - Supplemental Nutrition Assistance Program (SNAP) - Wyoming","American Community Survey (ACS) and Linked HUD-Subsidized Administrative data","HUD Tenant Rental Assistance Certification System (TRACS)","HUD Public and Indian Housing Information Center (PIC)","HUD PIC and TRACS Longitudinal","Importer Database","Quarterly Services Survey","American Community Survey Public Use Microdata Sample","Address Control FIle","BOC PIK Crosswalk American Housing Survey (AHS)","Commercial Black Knight Master Address Data (ADDR)","Commercial Black Knight Assignment of Mortgage Data (ASGN)","Commercial Black Knight Assessment Data (ASMT)","Commercial Black Knight Automated Valuation Models Data (AVM)","Commercial Black Knight Deeds Data (DEED)","Commercial Black Knight Active Loan Data (LOAN)","Commercial Black Knight Multiple Listing Service Data (MLS)","Commercial Black Knight Notice of Delinquency (Pre Foreclosure) Data (NOD)","Commercial Black Knight Parcel Boundary Data (PB)","Commercial Black Knight Release of Mortgage Data (REL)","Commercial Black Knight Stand-Alone Mortgage Data (SAM)","BOC PIK Crosswalk American Community Survey (ACS) Puerto Rico (PR)","HHS Temporary Assistance to Needy Families (TANF) Recipients File","State - SNAP and TANF - North Carolina","State - SNAP and TANF - Nebraska","State - SNAP and TANF - Nevada","State - SNAP and TANF - Oregon","State - SNAP and TANF - South Dakota","State - Supplemental Nutrition Assistance Program (SNAP) - Illinois","State - Supplemental Nutrition Assistance Program (SNAP) - Massachusetts","State - Supplemental Nutrition Assistance Program (SNAP) - Maryland","State - Supplemental Nutrition Assistance Program (SNAP) - Montana","State - Temporary Assistance for Needy Families (TANF) - Arizona","State - Temporary Assistance for Needy Families (TANF) - Hawaii","State - Temporary Assistance for Needy Families (TANF) - Indiana","State - Temporary Assistance for Needy Families (TANF) - Massachusetts","State - Temporary Assistance for Needy Families (TANF) - Michigan","State - Temporary Assistance for Needy Families (TANF) - Montana","State - Women, Infants and Children (WIC) - Alabama","State - Women, Infants and Children (WIC) - Arizona","State - Women, Infants, and Children (WIC) - Colorado","State - Women, Infants, and Children (WIC) - Connecticut","State - Women, Infants, Children (WIC) Iowa","State - Women, Infants and Children (WIC) - Idaho","State - Women, Infants, and Children (WIC) - Illinois","State - Women, Infants, and Children (WIC) - Kansas","State - Women, Infants, and Children (WIC) - Maine","State - Women, Infants and Children (WIC) - Michigan","State - Women, Infants, and Children (WIC) - Montana","State - Women, Infants, and Children (WIC) - South Dakota","State - Women, Infants, and Children (WIC) - Utah","State - Women, Infants and Children (WIC) - Washington","State - Women, Infants, and Children (WIC) - Wisconsin","National Student Clearinghouse Education Data - NAM","University of Minnesota - Navajo Nation","Census IPUMS Research","American Community Survey Paradata","Commercial DAR Partners","Commercial Experian Insource (INSRC)","Commercial Infogroup","Commercial Melissa Data Base","Commercial Targus National Address File (NAF)","Commercial Targus Federal Consumer","Commercial Targus Pure Wireless","Commercial VSGI Consumer Referential Database","Commercial VSGI Tracker (TRK)","Planning Database (PDB)","FDIC Small Business Lending Survey - Preliminary Data","BOC Best race and ethnicity administrative records file","BOC Best Race and Ethnicity Admin Records Modified","State - Education - Georgetown University Characteristics of Civil Court Partici","State - Eviction Data for Cook County, IL","State - Homeless Management Information System (HMIS) - All Chicago","USPS National Change of Address (NCOA)","BLS - Meta Information Survey of Occupational Injuries and Illnesses (SOII) Esta","BLS - Survey of Occupational Injuries and Illnesses (SOII) Case and Demographics","BLS - Survey of Occupational Injuries and Illnesses (SOII) Summary Records","Business Dynamics Statistics (BDS)","State - State Tax - California","BLS National Longitudinal Surveys Youth (NLSY) Adult PIK79","BLS National Longitudinal Surveys Youth (NLSY) Adult PIK97","BLS National Longitudinal Surveys Youth (NLSY) Child PIK79","BLS - NLSY79 Census and Zip (Active Cohort)","BLS - NLSY97 Census and Zip (Active Cohort)","NCVS Contact History Instrument (CHI)","Household Pulse Survey Additional Geograpic Information","NCVS School Crime Supplement","SBA Disaster Loan Data","SBA Disaster Loan Data Business Applicants (BA)","SBA Disaster Loan Data Business Decisions (BD)","SBA Disaster Loan Data Business Insurance (BI)","SBA Disaster Loan Data Business Loan Status (BLS)","SBA Disaster Loan Data Business Up (BU)","TargetSmart Voter Data","BOC PIK Crosswalk CPS School Enrollment Supplement","CPS School Enrollment Supplement","Commodity Flow Survey - T13","Manufacturers' Unfilled Orders Survey","National Sample Survey of Registered Nurses","SSA Master Beneficiary Record (MBR) CPS Extract","SBA COVID Economic Injury Disaster Loan (EIDL)","SBA Paycheck Protection Program (PPP)","SBA Restaurant Revitalization Fund (RRF)","SSA Master Beneficiary Record (MBR)","SBA Disaster Loan Data Home Applicants (HA)","SBA Disaster Loan Data Home Decisions (HD)","SBA Disaster Loan Data Home Up (HU)","BOC PIK Crosswalk Current Population Survey (CPS) Food Security Data","BOC PIK Crosswalk National Crime Victimization Survey (NCVS)","Current Population Survey Fertility Supplement","SSA Detailed Earnings Record (DER) ACS Extract","SSA Summary Earnings Record (SER) ACS Extract","SSA Supplemental Security Record (SSR) ACS Extract","State - Supplemental Nutrition Assistance Program (SNAP) - California LACO","International Price Program (IPP)","Producer Price Index","Commercial Legal Services Corporation (LSC) Eviction Data","DVA US Veterans","HUD PIC and TRACS","HUD Public and Indian Housing Information Center (PIC) Full Extract","HUD PIC Extract","HUD TRACS Extract","Commercial RealtyTrac Foreclosure","CPS Unbanked/Underbanked Supplement","Open Research Lab - Unconditional Cash Transfers","SSA Supplemental Security Record (SSR)","Commercial Private Capital Research Institute (PCRI) - Enhanced Private Equity","SBA Portfolio of 8(a) Certified Business (8ACERT)","SBA Dynamic Small Business Search (DSBS)","SBA Loan Program 504","State - Supplemental Nutrition Assistance Program (SNAP) - Colorado"
]
    datacodes = ['ASM','AUX','CCN','CFI','CMF','CMI','CRT','CSR','CUT','CWH','ESR','SSL','SSL_XNA','CEN','DEE','LBD','NBR','MECS','PAC','AHR','CPS','CFS','MEP','MED','UIW-CA','SMT','NCVS','AHS','NLS','SIRD','ACS','PCU','SIP-LON','SIPP','QFR','SBO','ACE','NSH','BES','CSB','OCD','SXW','CXW','LEHD-BRB-2004','LEHD-ECF-2004','LEHD-QWI-2008','NES','LEHD-GAL-2004','EDB','EXP','IMP','ACSUNEDIT','LEHD-ECF-2008','LEHD-EHF-2008','LEHD-ICF-2008','LEHD-U2W-2008','CBOE','QFRCEN','LEHD-BRB-2008','SAS','CIAPR','LEHD-GAL-2008','F55BF','ILBD','QPC','LEHD-ECF-2011','LEHD-EHF-2011','LEHD-ICF-2011','LEHD-U2W-2011','LFTTD','CENSUS_CROSSWALK_SIPP','SSA_DER_SIPP','SSA_MBR_SIPP','SSA_S831_SIPP','SSA_SER_SIPP','LEHD-SPF-2008','PATENT_NOPII','LBDREV','CENSUS_CROSSWALK_CUF','KFS','BERD','CENSUS_CROSSWALK_TU','COMM_TU','ARTS','CIR','NBERCES_PUBLIC','NLMS','M3','CENSUS_CONSXWALK_CPS','CENSUS_CROSSWALK_ACS','CENSUS_CROSSWALK_CPS','LEHD-BRB-2011','LEHD-ECFT26-2011','LEHD-ICFT26-2011','LEHD-QWI-2011','AWTS','CENSUS_CROSSWALK_MARF','MAFX','LEHD-ICFT26-2008','LEHD-GAL-2011','LEHD-ECF-2014','LEHD-EHF-2014','LEHD-GAL-2014','LEHD-ICF-2014','LEHD-QWI-2014','LEHD-U2W-2014','LEHD-ECFT26-2014','LEHD-ICFT26-2014','SWUM','CMS_MSIS','LEHD_DEMO','LEHD_JOBS','POP_TABLES','CENSUS_CNUM','CPSFS','ABS','CEF','CENSUS_CONSXWALK_SIPP','GEO_CODES','IP_INVENTOR_CROSSWALK','IP_PUBLIC_NOPII','LEHD_EMPLOYERS','LEHD_EMPLOYERS_T26','NSCG','NSCG_XWALK','NSF_NCSES_SDR_NONPVS','NSF_NCSES_SED','NSF_NCSES_SED_NONPVS','PRICE_INDICES','UMT','NCVSPPCS','HCEN','CPSVR','ECON_INDICATORS','LEHD_RESIDENCE','CMS_EDB','IND_PROD_CODES','INTL_TRADE_DATA','SE1518','MRTS','MWTS','CENCRS','LEHD-SPF-2014','SIPP-EHC','ABQ','LEHD-GALT26-2014','LEHD-QWIPU-2011','CCM','COMM_EXP_EDR','CUF','ASE','CENSUS_CROSSWALK_1940_IPUMS','CMS_TMSIS','COMM_1940_IPUMS_RESEARCH','MDAC','CPSCIUS','CPSTUS','COMM_CU_DEEDS','TAMU_HIDD','CPSVACL','CPSVOL','PUBLIC_COUNTY','AIES','BTOS','CENSUS_HH_COMP_KEY','HH_PULSE_SURVEY','SBPS','SSA_DER_CPS','SSBCI','SSA_PHUS_SIPP','SSA_SSR_SIPP','STATE_EDU_UCF_MIMFI','STATE_EDU_UCI_CJ','UCHICAGO_NMCD','UM_CJARS','COMM_CORELOGIC_AVM','COMM_CORELOGIC_BLDGS','COMM_CORELOGIC_DEED','COMM_CORELOGIC_FC','COMM_CORELOGIC_HOA','COMM_CORELOGIC_MLS','COMM_CORELOGIC_MLSBSMNT','COMM_CORELOGIC_OLS','COMM_CORELOGIC_TAX','COMM_CORELOGIC_TXHST','RHFS','USDA_REIS','NSCH','SSA_S831_CPS','SSA_SER_CPS','SSA_SSR_CPS','HUD_MTO','HUD_MTO_RESTRICTED','UCHICAGO_L2','CPSCIVIC','SBA_LOANPROG7A','STATE_SNAPTANF_CT','STATE_SNAPTANF_IA','STATE_SNAPTANF_ID','STATE_SNAPTANF_MS','STATE_SNAPTANF_ND','STATE_SNAPTANF_SC','STATE_SNAPTANF_UT','STATE_SNAP_AZ','STATE_SNAP_IN','STATE_SNAP_MI','STATE_SNAP_WY','ACSHUD','HUD-TRACS','HUD_PIC','HUD_PICTRACS_LNGTDNL','IDB','QSS','ACSPUMS','ACF','CENSUS_CROSSWALK_AHS','COMM_BLACKKNIGHT_ADDR','COMM_BLACKKNIGHT_ASGN','COMM_BLACKKNIGHT_ASMT','COMM_BLACKKNIGHT_AVM','COMM_BLACKKNIGHT_DEED','COMM_BLACKKNIGHT_LOAN','COMM_BLACKKNIGHT_MLS','COMM_BLACKKNIGHT_NOD','COMM_BLACKKNIGHT_PB','COMM_BLACKKNIGHT_REL','COMM_BLACKKNIGHT_SAM','CENSUS_CROSSWALK_ACS_PR','HHS_TANF','STATE_SNAPTANF_NC','STATE_SNAPTANF_NE','STATE_SNAPTANF_NV','STATE_SNAPTANF_OR','STATE_SNAPTANF_SD','STATE_SNAP_IL','STATE_SNAP_MA','STATE_SNAP_MD','STATE_SNAP_MT','STATE_TANF_AZ','STATE_TANF_HI','STATE_TANF_IN','STATE_TANF_MA','STATE_TANF_MI','STATE_TANF_MT','STATE_WIC_AL','STATE_WIC_AZ','STATE_WIC_CO','STATE_WIC_CT','STATE_WIC_IA','STATE_WIC_ID','STATE_WIC_IL','STATE_WIC_KS','STATE_WIC_ME','STATE_WIC_MI','STATE_WIC_MT','STATE_WIC_SD','STATE_WIC_UT','STATE_WIC_WA','STATE_WIC_WI','NSC_NAM','UMN_NAVAJONATION','COMM_CENSUS_IPUMS_RESEARCH','ACSP','COMM_DAR_PARTNERS','COMM_EXP_INSRC','COMM_INFOGROUP','COMM_MELISSA','COMM_TARGUS_ADDRESS','COMM_TARGUS_FEDCONSUMER','COMM_TARGUS_WIRELESS','COMM_VSGI_CRD','COMM_VSGI_TRK','PDB_PUBLIC','SBLS_FDIC','CENSUS_BESTRACE','CENSUS_BESTRACE_NONRSTRCT','STATE_EDU_GU_CCCP','STATE_EVIC_ILCH','STATE_HMIS_ALL_CHI','USPS_NCOA','SOII_A','SOII_C','SOII_S','BDS','STATE_TAX_CA','BLS_NLSY_ADULT_PIK79','BLS_NLSY_ADULT_PIK97','BLS_NLSY_CHILD_PIK79','Y79CZ','Y97CZ','NCS_CHI','HH_PULSE_SURVEY_GEO','NCVSSCS','SBA_DLD','SBA_DLD_BA','SBA_DLD_BD','SBA_DLD_BI','SBA_DLD_BLS','SBA_DLD_BU','TSMART_VOTER','CENSUS_CROSSWALK_CPSSCHOOL','CPSSCHOOL','CFS_T13','M3UFO','NSSRN','SSA_MBR_CPS','SBA_COVID_EIDL','SBA_PPP','SBA_RRF','SSA_MBR','SBA_DLD_HA','SBA_DLD_HD','SBA_DLD_HU','CENSUS_CROSSWALK_CPS_FS','CENSUS_CROSSWALK_NCVS','CPSFERT','SSA_DER_ACS','SSA_SER_ACS','SSA_SSR_ACS','STATE_SNAP_CA_LACO','IPP','PPI','COMM_LSC_EVICT','DVA_USVETS','HUD_PICTRACS','HUD_PIC_FULL_XTRCT','HUD_PIC_XTRCT','HUD_TRACS_XTRCT','COMM_REALTYTRAC','CPSUU','COMM_ORL_SEIUCT','SSA_SSR','COMM_PCRI_EPE','SBA_8ACERT','SBA_DSBS','SBA_LOANPROG504','STATE_SNAP_CO'
]
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords) or any(kw.lower() in text_lower for kw in datanames) or any(kw.lower() in text_lower for kw in datacodes)


def step3(webapifilepath,researchfilepath):
    #load the two files needed
    try:
        webapidf = pd.read_csv(webapifilepath)
        researchoutputdf = pd.read_excel(researchfilepath)

        #run uniquenes check with error handling
        try:
            print("Files loaded successfully")
            uniquedf = unique_check(webapidf,researchoutputdf)

            #run fsrdc checks against abstracts, datanames and datacodes
            try:
                uniquedf['FSRDC_related'] = uniquedf['abstract'].apply(fsrdc_check) or uniquedf['dataname'].apply(fsrdc_check) or uniquedf['datacode'].apply(fsrdc_check)
                print("Step 3 completed successfully")
                return uniquedf[uniquedf['FSRDC_related']==True]

            except Exception as e:
                print("Error with FSRDC related checks:",e)

        except Exception as e:
            print("Error running uniqueness:",e)



    except Exception as e:
        print("Error loading file:", e)
    

#run step 3
webapifilepath = ''
researchfilepath = 'https://github.com/dingkaihua/fsrdc-external-census-projects/blob/master/ResearchOutputs.xlsx'
step3file = step3(webapifilepath,researchfilepath)
df.to_csv("ProcessedData.csv")