#! /usr/bin/env python
'''
Main file to start tornado server
'''
import tornado.ioloop
import tornado.web
import urllib
import tweepy
import os


from maxentclassifier import MaximumEntropyClassifier
from naivebayesclassifier import NaiveBayesClassifier

# name of training set file
fname = 'trainingandtestdata/training.csv'

# train classifiers here first
nb = NaiveBayesClassifier(fname, grams=[1,2])
nb.setThresholds(neg=1.0, pos=20.0)
nb.setWeight(0.000000000005)
nb.trainClassifier()
ment = MaximumEntropyClassifier(fname)
ment.trainClassifier()
classifiers = [nb, ment]


class MainHandler(tornado.web.RequestHandler):
    '''
    Handles request to main page
    '''
    def get(self):
        query = self.get_argument("query", "").strip()
        cchosen = int(self.get_argument("classifier-type", 0))

        auth = tweepy.OAuthHandler ("Yd1EFIv3psmpXdhR3lPVjUXva","WcmeKDjoaD3suYMQbgIyXTTtKcaDvws4h5cFwmlBy7jgDMxO9E")
        auth.set_access_token ("797867203-pm0v4oRKAe6EThRKeAq2H8tPruUUHepzhrTuXdbB", "0HpeNMR6P00UFqMwHvadZxvhXGzIonDxW1LdMHSH5AOQR")
        api = tweepy.API(auth)

        # search twitter
        results =api.search(q=urllib.quote(query)) if len(query) > 0 else []

        tweets = []
        poscount = 0
        negcount = 0
        for result in results:
            cresult = classifiers[cchosen].classify(result.text)

            if cresult == 0: negcount += 1
            elif cresult == 1: poscount += 1
            else: cresult = 2

            tweets.append((cresult, result))

        pospercent = 0 if len(results) == 0 else "%.2f" \
                     % (float(poscount)*100/(poscount + negcount))
        negpercent = 0 if len(results) == 0 else "%.2f" \
                     % (float(negcount)*100/(poscount + negcount))

        self.set_header("Cache-Control","no-cache")

        # render results of sentiment analysis on tweets in real-time
        self.render("index.html",
                    poscount = poscount,
                    negcount = negcount,
                    pospercent = pospercent,
                    negpercent = negpercent,
                    query = query, 
                    tweets = tweets)


if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    settings = {
        "static_path" : os.path.join(dirname, "static"),
        "template_path" : os.path.join(dirname, "template")
    }
    application = tornado.web.Application([
        (r'/', MainHandler)
    ], **settings)

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    
