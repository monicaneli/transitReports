#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import csv
import re
import operator
import numpy
from nlp import NLP
from dictionary import Dictionary

class NER:
	totalNumInstances = 2861
	minSupportValue = 1
	nlp = None
	dictionary = None
	posTagging = None

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------	
	def __init__(self, gazetteer, annotatedEntities):
		self.initiateModules(gazetteer)
		self.dicitionaryTraining(annotatedEntities)

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------			
	def initiateModules (self, gazetteer):
		self.nlp = NLP()
		self.dictionary = Dictionary(gazetteer)

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------		
	def dicitionaryTraining(self, annotatedEntities):		
		with open(annotatedEntities, 'r', encoding='utf-8') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
			for row in spamreader:				
				self.addToDictionary(row[0], { "lat": float(row[1]), "lng": float(row[2])})							
			csvfile.close()

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def andOperationIOB(self, label1, label2):
		if (len(label1) > len(label2)):
			aux = label1
			label1 = label2
			label2 = aux
		labelFinal = ""
		for idx, letter in enumerate(label1):
			#B vs O = B
			if ((letter == 'O' and label2[idx] == 'B') or (letter == 'B' and label2[idx] == 'O')):
				labelFinal=labelFinal + 'B'

			#B vs I = I
			elif ((letter == 'I' and label2[idx] == 'B') or (letter == 'B' and label2[idx] == 'I')):
				labelFinal=labelFinal + 'I'

			#O vs I = I
			elif ((letter == 'O' and label2[idx] == 'I') or (letter == 'I' and label2[idx] == 'O')):
				labelFinal=labelFinal + 'I'

			elif (letter == label2[idx]): labelFinal=labelFinal + letter
			
		if(len(label2) > len(label1)):
			labelFinal=labelFinal + label2[len(label2)-(len(label2)-len(label1)):]

		return labelFinal
		
	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def dictionaryNER(self, sentenceTokens):
		startingIndex = 1
		labelFinal = ""

		for token in sentenceTokens:
			nGram = []
			nGram.append(token)
			
			#Numeric
			if (not token.isnumeric()):
				matched = self.dictionary.verifyAddress(token)
			else: matched = None
			
			labelPrevious = ""

			#Token Recognized
			if (matched != None and len(matched)>=1):
				labelPrevious = 'B'
			
			#Token not recognized
			else: labelPrevious = 'O'
		
			#Appending tokens to get a new expression
			for idx in range(startingIndex, len(sentenceTokens)):
				labelIter = ""
				nGram.append(sentenceTokens[idx])
				matched = self.dictionary.verifyAddress(" ".join(nGram))

				#Expression recognized
				if (matched != None and len(matched)>=1):
					labelIter = 'B'
					for i in range(len(nGram)-1): labelIter = labelIter + 'I'
					
				else:
					for i in range(len(nGram)): labelIter = labelIter + 'O'
				
				labelPrevious = self.andOperationIOB(labelPrevious, labelIter)

			if (startingIndex >= 2):
				labelPrevious = self.andOperationIOB(labelFinal[startingIndex-1:], labelPrevious)
				labelFinal = labelFinal[:startingIndex-1] + labelPrevious
			else:
				labelFinal = labelPrevious
				
			startingIndex = startingIndex + 1
			
		self.bruteForceLabel = labelFinal
		firstCoordinate = self.getSentenceCoordinate(self.bruteForceLabel, sentenceTokens)
		return [self.bruteForceLabel, firstCoordinate]

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------		
	def getSentenceCoordinate(self, bruteForceLabel, sentenceTokens):
		coordinate = None
		entities = self.extractAnnotatedEntities(bruteForceLabel, sentenceTokens)
		result = self.dictionary.verifyAddress(entities[0])
		if (type(result) is list and type(result[0]) is not list): coordinate = result[1]
		else: coordinate = result[0][1]
		return coordinate
		
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
			entities.append(" ".join(termo).upper())
			termo = []
		return entities

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def addToDictionary(self, entity, coordinates):
		self.dictionary.addToDictionary(entity, coordinates)

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def getLabelGeo(self, labelPrevious, nGramSize, isGeo):
		labelSize = len(labelPrevious)
		if (isGeo):
			if (labelSize == 0): 
				labelPrevious = labelPrevious + 'B'
				for i in range(nGramSize-1): labelPrevious = labelPrevious + 'I'
				
			elif (labelPrevious[labelSize-1] == 'B'): 
				for i in range(nGramSize): labelPrevious = labelPrevious + 'I'
			elif (labelPrevious[labelSize-1] == 'I'): 
				for i in range(nGramSize): labelPrevious = labelPrevious + 'I'
			else: 
				labelPrevious = labelPrevious + 'B'
				for i in range(nGramSize-1): labelPrevious = labelPrevious + 'I'
		else:
			for i in range(nGramSize): labelPrevious = labelPrevious + 'O'
		return labelPrevious

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def shiftOp(self, labelFinal, labelPrevious, labelItem, index):
		labelPrevious = self.andOperationIOB(labelFinal[index:], labelItem)
		labelFinal = labelFinal[:index] + labelPrevious
		return labelFinal