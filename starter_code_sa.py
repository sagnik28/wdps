import gzip
from bs4 import BeautifulSoup
from bs4.element import Comment
from warcio.archiveiterator import ArchiveIterator
from conversion import html_to_text, parse_html
from utils import NLP1, get_NER, NLP2
from test_elasticsearch_server import search
from strsimpy.cosine import Cosine


KEYNAME = "WARC-Record-ID"


# The goal of this function process the webpage and returns a list of labels -> entity ID
def find_keys(payload):
    if payload == '':
        return

    # The variable payload contains the source code of a webpage and some additional meta-data.
    # We firt retrieve the ID of the webpage, which is indicated in a line that starts with KEYNAME.
    # The ID is contained in the variable 'key'
    key = None
    for line in payload.splitlines():
        if line.startswith(KEYNAME):
            key = line.split(': ')[1]
            return key;

def cos_sim(str1,str2):
    cosine = Cosine(2)
    p1 = cosine.get_profile(str1)
    p2 = cosine.get_profile(str2)
    score = cosine.similarity_profiles(p1, p2)
    return score

def generate_candidates(NER_mention):
    candidates = None
    candidates = search(NER_mention).items()
    return candidates

def split_records(stream):
    payload = ''
    for line in stream:
        if line.strip() == "WARC/1.0":
            yield payload
            payload = ''
        else:
            payload += line
    yield payload

if __name__ == '__main__':
    import sys
    try:
        _, INPUT = sys.argv
    except Exception as e:
        print('Usage: python starter_code_sa.py INPUT(war.gz file)')
        sys.exit(0)
    count = 0
    with gzip.open(INPUT, 'rb') as stream:
        for record in ArchiveIterator(stream):
            if record.rec_type == 'response':
                    # the key_ID storing WebpageID, the text storing the text converted by html
                    key_ID = record.rec_headers.get_header(KEYNAME)
                    htmlcontent = record.content_stream().read()

                    # method 1 for html1 to text
                    soup = BeautifulSoup(htmlcontent, "lxml")
                    if soup == None:
                        continue

                    #test = parse_html(soup)
                    text = html_to_text(soup)
                    if text == "":
                        continue

                    

                    # The Token will return a list with ("string","type")
                    
                    NER_mentions = NLP1(text)
                    # drop duplicate in NER_mentions
                    NER_mentions = list(dict.fromkeys(NER_mentions))

                    
                    
                    
                    if count >= 0:
                        final_entities = []
                        for mention in NER_mentions:
                            # candidates is a dictionary with 10 results
                            candidates = generate_candidates(mention[0])
                            can_with_max_score = ""
                            max_score = 0
                            max_entity = []
                            if candidates == None:
                                continue
                            for entity_id, labels in candidates:

                                # convert labels into string type 
                                labels_str = ', '.join(labels)
                                
                                # if words of mention are "completely" in labels, add a bonus score 
                                contain_score = 0
                                if mention[0] in labels_str:
                                    contain_score = 0.1

                                # do the string similarity
                                temp_score = cos_sim(labels_str,mention[0]) + contain_score
                                if temp_score > max_score:
                                    max_score = temp_score
                                    max_entity = [mention[0],entity_id]
                            if len(max_entity) != 0:
                                final_entities.append(max_entity)

                        if len(final_entities) > 0:
                            for final_enity in final_entities:
                                print(key_ID + '\t' + final_enity[0] + '\t' + final_enity[1])

                        
                    count +=1
                    if count == 20:
                        break



