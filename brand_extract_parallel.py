'''
Functions to extract Brand information from inventory data.
main: extracts brand information
check: checks against a reference file

Depenencies:
    - brand_abbrevs: dictionary of abbreviations for common brand names, e.g. CATERPILLAR --> CAT.

Last updated: 07-07-20

'''

#import modules
import pandas as pd
import numpy as np
import pathlib
import re
import time
import multiprocessing as mp
from functools import partial

#Set some pandas options (only for viewing data)
pd.options.display.max_rows = 20
pd.options.display.max_columns = 5
pd.options.display.max_colwidth = 200

def parallelize_dataframe(df, func, brandlist, n_cores=mp.cpu_count()-1):
    df_split = np.array_split(df, n_cores)
    pool = mp.Pool(n_cores)
    df = pd.concat(pool.map(partial(regex_process, brandlist=brandlist), df_split))
    pool.close()
    pool.join()
    return df

def regex_process(df, brandlist):
    # #start loop in reverse order
    for num, i in enumerate(brandlist[::-1]):
        print(num, sep=' ', end=' ', flush=True)
        if i == 'LG':
            regex = re.compile(r'(?<=(?:[^MNRT"]\W|[^MNRT"]\s))\bLG\b(?!\sSLV|\sRAD|\sMOUNT)') #- BROKEN need to fix!
        elif i == '3M':
            regex = re.compile(r'(?<=(?:[A-Za-z0-9];|[A-Za-z0-9]\s|\W\W|\s\s|\W\s))\b3M\b(?!LG|\sLG|\sLENGTH|\sLONG)')
        else:
            regex = re.compile(r"(?<=(?:[A-Za-z0-9]\W|[A-Za-z0-9]\s|\s\s|\W\s|\W\W))\b"+i.upper()+r"\b")
        df['Brand'][df["text"].str.upper().str.contains(regex, regex=True)] = i.upper()
    return df

def detect_brands(cdf, brandlist=True, output_brandlist=False):

    #Code to run as function with brandlist already present in file
    cdf['text'].fillna('BLANK', inplace=True)
    if brandlist:
        # brands = list(cdf['Stock Master Combined[Brand v2]'].value_counts().index.values)
        brands = ['LG', 'KOMATSU', 'CAT']
    else:
        brands = pd.DataFrame(file_utils.read_csv(brandlist))
        brands = list(brands.Brand.values)

    #Remove all single quote marks (apostrophes)
    cdf["text"] = cdf["text"].str.upper().replace(r"'", '', regex=True)

    # #start loop in reverse order
    cdf = parallelize_dataframe(cdf, regex_process, brands)
    
    #Correct common spelling mistakes/abbreviations etc - need to automate with regexes!
    #Should create a dictionary of abbreviations/common spelling mistakes etc - do this for the top brands.
    babbrvs = pd.DataFrame(file_utils.read_csv('brand_abbrevs.csv'))
    for num, bi in enumerate(babbrvs.brandname.values):
        regex = re.compile(r"(?<=(?:[A-Za-z0-9]\W|[A-Za-z0-9]\s|\s\s|\W\s|\W\W))\b"+bi.upper()+r"\b")
        cdf['Brand'][cdf["text"]
        .str.upper().str.contains(regex, regex=True)] = babbrvs.to_use[babbrvs.brandname==bi].str.upper()

    ###SAVE cdf WITH NEW BRAND COLUMN
    if time.gmtime().tm_mon < 10:
        ms = '0'
    else:
        ms = ''
    if time.gmtime().tm_mday < 10:
        ds = '0'
    else:
        ds = ''

    #cdf.to_csv(fname.split('.csv')[0]+' ('+str(time.gmtime().tm_year)+ms+str(time.gmtime().tm_mon)+ds+str(time.gmtime().tm_mday)+').csv', index=False)

    #Save new brandlist
    #if output_brandlist:
    #    cdf['Brand v2'].value_counts().to_frame().to_csv('./brandlist'+'_'+ds+str(time.gmtime().tm_mday)+'-'+ms+str(time.gmtime().tm_mon)+'-'+str(time.gmtime().tm_year)[:2]+'.csv')

    print('DONE!')
    return cdf


def check(f1, bname, fref):
    '''
    Check number of instances of brand name against refeence file
    Current reference file: Stock Master Combined (20200630).xlsx
    '''

    print('CHECK Function')

    #Load data
    df1 = pd.read_csv(f1, header=0, usecols=[0, 1, 20], encoding='utf-8')

    dfref = pd.read_csv(fref, header=0, usecols=[0, 1, 20], encoding='utf-8')

    #Fill blank data
    df1['text'].fillna('BLANK', inplace=True)
    dfref['text'].fillna('BLANK', inplace=True)

    # print(df1.head(5))
    
    #Create brand name regex
    regex = re.compile(bname)
    print('regex ', regex)

    #Run test using contains functions
    x = df1[df1['text'].str.upper().str.contains(regex, regex=True)]
    ref = dfref[dfref['text'].str.upper().str.contains(regex, regex=True)]
    
    #Print results
    print('REF shape = ', ref.shape)
    print('File shape = ', x.shape)

    #Check based on [Brand v2] column
    xx = df1[df1['Brand v2'] == bname]
    ref2 = dfref[dfref['Brand v2'] == bname]
    #Print results
    print('REF [Band v2] shape = ', ref2.shape)
    print('File [Brand v2] shape = ', xx.shape)

    print('DONE')
    print(' ')

if __name__=="__main__":
    import sys
    print(len(sys.argv))
    if len(sys.argv) < 2 or sys.argv[1] not in ['run', 'check']:
        print('First argument must be one of: run, check')
        print('python brand_extract.py run [filename] [brandlist(True or name_of_brandlist_file)] [outputbrandlist(Bool)]')
        print(' ')
        print('python brand_extract.py run [filename] [brandname_to_check] [reference_filename]')
        print(' ')
        sys.exit()
    elif sys.argv[1] == 'run':
        main(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'check':
        check(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit()
