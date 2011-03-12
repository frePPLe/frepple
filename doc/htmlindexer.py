#!/usr/bin/python
#
# Copyright (C) 2010 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

import HTMLParser, os, os.path, sys

stoplist = frozenset(["able", "about", "above", "frepple", "according", "accordingly", 
  "across", "actually", "after", "afterwards", "again", "against", "ain't", "all", "allow", 
  "allows", "almost", "alone", "along", "already", "also", "although", "always", "am", 
  "among", "amongst", "an", "and", "another", "any", "anybody", "anyhow", "anyone", 
  "anything", "anyway", "anyways", "anywhere", "apart", "appear", "appreciate", 
  "appropriate", "are", "aren't", "around", "as", "aside", "ask", "asking", "associated", 
  "at", "available", "away", "awfully", "be", "became", "because", "become", "becomes", 
  "becoming", "been", "before", "beforehand", "behind", "being", "believe", "below", 
  "beside", "besides", "best", "better", "between", "beyond", "both", "brief", "but", 
  "by", "c'mon", "c's", "came", "can", "can't", "cannot", "cant", "cause", "causes", 
  "certain", "certainly", "changes", "clearly", "co", "com", "come", "comes", "concerning", 
  "consequently", "consider", "considering", "contain", "containing", "contains", 
  "corresponding", "could", "couldn't", "course", "currently", "definitely", "described", 
  "despite", "did", "didn't", "different", "do", "does", "doesn't", "doing", "don't", 
  "done", "down", "downwards", "during", "each", "edu", "eg", "eight", "either", "else", 
  "elsewhere", "enough", "entirely", "especially", "et", "etc", "even", "ever", "every", 
  "everybody", "everyone", "everything", "everywhere", "ex", "exactly", "example", 
  "except", "exist", "exists", "far", "few", "fifth", "first", "five", "followed", "following", "follows", 
  "for", "former", "formerly", "forth", "four", "from", "further", "furthermore", 
  "get", "gets", "getting", "given", "gives", "go", "goes", "going", "gone", "got", 
  "gotten", "greetings", "had", "hadn't", "happens", "hardly", "has", "hasn't", "have", 
  "haven't", "having", "he", "he's", "hello", "help", "hence", "her", "here", "here's", 
  "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "hi", "him", "himself", 
  "his", "hither", "hopefully", "how", "howbeit", "however", "i'd", "i'll", "i'm", "i've", 
  "ie", "if", "ignored", "immediate", "in", "inasmuch", "inc", "indeed", "indicate", 
  "indicated", "indicates", "inner", "insofar", "instead", "into", "inward", "is", "isn't", 
  "it", "it'd", "it'll", "it's", "its", "itself", "just", "keep", "keeps", "kept", "know", 
  "knows", "known", "last", "lately", "later", "latter", "latterly", "least", "less", 
  "lest", "let", "let's", "like", "liked", "likely", "little", "look", "looking", "looks", 
  "ltd", "main", "mainly", "manual", "many", "may", "maybe", "me", "mean", "meanwhile", "merely", "might", 
  "more", "moreover", "most", "mostly", "much", "must", "my", "myself", "name", "namely", 
  "nd", "near", "nearly", "necessary", "need", "needs", "neither", "never", "nevertheless", 
  "new", "next", "nine", "no", "nobody", "non", "none", "noone", "nor", "normally", "not", 
  "nothing", "novel", "now", "nowhere", "obviously", "of", "off", "often", "oh", "ok", 
  "okay", "old", "on", "once", "one", "ones", "only", "onto", "or", "other", "others", 
  "otherwise", "ought", "our", "ours", "ourselves", "out", "outside", "over", "overall", 
  "own", "particular", "particularly", "per", "perhaps", "placed", "please", "plus", 
  "possible", "presumably", "probably", "provides", "que", "quite", "qv", "rather", 
  "rd", "re", "really", "reasonably", "reference", "regarding", "regardless", "regards", "relatively", 
  "respectively", "right", "said", "same", "saw", "say", "saying", "says", "second", 
  "secondly", "see", "seeing", "seem", "seemed", "seeming", "seems", "seen", "self", 
  "selves", "sensible", "sent", "serious", "seriously", "seven", "several", "shall", 
  "she", "should", "shouldn't", "since", "six", "so", "some", "somebody", "somehow", 
  "someone", "something", "sometime", "sometimes", "somewhat", "somewhere", "soon", 
  "sorry", "specified", "specify", "specifying", "still", "sub", "such", "sup", "sure", 
  "take", "taken", "tell", "tends", "th", "than", "thank", "thanks", "thanx", "that", 
  "that's", "thats", "the", "their", "theirs", "them", "themselves", "then", "thence", 
  "there", "there's", "thereafter", "thereby", "therefore", "therein", "theres", 
  "thereupon", "these", "they", "they'd", "they'll", "they're", "they've", "think", 
  "third", "this", "thorough", "thoroughly", "those", "though", "three", "through", 
  "throughout", "thru", "thus", "to", "together", "too", "took", "toward", "towards", 
  "tried", "tries", "truly", "try", "trying", "twice", "two", "un", "under", "unfortunately", 
  "unless", "unlikely", "until", "unto", "up", "upon", "us", "use", "used", "useful", 
  "uses", "using", "usually", "value", "various", "very", "via", "viz", "vs", "want", 
  "wants", "was", "wasn't", "way", "we", "we'd", "we'll", "we're", "we've", "welcome", 
  "well", "went", "were", "weren't", "what", "what's", "whatever", "when", "whence", 
  "whenever", "where", "where's", "whereafter", "whereas", "whereby", "wherein", 
  "whereupon", "wherever", "whether", "which", "while", "whither", "who", "who's", "whoever", 
  "whole", "whom", "whose", "why", "will", "willing", "wish", "with", "within", "without", 
  "won't", "wonder", "would", "would", "wouldn't", "yes", "yet", "you", "you'd", "you'll", 
  "you're", "you've", "your", "yours", "yourself", "yourselves", "zero"
  ])
  
# Define a parser which finds all keywords in a file
class FindKeywords(HTMLParser.HTMLParser): 
  def clear(self):
    self.fed = []
    self.title = ''
    self.intext = False
    self.intitle = False
  def handle_starttag(self, tag, attrs):
    if tag == 'title':
      self.intitle = True
    if not self.intext and tag == 'div' and ('id','wikitext') in attrs:
      self.intext = True
  def handle_endtag(self, tag):
    if tag == 'title':
      self.intitle = False
  def handle_data(self, d): 
    if self.intitle:
      self.title += d
    if self.intext:
      self.fed.append(d) 
  def get_keywords(self): 
    for x in ' '.join(self.fed).split():
      k = x.strip(".-;/=,():\"'?").lower()
      if len(k) > 1 and not k in stoplist and k.isalnum() and not k[0].isdigit(): 
        yield k 
  def get_title(self): 
    return self.title

# Open the output index file
outfile = open("index.js","wt")
print >>outfile, "var docs = ["

# Loop through all HTML files under this subdirectory
parser = FindKeywords() 
keys = {}
filecounter = 0
for d in sys.argv[1:]:
  for root, dirs, files in os.walk(d):
    for f in files:
      if f.endswith('.html'):
        # Parse the current file
        fd = open(os.path.join(root,f))
        try:        
          parser.clear()
          while True:
            data = fd.read(8192)
            if not data: break
            parser.feed(data)
        finally:
          fd.close()
        print >>outfile, "{name: '%s', title: '%s'}," % (os.path.join(root,f), parser.get_title().strip())
        for i in parser.get_keywords():
          if not i in keys.keys():
            keys[i] = {'count': 1, 'filecount': 1, 'refs':{filecounter:1}}
          else:
            keys[i]['count'] += 1
            if filecounter in keys[i]['refs'].keys():
              keys[i]['refs'][filecounter] += 1
            else:
              keys[i]['refs'][filecounter] = 1
              keys[i]['filecount'] += 1
        filecounter += 1

# Generate index file
print >>outfile, "];"
sk = sorted(keys.items())
print >>outfile, "var index = {"
first = True
for k, v in sk:
  outfile.write("%s'%s': {count:%d, filecount:%d, refs:%s}" % (first and '  ' or ',\n  ', k, v['count'], v['filecount'], v['refs']))
  first = False
print >>outfile, "\n};"

# Print some interesting statistics
print "Statistics:"     
print "\n%d keywords found in %d files" % (len(keys), filecounter)
print "\nTop 10 of most common words:"
sk = sorted(keys.items(), key=lambda(k,v):(-v['count'],k))
for k, v in sk[0:10]:
  print "   '%s' used %d times in %d files" % (k, v['count'], v['filecount'])
print "\nTop 10 of words appearing in most files:"
sk = sorted(keys.items(), key=lambda(k,v):(-v['filecount'],k))
for k, v in sk[0:10]:
  print "   '%s' used %d times in %d files" % (k, v['count'], v['filecount'])
