import csv
import math
import re
import sys


import numpy as np
np.seterr(divide='ignore', invalid='ignore')
from movielens import ratings
from random import randint


class Chatbot:
   

    def __init__(self, is_turbo=False):
      self.name = 'moviebot'
      self.is_turbo = is_turbo
      self.stemmedSentiment = {}
      self.p = PorterStemmer()
      self.movieDB = {}
      self.alphanum = re.compile('[^a-zA-Z0-9]')
      self.numOfGoodReplys = 0
      self.userRatings = [] #list of Ratings from the user. Elements are lists in the form: [movieTitle, rating, index in self.titles]
      self.numOfReviewsUntilReady = 5
      self.mostRecent = ''
      self.agreeScore = 0
      self.lastRating = 0
      self.angryWords = ['mad', 'angry', 'furious', 'agitated', 'distraught', 'exasperated', 'livid', 'resentful',
                         'enraged', 'rage', 'fuming', 'upset', 'infuriated', 'irritated']
      self.happyWords = ['happy', 'elated', 'delighted', 'glad', 'joyful', 'pleased', 'thrilled', 'ecstatic', 'merry'
                         'content']
      self.userIsAngryMsgs = ['Please don\'t be mad.\n', 'I\'m sorry if I made you angry.\n', 'Please calm down\n']
      self.userIsHappyMsgs = ['Well, you\'re happy today', 'I can tell that you\'re happy\n', 'I see that you are enjoying yourself\n']
      self.read_data()
      self.runCount = 0

   
    def greeting(self):
     
      greeting_msgs = ['Hello, I\'m ChatBot! I\'m going to recommend a movie to you.'
                  + ' First I will ask you about your taste in movies. Tell me about'
                  + ' a movie that you have seen.', 'Hey! My name\'s ChatBot. Tell'
                  + ' me about a few movies you like or dislike and I\'ll try to'
                  + ' recommend something new for you to watch.', 'Hi there! You\'ve'
                  + ' just fired up the ol\' ChatBot. Give me the names of some'
                  + ' movies you\'ve seen and tell me whether you liked them or not'
                  + ' and I\'ll search my databases for new titles you\'ll enjoy.']

      return greeting_msgs[randint(0, len(greeting_msgs) - 1)]

    def goodbye(self):
      
      goodbye_msgs = ['Have a great day!', 'So long for now!', 'Bye!', 'Have a nice day!']

      return goodbye_msgs[randint(0, len(goodbye_msgs) - 1)]

   
    def negatedWord(self, prevWord, wordTwoBack):
        if prevWord == 'not' or prevWord.endswith('nt') or prevWord == 'never':
            return True
        if wordTwoBack == 'not' or wordTwoBack.endswith('nt') or wordTwoBack == 'never':
            return True
        return False
    
    
    def likedMovie(self, sentence):
        posWordCount = 0
        negWordCount = 0
        words = sentence.split()
        prevWord = ""
        wordTwoBack = ""
        for word in words:
            word = word.lower() 
            word = word.strip()
            word = self.alphanum.sub('', word)
            if word != '':
               word = self.p.stem(word, 0, len(word)-1)
               rating = self.stemmedSentiment.get(word) 
               if rating == 'pos':
                  
                   if self.negatedWord(prevWord, wordTwoBack):
                       negWordCount += 1
                   else:
                       posWordCount += 1
               elif rating == 'neg':
                   if self.negatedWord(prevWord, wordTwoBack):
                       posWordCount += 1
                   else:
                       negWordCount += 1
            wordTwoBack = prevWord
            prevWord = word
        if (posWordCount == negWordCount):
            return 0
        elif (posWordCount > negWordCount):
            return 1
        else:
            return -1

    
    def timeForRec(self):
      if self.numOfGoodReplys != 0:
          if (self.numOfGoodReplys % self.numOfReviewsUntilReady) == 0:
              return True
          else:
              return False
      else:
          return False

    def checkForEmotion(self, input):
      inputList = input.split()
      prevWord = ''
      wordTwoBack = ''
      happyMsg = self.userIsHappyMsgs[randint(0, len(self.userIsHappyMsgs) - 1)]
      angryMsg = self.userIsAngryMsgs[randint(0, len(self.userIsAngryMsgs) - 1)]

      for word in inputList:
          word = self.alphanum.sub('', word)

          if word != '':
              word = self.p.stem(word, 0, len(word) - 1)
              if word in self.happyWords:
                  if self.negatedWord(prevWord, wordTwoBack):
                      return angryMsg
                  else:
                      return happyMsg
              if word in self.angryWords:
                  if self.negatedWord(prevWord, wordTwoBack):
                      return happyMsg
                  else:
                      return angryMsg
          wordTwoBack = prevWord
          prevWord = word
      return ''


    def process(self, input):
      if self.runCount == 0:
        self.runCount += 1
        if self.is_turbo:
          self.mean_subtract()
        else:
          self.binarize()
      


      movie = ''
      restOfSentence = ''
      oppositeOfLast = False
      sameAsLast = False
      inQuotePattern = '(.*?)\"(.*?)\"(.*)'  
      match = re.findall(inQuotePattern, input)
      reply = ''
      if len(match) == 0:  
        emotionProcessed = self.checkForEmotion(input)
        if emotionProcessed != '':
          reply += emotionProcessed
        referencePattern = '(.*?)(it|that movie|the movie|that)(.*)'
        refer = re.findall(referencePattern, input.lower())
        if len(refer) != 0:
          movie = self.mostRecent
          restOfSentence = refer[0][0] + refer[0][2]
        else:
          no_match_msgs = ["Umm, I want to hear more about movies! That's really the only thing I can help you with...",
                         "Ok. Let's stay on the topic of movies though.", "Now that we are done with that let's talk more about"
                         + " movies.", "Fine. Now can you tell me about a movie you like or dislike?",
                         "Cool. I need a movie title in quotation marks and how you felt about it now."]
          return reply + no_match_msgs[randint(0, len(no_match_msgs) - 1)]
      if len(match) > 1: 
        return "Please tell me about one movie at a time. Go ahead."
      if len(match) == 1:
        movie = match[0][1]
        restOfSentence = match[0][0] + match[0][2]
        reply += self.checkForEmotion(restOfSentence)
        if restOfSentence.lower().startswith("but not") or restOfSentence.lower().startswith("and not"):
          oppositeOfLast = True
        restOfSentenceList = restOfSentence.split()
        if len(restOfSentenceList) == 1 and restOfSentenceList[0].lower() == 'and':
          sameAsLast = True

        
      movie_index = self.search_for_title_str(str.lower(movie)) 
      if movie_index == -1:
            
          never_heard_messages = ["I've never heard of that movie. Please tell me about another movie.",
                                  "What movie is that? Never heard of it",
                                  "Please tell me about an actual movie haha"]
          return never_heard_messages[randint(0, len(never_heard_messages) - 1)]
      elif movie_index == -2:
          no_info_messages = ["I'm afraid I don't have any info about the movie you're looking for, then.",
                              "Welp, then I don't have any info about that movie,"
                              "I guess you're out of luck!"]
          return no_info_messages[randint(0, len(no_info_messages)-1)] + " Please tell me about another movie."
      movie = self.titles[movie_index][0]
      self.mostRecent = movie


        

      movieRating = self.likedMovie(restOfSentence)

        # checks to see if the user typed something that refered to the sentiment of the last input
      if oppositeOfLast:
        movieRating = self.lastRating * -1
      elif sameAsLast:
        movieRating = self.lastRating
      self.lastRating = movieRating

      reply = ""

       
      moviesSeenIndex = [k for k, userRating in enumerate(self.userRatings) if userRating[0] == movie]
      if len(moviesSeenIndex) != 0:
        if movieRating == self.userRatings[moviesSeenIndex[0]][1]:
            reply += "You didn't even change your opinion about %s! " % movie
        else:
            reply += "You changed your opinion about %s! " % movie
        self.userRatings.pop(moviesSeenIndex[0])
              

      botRating = self.movieDB[movie][1]

      if (movieRating == 1):
        if botRating == 1:
            reply += 'Hey! I really liked that movie too! ' # this is just an example statement
            self.agreeScore += 1
        if botRating == -1:
            reply += 'Hmm, not sure if I agree with your taste, but okay. ' # this is jusft an example statement
            self.agreeScore -= 1
        reply += "You liked " + movie + ". "
        if botRating == 0: reply += 'I haven\'t watched it, but will try it since you liked it. :) ' # this is just an example statement
        self.numOfGoodReplys += 1   #Counts the number of times the user inputs a valid review of a moivie
        self.userRatings.append([movie, 1, movie_index])
      elif (movieRating == -1):
        if botRating == 1:
            reply += 'Hmm, I think that one was alright, but okay. ' # this is jusft an example statement
            self.agreeScore -= 1
        reply += "You did not like " + movie + ". "
        if botRating == -1:
            reply += 'Totally agree. Hated that one too. ' # this is just an example statement
            self.agreeScore += 1
        if botRating == 0: reply += 'I haven\'t watched it, but will make sure to avoid it. ' # this is just an example statement
        self.numOfGoodReplys += 1
        self.userRatings.append([movie, -1, movie_index])
      else:
        return "I'm sorry, I'm not quite sure if you liked " + movie + ".\nTell me more clearly your opinion about " + movie + ""

      if (self.timeForRec()): # when it has enough info to make a recommendation
        reply += "That's enough for me to make a recommendation\n"
        recommendation = self.recommend([])
        if self.agreeScore > 2:
            reply += "Super excited to find that we have similar movie taste. I really liked " + recommendation
            reply += " personally, so you should check it out too! ;)"
        if self.agreeScore < -2:
            reply += "Seems like you appreciate bad movies, and dislike the good ones, so I recommend you watch "
            reply += recommendation + " since I know that one's terrible."
        else:
            reply += "I suggest you watch " + recommendation + "!"
        self.agreeScore = 0


      reply += "\nTell me about another movie you have seen"

      return reply

    def rearrange_articles(self, title_str):
       
        single_article_pattern = r'(.*), ([A-Z][a-z]{0,2}) (\([0-9]{4}\))'
        single_article_matches = re.findall(single_article_pattern, title_str)
        if len(single_article_matches) > 0:
            name = single_article_matches[0][0]
            article = single_article_matches[0][1]
            year = single_article_matches[0][2]
            title_str = article + " " + name + " " + year

        
        first_name_article_pattern = r'(.*), ([A-Z][a-z]{0,2}) (\(.*\) \([0-9]{4}\))'
        first_name_article_matches = re.findall(first_name_article_pattern, title_str)
        if len(first_name_article_matches) > 0:
            name = first_name_article_matches[0][0]
            article = first_name_article_matches[0][1]
            rest_of_str = first_name_article_matches[0][2]
            
            title_str = article + " " + name + " " + rest_of_str

            
            second_name_article_pattern = r'(.*\()(.*), ([A-Z][a-z\']{0,2})(\) \([0-9]{4}\))'
            second_name_article_matches = re.findall(second_name_article_pattern, title_str)
            if len(second_name_article_matches) > 0:
                first_name = second_name_article_matches[0][0]
                second_name = second_name_article_matches[0][1]
                second_article = second_name_article_matches[0][2]
                year = second_name_article_matches[0][3]
                
                if '\'' in second_article:
                    title_str = first_name + second_article + second_name + year
                else:
                    title_str = first_name + second_article + " " + second_name + year

        return title_str

    def search_for_title_str(self, search_str):
        matches = []
        min_edit_dist = float('inf')  

        for movie_index in xrange(0, len(self.titles)):
            movie = self.titles[movie_index]
            
            title = str.lower(self.rearrange_articles(movie[0]))
            if search_str == title:
                return movie_index
            else:
                if search_str in title:  
                    edit_dist = self.edit_distance(title, search_str)
                    if edit_dist < min_edit_dist:
                        matches = [movie_index] + matches
                        if len(matches) > 10:
                            matches = matches[0:10]
                        min_edit_dist = edit_dist
                    else:
                        if len(matches) < 10:
                            matches.append(movie_index)

        if len(matches) > 1:
            index = -1
            for i in xrange(0, len(matches)):
                print str(i) + ': ' + self.titles[matches[i]][0] + '\n'

            while index < 0 or index > len(matches):
                input_str = raw_input('Did you mean one of these movies? Please select the index of the movie you ' +\
                                      'meant or enter "none" if none of them are what you are looking for: ')
                if input_str == 'none':
                    return -2

                try:
                    index = int(input_str)
                    if index < 0 or index > len(matches):
                        print 'Please enter \'none\' or a valid number from the above indices.'
                except ValueError:
                    print 'Please enter \'none\' or a valid number from the above indices.'
                except NameError:
                    print 'Please enter \'none\' or a valid number from the above indices.'
                except SyntaxError:
                    print 'Please enter \'none\' or a valid number from the above indices.'

            return matches[index]

        elif len(matches) == 1:
            return matches[0]
        else:
            return -1

    def edit_distance(self, string_a, string_b):
        n = len(string_a)
        m = len(string_b)
        distance_tbl = [[-1 for i in xrange(n + 1)] for j in xrange(m + 1)]
        distance_tbl[0][0] = 0

        # init values for empty string_a/empty string_b
        for i in xrange(1, m + 1):
            distance_tbl[i][0] = distance_tbl[i - 1][0] + 1
        for j in xrange(1, n + 1):
            distance_tbl[0][j] = distance_tbl[0][j - 1] + 1

        for i in xrange(1, m + 1):
            for j in xrange(1, n + 1):
                sub_cost = 0 if string_a[j - 1] == string_b[i - 1] else 2
                distance_tbl[i][j] = min(distance_tbl[i - 1][j] + 1,
                                         distance_tbl[i - 1][j - 1] + sub_cost,
                                         distance_tbl[i][j - 1] + 1)

        return distance_tbl[m][n]

    #############################################################################
    # 3. Movie Recommendation helper functions                                  #
    #############################################################################

    def read_data(self):
      
      self.titles, self.ratings = ratings()
      reader = csv.reader(open('data/sentiment.txt', 'rb'))
      self.sentiment = dict(reader)
      #stem everything in the dictionary and put it in a new dictionary called stemmedSentiment
      for key in self.sentiment:
        newKey = key.lower()
        newKey = self.p.stem(newKey, 0, len(newKey)-1)
        self.stemmedSentiment[newKey] = self.sentiment[key]

      del self.stemmedSentiment['actual']
      for i, happyWord in enumerate(self.happyWords):
        happyWord = self.p.stem(happyWord, 0, len(happyWord)-1)
        self.happyWords[i] = happyWord

      for j, angryWord in enumerate(self.angryWords):
        angryWord = self.p.stem(angryWord, 0, len(angryWord)-1)
        self.angryWords[j] = angryWord
      for title in self.titles:
        genres = []
        for genre in title[1].split('|'):
            genres.append(genre)
        movie_data = [genres, randint(-1, 1)]
        self.movieDB[title[0]] = movie_data

    def mean_subtract(self):
      for rating in self.ratings:
        mean = np.mean(rating)
        for score in rating:
            if score != 0:
                score -= mean

    
    def binarize(self):
      
      self.ratings[np.where(self.ratings > 2.5)] = 10
      self.ratings[np.where(self.ratings == 0)] = 9
      self.ratings[np.where(self.ratings <= 2.5)] = -1
      self.ratings[np.where(self.ratings == 9)] = 0
      self.ratings[np.where(self.ratings == 10)] = 1



    def distance(self, u, v):
      
      dot = np.dot(v, u)
      u_length = np.linalg.norm(u)
      v_length = np.linalg.norm(v)
      distance = dot / (u_length * v_length)
      return distance

    def recommend(self, u):
      
      bestMovieTitle = ""
      max_score = -1
      for i in xrange(0, len(self.titles)):
          movieIndex = [k for k, x in enumerate(self.userRatings) if x[0] == self.titles[i][0]] 
          if len(movieIndex) == 0:
              score = 0.0
              total_cossim = 0.0
              for j in xrange(len(self.userRatings)): 
                  cossim = self.distance(self.ratings[self.userRatings[j][2]], self.ratings[i])
                  total_cossim += cossim
                  score += cossim * self.userRatings[j][1]
              if self.is_turbo:
                  score %= total_cossim
              if score > max_score:
                  max_score = score
                  bestMovieTitle = self.titles[i][0]
      return bestMovieTitle

    
    def debug(self, input):
      
      debug_info = 'debug info'
      return debug_info


    #############################################################################
    # 5. Write a description for your chatbot here!                             #
    #############################################################################
    def intro(self):
      return """
      Welcome to MovieBot 2000!
      """

  
    def bot_name(self):
      return self.name


if __name__ == '__main__':
    Chatbot()


#all PorterStemmer stuff
class PorterStemmer:

    def __init__(self):
        

        self.b = ""  
        self.k = 0
        self.k0 = 0
        self.j = 0   

    def cons(self, i):
        
        if self.b[i] == 'a' or self.b[i] == 'e' or self.b[i] == 'i' or self.b[i] == 'o' or self.b[i] == 'u':
            return 0
        if self.b[i] == 'y':
            if i == self.k0:
                return 1
            else:
                return (not self.cons(i - 1))
        return 1

    def m(self):
        
        n = 0
        i = self.k0
        while 1:
            if i > self.j:
                return n
            if not self.cons(i):
                break
            i = i + 1
        i = i + 1
        while 1:
            while 1:
                if i > self.j:
                    return n
                if self.cons(i):
                    break
                i = i + 1
            i = i + 1
            n = n + 1
            while 1:
                if i > self.j:
                    return n
                if not self.cons(i):
                    break
                i = i + 1
            i = i + 1

    def vowelinstem(self):
        """vowelinstem() is TRUE <=> k0,...j contains a vowel"""
        for i in range(self.k0, self.j + 1):
            if not self.cons(i):
                return 1
        return 0

    def doublec(self, j):
        
        if j < (self.k0 + 1):
            return 0
        if (self.b[j] != self.b[j-1]):
            return 0
        return self.cons(j)

    def cvc(self, i):
        
        if i < (self.k0 + 2) or not self.cons(i) or self.cons(i-1) or not self.cons(i-2):
            return 0
        ch = self.b[i]
        if ch == 'w' or ch == 'x' or ch == 'y':
            return 0
        return 1

    def ends(self, s):
        
        length = len(s)
        if s[length - 1] != self.b[self.k]: # tiny speed-up
            return 0
        if length > (self.k - self.k0 + 1):
            return 0
        if self.b[self.k-length+1:self.k+1] != s:
            return 0
        self.j = self.k - length
        return 1

    def setto(self, s):
        
        length = len(s)
        self.b = self.b[:self.j+1] + s + self.b[self.j+length+1:]
        self.k = self.j + length

    def r(self, s):
       
        if self.m() > 0:
            self.setto(s)

    def step1ab(self):
       
        if self.b[self.k] == 's':
            if self.ends("sses"):
                self.k = self.k - 2
            elif self.ends("ies"):
                self.setto("i")
            elif self.b[self.k - 1] != 's':
                self.k = self.k - 1
        if self.ends("eed"):
            if self.m() > 0:
                self.k = self.k - 1
        elif (self.ends("ed") or self.ends("ing")) and self.vowelinstem():
            self.k = self.j
            if self.ends("at"):   self.setto("ate")
            elif self.ends("bl"): self.setto("ble")
            elif self.ends("iz"): self.setto("ize")
            elif self.doublec(self.k):
                self.k = self.k - 1
                ch = self.b[self.k]
                if ch == 'l' or ch == 's' or ch == 'z':
                    self.k = self.k + 1
            elif (self.m() == 1 and self.cvc(self.k)):
                self.setto("e")

    def step1c(self):
        
        if (self.ends("y") and self.vowelinstem()):
            self.b = self.b[:self.k] + 'i' + self.b[self.k+1:]

    def step2(self):
        
        if self.b[self.k - 1] == 'a':
            if self.ends("ational"):   self.r("ate")
            elif self.ends("tional"):  self.r("tion")
        elif self.b[self.k - 1] == 'c':
            if self.ends("enci"):      self.r("ence")
            elif self.ends("anci"):    self.r("ance")
        elif self.b[self.k - 1] == 'e':
            if self.ends("izer"):      self.r("ize")
        elif self.b[self.k - 1] == 'l':
            if self.ends("bli"):       self.r("ble") 
            
            elif self.ends("alli"):    self.r("al")
            elif self.ends("entli"):   self.r("ent")
            elif self.ends("eli"):     self.r("e")
            elif self.ends("ousli"):   self.r("ous")
        elif self.b[self.k - 1] == 'o':
            if self.ends("ization"):   self.r("ize")
            elif self.ends("ation"):   self.r("ate")
            elif self.ends("ator"):    self.r("ate")
        elif self.b[self.k - 1] == 's':
            if self.ends("alism"):     self.r("al")
            elif self.ends("iveness"): self.r("ive")
            elif self.ends("fulness"): self.r("ful")
            elif self.ends("ousness"): self.r("ous")
        elif self.b[self.k - 1] == 't':
            if self.ends("aliti"):     self.r("al")
            elif self.ends("iviti"):   self.r("ive")
            elif self.ends("biliti"):  self.r("ble")
        elif self.b[self.k - 1] == 'g': # --DEPARTURE--
            if self.ends("logi"):      self.r("log")
       
    def step3(self):
        
        if self.b[self.k] == 'e':
            if self.ends("icate"):     self.r("ic")
            elif self.ends("ative"):   self.r("")
            elif self.ends("alize"):   self.r("al")
        elif self.b[self.k] == 'i':
            if self.ends("iciti"):     self.r("ic")
        elif self.b[self.k] == 'l':
            if self.ends("ical"):      self.r("ic")
            elif self.ends("ful"):     self.r("")
        elif self.b[self.k] == 's':
            if self.ends("ness"):      self.r("")

    def step4(self):
        
        if self.b[self.k - 1] == 'a':
            if self.ends("al"): pass
            else: return
        elif self.b[self.k - 1] == 'c':
            if self.ends("ance"): pass
            elif self.ends("ence"): pass
            else: return
        elif self.b[self.k - 1] == 'e':
            if self.ends("er"): pass
            else: return
        elif self.b[self.k - 1] == 'i':
            if self.ends("ic"): pass
            else: return
        elif self.b[self.k - 1] == 'l':
            if self.ends("able"): pass
            elif self.ends("ible"): pass
            else: return
        elif self.b[self.k - 1] == 'n':
            if self.ends("ant"): pass
            elif self.ends("ement"): pass
            elif self.ends("ment"): pass
            elif self.ends("ent"): pass
            else: return
        elif self.b[self.k - 1] == 'o':
            if self.ends("ion") and (self.b[self.j] == 's' or self.b[self.j] == 't'): pass
            elif self.ends("ou"): pass
            # takes care of -ous
            else: return
        elif self.b[self.k - 1] == 's':
            if self.ends("ism"): pass
            else: return
        elif self.b[self.k - 1] == 't':
            if self.ends("ate"): pass
            elif self.ends("iti"): pass
            else: return
        elif self.b[self.k - 1] == 'u':
            if self.ends("ous"): pass
            else: return
        elif self.b[self.k - 1] == 'v':
            if self.ends("ive"): pass
            else: return
        elif self.b[self.k - 1] == 'z':
            if self.ends("ize"): pass
            else: return
        else:
            return
        if self.m() > 1:
            self.k = self.j

    def step5(self):
        
        self.j = self.k
        if self.b[self.k] == 'e':
            a = self.m()
            if a > 1 or (a == 1 and not self.cvc(self.k-1)):
                self.k = self.k - 1
        if self.b[self.k] == 'l' and self.doublec(self.k) and self.m() > 1:
            self.k = self.k -1

    def stem(self, p, i, j):
      
        self.b = p
        self.k = j
        self.k0 = i
        if self.k <= self.k0 + 1:
            return self.b # --DEPARTURE--

       

        self.step1ab()
        self.step1c()
        self.step2()
        self.step3()
        self.step4()
        self.step5()
        return self.b[self.k0:self.k+1]


if __name__ == '__main__':
    p = PorterStemmer()
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            infile = open(f, 'r')
            while 1:
                output = ''
                word = ''
                line = infile.readline()
                if line == '':
                    break
                for c in line:
                    if c.isalpha():
                        word += c.lower()
                    else:
                        if word:
                            output += p.stem(word, 0,len(word)-1)
                            word = ''
                        output += c.lower()
                print output,
            infile.close()