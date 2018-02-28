import json, os, time, datetime, re
import requests
from urllib.parse import unquote_plus, quote_plus
from urllib.request import urlretrieve
from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import ExpiresAfter
from requests_toolbelt.utils import dump
from config import SBConfig

from cbserver.models import Arc, Character, Creator, Team, Publisher, Series, Issue, Settings
#from .comicfilehandler import ComicFileHandler
#from . import fnameparser, util

from bs4 import BeautifulSoup, UnicodeDammit

from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app import app
import logging

logging.basicConfig(level=logging.DEBUG)

#sess = CacheControl(requests.Session(), cache=FileCache('./comicvine-cache'), heuristic=ExpiresAfter(days=1))
forever_cache = FileCache('./var/comicvine-cache', forever=True)
sess = CacheControl(requests.Session(), forever_cache, heuristic=ExpiresAfter(days=1))

class CVWrapper(object):
    def __init__(self, **kwargs):
        self.model=''
        # API Strings
        self.baseurl = 'https://comicvine.gamespot.com/api/'
        self.imageurl = 'https://comicvine.gamespot.com/api/image/'
        #self.baseurl = 'http://10.68.230.2:95/api'
        #self.imageurl = 'http://10.68.230.2:95/api/image/'
        self.api_key=SBConfig.get_api_key()
        self.base_params = { 'format': 'json', 'api_key': self.api_key }
        self.headers = { 'user-agent': 'somethingbetter' }
        # API field strings
        self.arc_fields = 'deck,description,id,image,name,site_detail_url'
        self.character_fields = 'deck,description,id,image,name,site_detail_url'
        self.creator_fields = 'deck,description,id,image,name,site_detail_url'
        self.issue_fields = 'api_detail_url,character_credits,cover_date,deck,description,id,image,issue_number,name,person_credits,site_detail_url,story_arc_credits,team_credits,volume'
        self.publisher_fields = 'deck,description,id,image,name,site_detail_url'
        self.query_issue_fields ='cover_date,id,issue_number,name,volume'
        self.query_issue_limit = '100'
        self.query_series_fields = 'id,name,start_year,api_detail_url,description'
        self.query_series_limit = '10'
        self.series_fields = 'api_detail_url,deck,description,id,name,publisher,site_detail_url,start_year'
        self.team_fields = 'characters,deck,description,id,image,name,site_detail_url'
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_issue_cvid_by_number(self):
        query_params = self.base_params
        query_params['resources'] = 'volume'
        query_params['field_list'] = 'issues'
        query_response = self._query_cv((self.baseurl + 'volume/4050-' + str(self.model.series.cvid)), query_params)
        if self.model.series.cvid:
            cvresult = next((series_issue['id'] for series_issue in query_response['results']['issues'] if int(series_issue['issue_number']) == self.model.number), None)
        else:
            cvresult="Must define Series ID first."
        return cvresult

    def import_issue_details(self, comic):
        query_params = self.base_params
        query_params['field_list'] = 'image,description' #self.query_series_fields
        query_response = self._query_cv((self.baseurl + 'issue/4000-' + str(comic.cvid)), query_params)
        #comic.cover=query_response['results']['image']['thumb_url']
        #comic.desc=query_response['results']['description']
        #db.session.commit()
        #return issue

    def import_issue_covers(self, comic):
        #comic = db.session.query(Issue).filter_by(id=id).first()
        if comic:
            query_params = self.base_params
            query_params['field_list'] = 'image' #self.query_series_fields
            query_response = self._query_cv((self.baseurl + 'issue/4000-' + str(comic.cvid)), query_params)
            #comic.cover=query_response['results']['image']['thumb_url']
            #comic.cover=query_response['results']['image']['thumb_url']
            #db.session.commit()
        #return issue

    def find_issue_id(self, comic):
            query_params = self.base_params
            query_params['field_list'] = 'issues' #,name,start_year,api_detail_url,description' #self.query_series_fields
            query_response = self._query_cv((self.baseurl + 'volume/4050-' + comic.series.cvid), query_params)
            for result in query_response['results']['issues']:
                if str(result['issue_number']) == str(comic.number):
                    comic.cvid=result['id']
                    comic.cvurl=result['site_detail_url']
                    comic.name=result['name']
                    response=comic
            #db.session.commit()
            return response

    def find_series_matches(self):
        query_params = self.base_params
        query_params['resources'] = 'volume'
        #query_params['field_list'] = 'id,name,start_year,api_detail_url,description' #self.query_series_fields
        query_params['filter'] = 'name:' + self.name
        response = self._query_cv((self.baseurl + 'volumes'), query_params)
        self.query_response = response['results']
        self.get_descriptions()
        return self.query_response

    def get_series_details(self):
        query_params = self.base_params
        query_params['resources'] = 'volume'
        query_params['field_list'] = 'deck,description,image,name,publisher,api_detail_url'
        response = self._query_cv((self.baseurl + 'volume/4050-' + self.cvid), query_params)
        self.query_response = response['results']
        print(self.query_response)
        self.get_description(self.query_response)
        #print(query_response)
        #description = query_response['results']['description']
        #print(description)
        #if description is not None:
        #    query_response['results']['description'] = self.get_p(query_response['results']['description'])
        return self.query_response

    def get_issue_details(self):
        query_params = self.base_params
        query_params['resources'] = ''
        query_params['field_list'] = 'cover_date,description,image,name,aliases'
        response = self._query_cv((self.baseurl + 'issue/4000-' + str(self.cvid)), query_params)
        self.query_response = response['results']
        self.get_description(self.query_response)
        #self.query = query_response['results']['description']
        #if description:
        #    query_response['results']['description'] = self.get_p(query_response['results']['description'])
        return self.query_response

    def get_description(self, record): #Used to get a single result's descriptions.
        text = record['description']
        if text is not None:
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.find('p')
        if text is not None:
            text = text.get_text()
            record['description'] = UnicodeDammit(soup.find('p').text, ["windows-1252"], smart_quotes_to="html").unicode_markup #10,000 deaths to anyone who uses smart quotes.
        return record

    def get_descriptions(self): #Used to get a list of result's descriptions.
        results = [self.get_description(record) for record in self.query_response]
        self.query_response = results

    @classmethod
    def get_p(self):
        #print(query)
        try:
            text = self.query_response['results']['description']
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.find('p').text
            self.query_response['results']['description'] = UnicodeDammit(soup.find('p').text, ["windows-1252"], smart_quotes_to="html").unicode_markup #10,000 deaths to anyone who uses smart quotes.
            return self.query_response['results']['description']
        except:
            return None

    def _query_cv(self, query_url, query_params):
        response = sess.get(
            query_url + '/',
            params=query_params,
            headers=self.headers,
        )

        return json.loads(response.text)
