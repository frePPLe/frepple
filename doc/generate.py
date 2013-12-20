#!/usr/bin/python
#
# Copyright (C) 2010-2013 by Johan De Taeye, frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import print_function
import os, os.path, sys, re
try:
  from HTMLParser import HTMLParser
except:
  from html.parser import HTMLParser

# List of stopwords, loosely based on:
#    http://en.wikipedia.org/wiki/Stop_words
#    http://armandbrahaj.blog.al/2009/04/14/list-of-english-stop-words/
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

pattern = re.compile('[\.-;/=,():\*"\'\?]+')

# Define a parser which takes care of:
#   - finds all keywords in a file
#   - echo the input as output, with certain parts of the document replaced
class WebSiteParser(HTMLParser):

  def clear(self):
    if getattr(self,'intitle',False) or getattr(self,'inreplace',False) or getattr(self,'intext',False):
      print("Warning: page '%s' not parsed as expected" % self.title)
    self.fed = []
    self.title = ''
    self.intitle = False
    self.intext = 0
    self.inreplace = False
    self.depth = 0

  def handle_starttag(self, tag, attrs):
    if tag == 'title':
      self.intitle = True
    if tag == 'div':
      if not self.intext and ('id','main-content') in attrs:
        self.intext = 1
      elif self.intext:
        self.intext += 1
    if tag == 'ul' and ('id','social-list') in attrs:
      self.inreplace = True
    elif tag == 'section' and ('id','comments') in attrs:
      self.inreplace = True
    elif tag == 'li' and ('id','recent-comments-5') in attrs:
      self.inreplace = True
    elif tag == 'script' and ('id','javascript_footer') in attrs:
      self.inreplace = True
    elif tag == 'footer':
      self.file_out.write('''<footer class="rtf">
	<div id="footer-content" class="clearfix container">
		<div id="copyright">Copyright &#xa9; 2010-2013 frePPLe bvba</div>
	</div>''')
      self.inreplace = True
    elif tag == 'form' and ('action','http://frepple.com') in attrs:
      self.file_out.write('''<form id="search-form" action="%ssearch.html">
	<input type="text" id="search-text" class="input-text waterfall" name="search" placeholder="Search &#8230;" default="" value="" size="30">
	<button type="submit" id="search-button"><span>Search</span></button>
  </form>''' % self.root)
      self.inreplace = True
    elif tag == 'a' and ('id','site-title-text') in attrs:
      self.file_out.write('''<a href="http://frepple.com/" title="frePPLe" rel="home" id="site-title-text">
          <img src="%swp-content/uploads/frepple.svg" onerror="this.src='%swp-content/uploads/frepple.png';" height="65px" alt="frePPLe">Open source Production Planning v%s</a>''' % (self.root, self.root, os.getenv('PACKAGE_VERSION', "NA")))
      self.inreplace = True
    elif tag == 'nav' and ('id','primary-menu-container') in attrs:
      self.file_out.write('''<nav id="primary-menu-container">
		<ul id="primary-menu">
	  <li class="menu-item menu-item-type-post_type menu-item-object-page"><a href="http://frepple.com/">Home</a></li>
    <li class="menu-item menu-item-type-post_type menu-item-object-page page_item"><a href="%sdocumentation/index.html">Documentation</a></li>
    <li class="menu-item menu-item-type-post_type menu-item-object-page current-menu-item page_item current_page_item"><a href="%sapi/index.html">C++ API</a>
    </ul></nav>''' % (self.root, self.root))
      self.inreplace = True
    if self.inreplace:
      self.depth += 1
    else:
      self.file_out.write(self.get_starttag_text())


  def handle_startendtag(self, tag, attrs):
    if tag == 'link' and ('rel','profile') in attrs:
      return
    if tag == 'link' and ('rel','alternate') in attrs:
      return
    if tag == 'link' and ('rel','pingback') in attrs:
      return
    if tag == 'link' and ('rel','next') in attrs:
      return
    if tag == 'link' and ('rel','prev') in attrs:
      return
    if tag == 'link' and ('rel','canonical') in attrs:
      return
    if tag == 'link' and ('rel','EditURI') in attrs:
      return
    if not self.inreplace: self.file_out.write(self.get_starttag_text())

  def handle_endtag(self, tag):
    if tag == 'title':
      self.intitle = False
    if self.intext > 0 and tag == 'div':
      self.intext -= 1
    if not self.inreplace:
      self.file_out.write("</%s>" % tag)
    else:
      self.depth -= 1
      if self.depth == 0:
        self.inreplace = False

  def handle_data(self, d):
    if self.inreplace: return
    if self.intitle: self.title += d
    if self.intext > 0:
      self.fed.append(d)
    self.file_out.write(d)

  def handle_entityref(self, name):
    if not self.inreplace: self.file_out.write("&%s;" % name)

  def handle_charref(self, name):
    if not self.inreplace: self.file_out.write("&#%s;" % name)

  def handle_decl(self, decl):
    self.file_out.write("<!%s>" % decl)

  def get_keywords(self):
   try:
    for x in ' '.join(self.fed).split():
      k = pattern.sub("",x).lower()
      if len(k) > 1 and not k in stoplist and k.isalnum() and not k[0].isdigit():
        yield k
   except Exception as e:
    print(e)

  def parseFiles(self, infolder):
    global filecounter, outfile, keys
    for root, dirs, files in os.walk(infolder):
      for f in files:
        if not f.endswith('.html'): continue
        if f.endswith('.html.html'): continue
        infile = os.path.join(root,f)
        filecounter += 1
        self.root = '../' * (infile.count(os.sep) - 1)
        file_in = open(infile)
        self.file_out = open("%s.tmp" % infile, 'wt')
        try:
          parser.clear()
          while True:
            data = file_in.read(8192)
            if not data: break
            parser.feed(data)
          print("{name: '%s', title: '%s'}," % (infile[7:], parser.get_title().strip()), file=outfile)
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
        finally:
          file_in.close()
          self.file_out.close()
          try:
            os.unlink(infile)
            os.rename("%s.tmp" % infile, infile)
          except:
            pass

  def get_title(self):
    return self.title

# Open the output index file
outfile = open(os.path.join("output","index.js"),"wt")
print ("var docs = [", file=outfile)

# Loop through all HTML files under the documentation subdirectory
parser = WebSiteParser()
keys = {}
filecounter = -1
parser.parseFiles(os.path.join('output','documentation'))

# Generate index file
print("];", file=outfile)
sk = sorted(list(keys.items()))
print("var index = {", file=outfile)
first = True
for k, v in sk:
  outfile.write("%s'%s': {count:%d, filecount:%d, refs:%s}" % (first and '  ' or ',\n  ', k, v['count'], v['filecount'], v['refs']))
  first = False
print("\n};", file=outfile)

# Print some interesting statistics
print("Statistics:")
print("\n%d keywords found in %d files" % (len(keys), filecounter))
print("\nTop 10 of most common words:")
sk = sorted(list(keys.items()), key=lambda k:(-k[1]['count'],k[0]))
for k, v in sk[0:10]:
  print("   '%s' used %d times in %d files" % (k, v['count'], v['filecount']))
print("\nTop 10 of words appearing in most files:")
sk = sorted(list(keys.items()), key=lambda k:(-k[1]['filecount'],k[0]))
for k, v in sk[0:10]:
  print("   '%s' used %d times in %d files" % (k, v['count'], v['filecount']))
