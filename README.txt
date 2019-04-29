At init stage, chatbot assigns random integer rating between -1 and 1 inclusive for each movie, where -1 is dislike, 0 is 'haven't watched', and 1 is like.
When the user indicates their thoughts on each movie during discussion, response of chatbot changes depending on whether bot's rating of movie is equal to or different from the user.
This accumulates over the conversation. 
If user and chatbot agree on 3 or more movies out of 5, then movie bot responds very kindly;
if user and moviebot disagree on 3 or more movies out of 5, then movie bot responds rudely; 
else, moviebot just responds neutrally. This is to give a sense of talking to an actual person with their own thoughts on movies. 
The chatbot understands things referring to statements made previously. 
All three features on the rubric should pass for this.
Also, the user can change the review of any past review and can change the last one by referring to it. 
The chatbot understands movie titles that are not correctly capitalized.
The chatbot disambiguates movie titles.
It suggests a list of matching titles and asks the user to specify which one they meant. 
The first title in the list has the shortest edit distance from the search string the user provides. 
The chatbot identifies angry and happy emotions made by the user and responds accordingly by responding to the emotion. 
This can be within a review of a movie or standalone.