"""Common functions for commodity and row-to-row matching."""

import regex as re

def preprocess(string, abbrevs = []):
    '''
    Preprocess a string. Removes commas and semicolons, removes extra spaces,
    and expands abbreviations.
    INPUTS:
    - string to preprocess
    - abbreviations to replace. List of dicts with Abbreviation and Expanded keys.
    OUTPUTS:
    - set of preprocessed words
    '''
    #Lowercase, replace , and ; with spaces to prevent merging words
    string = string.lower().replace(",", " ").replace(";", " ")
    #Remove extra spaces we may have added
    string = " ".join(string.split())
    #Expand any abbreviations we may have
    for abbrev in abbrevs:
        string = string.replace(abbrev["Abbreviation"].lower(), abbrev["Expanded"].lower())
    return set(string.split(" "))

def to_base_word_set(word_string, abbrevs = []):
    word_string = word_string.lower()
    # Note that this may expand "abbreviations" which are part of another word. TODO: test and fix this.
    for abbrev in abbrevs:
        word_string = word_string.replace(abbrev["Abbreviation"].lower(), abbrev["Expanded"].lower())
    words = re.findall(r"[\w]+", word_string)
    base_words = [re.sub('\er$', '', re.sub('\ing$', '', w.lower().rstrip("s"))) for w in words]
    return set(base_words)

def most_matching_words(words_to_match, sentences_preprocessed, number_of_results, words_to_exclude):
    '''
    Function to calculate Jaccard distance between individual words.
    Preprocess words_to_match and sentences_preprocessed with to_base_word_set().
    sentences_preprocessed should be a {string: {"Preprocessed": to_base_word_set(string)}} dictionary.
    INPUTS:
     - words_to_match
     - sentences_preprocessed
     - number_of_results
     - words_to_exclude
    OUTPUTS:
     - matches_sorted[:limit]
     - scores_sorted[:limit]
    '''
    #print("Matching " + str(words_to_match))
    jaccard_index = {}
    try:
        for match_candidate in sentences_preprocessed:
            preprocessed_candidate = sentences_preprocessed[match_candidate]["Preprocessed"]
            words_to_match -= words_to_exclude
            intersection = len(preprocessed_candidate.intersection(words_to_match))
            jaccard_index[match_candidate] = intersection / (len(preprocessed_candidate) + len(words_to_match) - intersection)
        matches_sorted, scores_sorted = best_n_results(jaccard_index, number_of_results)
    except Exception as e:
        print(e)
        matches_sorted = ["NOT FOUND" for i in range(number_of_results)]
        scores_sorted = [0 for i in range(number_of_results)]
    #print("Finished " + str(words_to_match))
    return matches_sorted[:number_of_results], scores_sorted[:number_of_results]

def best_n_results(jaccard_index, n):
    commodities_sorted = sorted(list(jaccard_index.keys()), key=lambda commodity: -jaccard_index[commodity])
    scores_sorted = sorted(list(jaccard_index.values()), reverse=True)
    return commodities_sorted[:n], scores_sorted[:n]
