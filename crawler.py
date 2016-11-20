#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import math
import time
import requests
from datetime import datetime
import simplejson as json
from tweepy import OAuthHandler
from tweepy import StreamListener
from tweepy import Stream
import tweepy				#Versao tweepy==3.6.0 e 3.5.0 apresentaram problemas -> use versao tweepy==3.2.0
from pymongo import MongoClient
from classification import Classification

consumerKey = 'qa6PVsPZOJQ4aeJMsXgcCQTLf'
consumerSecret ='TXzettXE1zAnxQKJuMIDk3e6vodgmSPkr52Es33UPgEZ09WTX3'
accessToken = '127248314-tcg8w96hKYXfB9iZHVexN3SUKr9O8KdW77SB2DhA'
accessSecret = 'z5CmBDAxmbsOOnQJY4NeMMos4yw4NnT4mERlzmqXZ1SvR'
#api.user_timeline(id="oficialbhtrans")
#api.user_timeline(id="524349796")
#db.reports.find({}).sort({"timestamp_ms": -1})

#------------------------------------------------------
# Class: 
# REFERENCES: 
# http://www.benkhalifa.com/twitter-crawler-python
# https://marcobonzanini.com/2015/03/02/mining-twitter-data-with-python-part-1/	
# @params:
# @author: Monica
#------------------------------------------------------
class MyListener(StreamListener):
	classification = None
	url = "http://pociidata-ufsjsocial.rhcloud.com/insert"	
	urlGet = "http://pociidata-ufsjsocial.rhcloud.com/find/"	
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
		
	def __init__(self, classification):
		self.classification = classification
	
	def on_data(self, data):
		try:
			data2 = json.loads(data)				
								
			# Verifica se o item já está no banco
			#cursor = db.informesTest.find({"id_str": data2["id_str"]})	
			#print ("\nTentativa.. "+str(cursor.count()))			
			#if(cursor.count() > 0): return True
			response = requests.get(self.urlGet+data2["id_str"])	
			json_data = json.loads(response.text)
			#print ("\nTentativa.. "+str(len(json_data["data"])))
			if (len(json_data["data"]) > 0): return True
	
			#Informe Object
			classificationResults = self.classification.classify(data2["text"])
			informe = 	{"created_at": data2["created_at"], "id_str" : data2["id_str"], "informe" :data2["text"], "timestamp_ms" :data2["timestamp_ms"], "topic": classificationResults[3],  "iob_label": classificationResults[1],  "coordinates": classificationResults[2]}
			
			#Request to nodejs server		
			r = requests.post(self.url, data=json.dumps(informe), headers=self.headers)
			if (r.status_code != 200): print ("Erro ao inserir no banco de dados")
			else: print ("Inserido")
			
		except BaseException as e:
			print("Error on_data: %s" % str(e))
		return True

	def on_error(self, status):
		print(status)
		return True    
		    
 
#------------------------------------------------------
# Function
# @params:
# @author: Monica
#------------------------------------------------------
def main(gazetteer, datasetFile, annotatedEntities, vocabularyFile):
	print("Geração dos módulos...")
	classification = Classification(gazetteer, datasetFile, annotatedEntities, vocabularyFile)
	#classification.teste()
	#return
	
	while (True):
		print("Esperando por tweets...")
		
		try:
			auth = OAuthHandler(consumerKey, consumerSecret)
			auth.set_access_token(accessToken, accessSecret)
			api = tweepy.API(auth)
			twitterStream = Stream(auth, MyListener(classification))
			#twitterStream.filter(follow=['8802752'])   #G1 - teste
			twitterStream.filter(follow=['524349796']) #BHTrans

		except ValueError:
			print("Erro: "+ValueError) 