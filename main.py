CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

import csv
import os
import pickle

import google.oauth2.credentials

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import numpy as np
from sklearn.model_selection import train_test_split
import pandas as pd
from konlpy.tag import Okt

def get_noun(text):
    tokenizer = Okt()
    nouns = tokenizer.nouns(text)
    return [n for n in nouns]

filename = 'model.sav'
loaded_model = pickle.load(open(filename, 'rb'))

def predict(texts):
    return (loaded_model.predict(texts))

def write_to_csv(comments,name):
    with open(name, 'a') as comments_file:
        for row in comments:
            comments_file.write(row+"\n")

# def get_authenticated_service():
#     flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
#     credentials = flow.run_console()
#     return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def get_authenticated_service():
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    #  Check if the credentials are invalid or do not exist
    if not credentials or not credentials.valid:
        # Check if the credentials have expired
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_console()

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def get_videos(service, **kwargs):
    final_results = []
    results = service.search().list(**kwargs).execute()

    i = 0
    max_pages = 5
    while results and i < max_pages:
        final_results.extend(results['items'])

        # Check if another page exists
        if 'nextPageToken' in results:
            kwargs['pageToken'] = results['nextPageToken']
            results = service.search().list(**kwargs).execute()
            i += 1
        else:
            break

    return final_results

def get_video_comments(service, **kwargs):
    comments = []
    results = service.commentThreads().list(**kwargs).execute()

    while results:
        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        if len(comments) > 300:
            break

        # Check if another page exists
        if 'nextPageToken' in results:
            kwargs['pageToken'] = results['nextPageToken']
            results = service.commentThreads().list(**kwargs).execute()
        else:
            break

        

    return comments


def search_videos_by_keyword(service, **kwargs):
    results = get_videos(service, **kwargs)
    for item in results:
        print('%s - %s' % (item['snippet']['title'], item['id']['videoId']))


# import numpy as np
# from sklearn.model_selection import train_test_split
if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()
    which = input('Search: 0\nComments: 1:\nAnalyze: 2: ')

    if which == '0':
        keyword = input('Type your search query: ')
        search_videos_by_keyword(service, q=keyword, part='id,snippet', eventType='completed', type='video')
    elif which == '1':
        keyword = input('Type ID of video: ')
        name = input('name of csv: ')
        comments = get_video_comments(service, part='snippet', videoId=keyword, textFormat='plainText')
        write_to_csv(comments,name)
    elif which == '2':
        keyword = input('Type ID of video: ')
        comments = get_video_comments(service, part='snippet', videoId=keyword, textFormat='plainText')
        predicted = list(predict(comments))
        print({"good": predicted.count(1), "bad": predicted.count(2)})
    elif  which == '3':
        keyword = input('Type ID of video: ')
        comments = get_video_comments(service, part='snippet', videoId=keyword, textFormat='plainText')
        print(len(list(comments)))

        
   

