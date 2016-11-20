#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division, unicode_literals
import math
import nltk
import nltk.corpus
import csv
import re
import numpy
from sklearn import svm
from sklearn.externals import joblib
from nlp import NLP

class TopicClassification:
	nlp = NLP()
	stopwords = None
	vocabulary = []
	labelsTraining = []
	trainingInstances = []
	totalNumInstances = 2861
	instanceToPredict = []
	classifier = None
	vocabularyFile = None

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------			
	def __init__(self, dataset, vocabularyFile):
		self.stopwords = nltk.corpus.stopwords.words('portuguese')
		self.loadClassifier(vocabularyFile)
		#self.readTrainingFile0(dataset)
		#self.generateSVMClassifier()
		#self.predictTopic("Trânsito lento na Avenida bias fortes mas fluindo no sentido centro.")

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------			
	def predictTopic (self, sentence):
		instance = []
		instances = []
		sentenceTokens = self.tokenization(sentence.lower())
		tokensCount = {}
		for token in sentenceTokens: 		
			#Vocabulário
			if (token in self.vocabulary): 
				indexVocabulary = self.vocabulary.index(token)										
								
				#Contagem
				tokensCount[indexVocabulary] = self.tf(token, sentenceTokens)
	
		#Geração da Matriz
		vocabularySize = len(self.vocabulary)
		instance = [0]*vocabularySize
		for tupla in tokensCount.items(): instance[tupla[0]] = tupla[1]
		instances.append(instance)
		self.instanceToPredict = numpy.array(instances)
	
		#Instances
		for i,line in enumerate(self.instanceToPredict): 	
			#Terms
			for j,column in enumerate(line):
				self.instanceToPredict[i][j] = self.tfidf(column, self.instanceToPredict[:,j])
		
		#Classificação
		predictedLabel = self.classifier.predict(self.instanceToPredict)
		return predictedLabel[0]

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------			
	def loadClassifier (self, vocabularyFile):	
		#Loading Vocabulary
		self.vocabulary = []
		with open(vocabularyFile, 'r') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')			
			for row in spamreader:		
				termo = row[0]
				self.vocabulary.append(termo)
		
		#loading model		
		self.classifier = joblib.load('SVMmodel/svmModel.pkl') 
		
	#------------------------------------------------------
	# Function
	# computes term frequency: which is the number of times a word appears in a document, 
	# normalized by dividing by the total number of words in the document
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def tf(self, word, sentenceTokens):
		return sentenceTokens.count(word) / len(sentenceTokens)

	#------------------------------------------------------
	# Function
	# returns the number of documents containing word
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def n_containing(self, sentenceList):
		return sum(1 for sentence in sentenceList if sentence > 0)

	#------------------------------------------------------
	# Function
	# computes inverse document frequency: which measures how common a word 
	# is among all documents. The more common a word is, the lower its idf.
	# We take the ratio of the total number of documents to the number of 
	# documents containing word, then take the log of that. 
	# Add 1 to the divisor to prevent division by zero.
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def idf(self, sentenceList):
		return math.log(len(sentenceList) / (1.0  + self.n_containing(sentenceList)))

	#------------------------------------------------------
	# Function
	# computes the TF-IDF score
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def tfidf(self, TF, sentenceList):
		return TF * self.idf(sentenceList)

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------		
	def tokenization(self, sentence):
		return nltk.word_tokenize(str(sentence))

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------		
	def generateSVMClassifier(self):
		self.classifier = svm.LinearSVC()
		self.classifier.fit(self.trainingInstances, self.labelsTraining)
		joblib.dump(self.classifier, 'svmModel.pkl')
		return self.classifier	

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------				
	def extractAnnotatedEntities(self, patternLabel, sentenceTokens):
		occurrences = re.findall('(BI*)', patternLabel)
		entities = []
		newPattern = patternLabel
		indices = []

		for indx, occurrence in enumerate(occurrences):
			indexStart = newPattern.find(occurrences[indx])
			indices.append([indexStart, indexStart+len(occurrences[indx])])
			subs= ""
			for i in range(len(occurrences[indx])): subs= subs+'X'
			newPattern = newPattern.replace(occurrences[indx], subs, 1)

		termo = []
		for i,idx in enumerate(indices):
			for position in range(idx[0], idx[1]):
				termo.append(sentenceTokens[position])
				
			entities.append(" ".join(termo))
			termo = []
		return entities	

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------		
	def initiateModules(self):
		self.vocabulary = []

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------			
	def readTrainingFile0(self, fileNameTrainning):
		vocabularyFreq = []
		matrix = []
		instances = []		
		self.vocabularyFile = csv.writer(open("VocabularyFile.csv", 'w', newline=''))
		
		with open(fileNameTrainning, 'r') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
			
			for row in spamreader:
				sentence = row[1]				
				sentenceTokens = self.tokenization(sentence)
				
				#Removing entities
				entities = self.extractAnnotatedEntities(row[0], sentenceTokens)
				for entity in entities: sentence = sentence.replace(str(entity), '')
				sentenceTokens = self.tokenization(sentence.lower())
				
				tokensCount = {}
				self.labelsTraining.append(str(row[2]))
				
				for token in sentenceTokens: 						
					#Removendo stop-words
					if ((token not in self.stopwords)and (len(token) > 1) and (not token.isnumeric())):			
						#Vocabulário
						if (token not in self.vocabulary): self.vocabulary.append(token)	
						indexVocabulary = self.vocabulary.index(token)					
										
						#Contagem
						tokensCount[indexVocabulary] = self.tf(token, sentenceTokens)

				#Matriz
				matrix.append(tokensCount)
							
		vocabularySize = len(self.vocabulary)
		for item in self.vocabulary:
			self.vocabularyFile.writerow([item])
		
		#Generating Matrix of terms
		for line in matrix:
			instance = [0]*vocabularySize
			for tupla in line.items(): instance[tupla[0]] = tupla[1]
			instances.append(instance)		
		self.trainingInstances = numpy.array(instances)
		
		#Instances
		for i,line in enumerate(self.trainingInstances): 	
			#Terms
			for j,column in enumerate(line):
				self.trainingInstances[i][j] = self.tfidf(column, self.trainingInstances[:,j])
				