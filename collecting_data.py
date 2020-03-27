import logging
import time
from datetime import datetime, timedelta
import tweepy
from tweepy import Stream
from tweepy.streaming import StreamListener
import json
from pathlib import Path

# How to use this scrite to download twitte data regarding specifid keywords:
# 1. You need to add a bunch of keywords that appears in twittes to the file "./keywords.txt",
#    So far, I already add some keywords about coronavirus, but not for all.

keyword_path = "./keywords.txt"

# 2. You need to register a twitter account and create an application, then get [[access_token]],
#    [[access_token_secret]], [[consumer_key]], [[consumer_secret]]
#    You can refer to https://docs.inboundnow.com/guide/create-twitter-application/ for more help.
access_token = ''
access_token_secret = ''
consumer_key = ''
consumer_secret = ''

# 3. You need to specify the start day that you want to retrive data and
#    also how many days data that you need. For example in the default value,
#    I will retreive all twittes starting from 2020-03-25 00:00:00 to 2020-03-26 00:00:00
#    Since the twitter community is very active to talk about covid-19, there would be a
#    lot of twittes per day. So I would suggest to download one day data when you call scripts.
startDate = datetime(2020, 3, 25)
nums_day = 1
# ************************************************************************


# 4. Max numbers of twittes you can download.
max_nums_tweets = 50000

# 5. The tweets will be download and save them into a jsonl file (folder: ./data/).  Since the total number of tweets
#    may be very large so I create mulitple jsonl files to save them.  Each jsonl file have number
#    of [[nums_per_file]] tweets.

nums_per_file = 1000

def date_range(start, end):
    current = start
    while (end - current).days >= 0:
        yield current
        current = current + datetime.timedelta(seconds=1)


# A define listener to monitor data
class TweetListener(StreamListener):
    def on_status(self, status):
        stopDate = startDate + timedelta(days=nums_day)
        for date in date_range(startDate, stopDate):
            status.created_at = date
            print("tweet " + str(status.created_at) + "\n")
            print(status.text + "\n")
            # You can dump your tweets into Json File, or load it to your database


def get_data_stream(auth, hashtags=u"#Syria"):
    stream = Stream(auth, TweetListener(), secure=True, )
    stream.filter(track=[hashtags])


def get_data_api(auth, hashtags=u"#Coronavirus"):
    count_item = 0
    count_file = 0
    # Create API object
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    stopDate = startDate + timedelta(days=nums_day)

    root_path = "./data/" + str(startDate.date()) + "/"
    Path(root_path).mkdir(parents=True, exist_ok=True)
    output_path = root_path + str(count_file) + ".jsonl"
    output = open(output_path, 'wb')


    try:
        for tweet in tweepy.Cursor(api.search, q=keyword, since=startDate, until=stopDate,
                                   count=10, result_type='recent', include_entities=True, monitor_rate_limit=True,
                                   wait_on_rate_limit=True, lang="en").items(max_nums_tweets):
            try:
                if count_item % nums_per_file == 0 and count_file != 0:
                    output_path = root_path + str(count_file) + ".jsonl"
                    output = open(output_path, 'wb')

                output.write(json.dumps(tweet._json).encode('utf8') + b"\n")

                if count_item % nums_per_file == nums_per_file - 1:
                    logging.info("[Done]The file %s contain %d twittes ...", output_path, nums_per_file)
                    output.close()
                    count_file += 1

                count_item += 1

                if count_item % 1000 == 0:
                    time.sleep(20 * 60)
                    continue
            except tweepy.TweepError:
                time.sleep(60 * 10)
                continue
            except IOError:
                time.sleep(60 * 2)
                continue
            except StopIteration:
                break
    finally:
        output.close()
        logging.info("[Done]The file %s contain %d twittes ...", output_path, count_item % nums_per_file)
        logging.info("The total nums of tweets: %d", count_item)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Set up Twitter application authifications.
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    with open(keyword_path, 'r') as f:
        mylist = f.read().splitlines()
    keyword = " OR ".join(list(map(lambda x: '"' + x + '"', mylist)))
    logging.info("The Query Key words: %s", keyword)

    get_data_api(auth=auth, hashtags=keyword)
