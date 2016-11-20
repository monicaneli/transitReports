#!/usr/bin/python
# -*- coding: utf-8 -*-
import Levenshtein
import unicodedata
import nltk.corpus
import string
import re
import csv

class Dictionary:
	dicionario = {}
	sortedKeys = None
	stopwords = None
	keyWordsEncoded = ['avenida', 'rua', 'bairro', 'rodovia', 'elevado', 'praca', 'praça']
	
	#parameters
	matchesLimitNumber = 3
	distanciaMax = 1
	minimumTermsNumber = 2
	minumumUppercaseTerms = 0.5
	minumumStopWordsTerms = 0.5
	minimumWordSize = 4
	
	def __init__(self, gazetteer):
		self.dicionario = {}
		self.sortedKeys = None
		self.stopwords = None
		self.stopwords = nltk.corpus.stopwords.words('portuguese')		
		self.readGazetteer(gazetteer)					
		#self.dictionaryInfo()		

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def dictionaryInfo(self):
		vals = 0
		self.sortedKeys = sorted(self.dicionario)
		print ("\n---------DICTIONARY PRE-PROCESSING--------")
		print ("Dictionary keys: " + str(len(self.sortedKeys)))
		for key in self.sortedKeys:
			vals = vals + len(self.dicionario[key])
		print ("Dictionary values: " + str(vals))
		print ("-----------------------------------------------\n")

	#------------------------------------------------------
	# Function extractKey
	# @params: address
	# @author: Monica
	#------------------------------------------------------
	def extractKey(self, address):
		words = str(address).split(' ')
		key = ''
		for word in words: key = key + word[0]
		return key

	#------------------------------------------------------
	# Function addToDictionary and get the coordinates
	# @params: key, address
	# @author: Monica
	#------------------------------------------------------
	def addToDictionary(self, address, coordinates):
		#Remover termos de categoria de endereço
		address = self.removeAddressCategory(address)
		
		if (address != "" and address != " "):	
			#Starts with stopwords
			addressTokens = address.split(" ")
			if (addressTokens[0] in self.stopwords):
				for index,word in enumerate(addressTokens):
					if (not word in self.stopwords):				
						newVersionOfAddress = addressTokens[index: len(addressTokens)]
						self.addToDictionary(" ".join(newVersionOfAddress))
						break
			
			#Extract the entry key
			key = self.extractKey(address)
						
			if (not(key in self.dicionario)):
				self.dicionario[key] = []
				
				#Add entry (address
				self.dicionario[key].append([address, coordinates])
			else:
				if (not (address in self.dicionario[key])):
					self.dicionario[key].append([address, coordinates])
			
	#------------------------------------------------------
	# Function addToDictionary
	# @params: key, address
	# @author: Monica
	#------------------------------------------------------
	def addToGazetteer(self, address, coords):
		#Remover termos de categoria de endereço
		address = self.removeAddressCategory(address)
		
		if (address != "" and address != " "):		
			#Extract the entry key
			key = self.extractKey(address)
			
			if (not(key in self.dicionario)):
				self.dicionario[key] = []
				
				#Add entry (address
				self.dicionario[key].append([address, coords])
			else:
				if (not (address in self.dicionario[key])):
					self.dicionario[key].append([address, coords])			
				
	#------------------------------------------------------
	# Function readDictionary
	# @params: fileName
	# @author: Monica
	#------------------------------------------------------
	def readGazetteer(self, fileName):
		f = open(fileName, 'r')

		for line in f:
			entry = line
			entry = entry.replace('\n', "")
			entry = entry.split(",")
			
			address= str(entry[0])
			coords = {"lat": float(entry[1]), "lng": float(entry[2])}			
			self.addToGazetteer( address, coords)

		f.close()

	#------------------------------------------------------
	# Function getDistance
	# Description: returns the entries matched and the indices of distances 
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def getDistance(self, addressItem, dicionaryEntry, addressesMatched):
		indices = []
		
		#Original version of dictionary entry
		if (type(dicionaryEntry[1]) is not list):
			address = dicionaryEntry[0]
			addressEntry = dicionaryEntry[0]
			coordinate = dicionaryEntry[1]			
		else:
			#Abreviated version of dictionary entry
			address = dicionaryEntry[0]
		
			#Original Dictionary entry
			addressEntry = dicionaryEntry[1][0]
			coordinate = dicionaryEntry[1][1]	
				
		distancia = Levenshtein.distance(str(addressItem), str(address))
		
		if (distancia >= 0 and distancia <= self.distanciaMax):
			if (not distancia in addressesMatched):
				addressesMatched[distancia] = []

			#Adiciona a entrada do dicionário que casou
			if (not address in addressesMatched[distancia]):
				indices.append(distancia)
				indices.append(len(addressesMatched[distancia]))
				addressesMatched[distancia].append([addressEntry, coordinate])

		return indices


	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def verifyCompleteAddress(self, key, addressToVerify, addressesMatched):
		#vetor de distancias matched
		indices = []
		matched = False
		
		#Verificando endereço sem abreviações
		if (key in self.dicionario):
			#casamento de cadeias
			for dicionaryEntry in self.dicionario[key]:
				indices = self.getDistance(addressToVerify, dicionaryEntry, addressesMatched)
				if (len(indices) > 0):
					matched = True
					if (len(addressesMatched) >= self.matchesLimitNumber): break
		return matched	
		
	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def verifyAbbreviatedAddress(self, key, addressToVerify, addressesMatched):
		#vetor de distancias matched
		indices = []
		matched = False
		isAbbreviated = False
		
		words = str(addressToVerify).split(" ")
		for word in words:
			if (len(word) == 1): isAbbreviated = True
		if(not isAbbreviated): return matched
			
		#casamento de cadeias
		for dicionaryEntry in self.dicionario[key]:			
			addressEntry = dicionaryEntry[0]
			coordinate = dicionaryEntry[1]
			
			words = str(addressToVerify).split(" ")
			dicionarioAddress = str(addressEntry).split(" ")
			abbreviatedAddressEntry = addressEntry

			#Abreviando o Endereço do Dicionário de acordo com o padrão
			i = 0
			for word in words:
				if (len(word) == 1):
						abbreviatedAddressEntry = str(abbreviatedAddressEntry).replace(dicionarioAddress[i], dicionarioAddress[i][0])
				i = i + 1			
			
			indices = self.getDistance(addressToVerify, [abbreviatedAddressEntry, [addressEntry, coordinate]], addressesMatched)
			if (len(indices) > 0):
				matched = True
				distance = indices[0]
				numberOfMatches = indices[1]				
				addressesMatched[distance][numberOfMatches] = dicionaryEntry
				if (len(addressesMatched) >= self.matchesLimitNumber): break
		
		return matched

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def verifyApproximatedAddress(self, key, addressToVerify, addressesMatched):
		#vetor de distancias matched
		indices = []
		matched = False
		increment = True
		
		#Verificando endereço sem abreviações
		for keyEntry in self.dicionario.keys():
			if (keyEntry[0] == key):			
				#casamento de cadeias
				for dicionaryEntry in self.dicionario[keyEntry]:
					addressEntry = dicionaryEntry[0]
					coordinate = dicionaryEntry[1]

					words = str(addressToVerify).split(" ")
					dicionarioAddress = str(addressEntry).split(" ")
					abbreviatedAddressEntry = addressEntry 
					
					if (len(words) >= len(dicionarioAddress)):
						expression0 = words
						expression1 = dicionarioAddress
					else:
						expression0 = dicionarioAddress
						expression1 = words
									
					#Abreviando o Endereço do Dicionário de acordo com o padrão
					i = 0
					for term in expression0:
						increment = True
						if (i < len(expression1)):
							#abreviar
							if (expression1[i][0] == term[0] and len(expression1[i]) != len(term)):
								abbreviatedAddressEntry = str(abbreviatedAddressEntry).replace(dicionarioAddress[i], dicionarioAddress[i][0])
							
							#Remove middle word
							elif (expression1[i][0] != term[0] or Levenshtein.distance(str(expression1[i]), str(term)) > 0):
								abbreviatedAddressEntry = str(abbreviatedAddressEntry).replace(dicionarioAddress[i], "")
								increment = False
							
						if (increment): i = i + 1
					
					abbreviatedAddressEntry = re.sub('\s+', ' ', abbreviatedAddressEntry).strip()
					indices = self.getDistance(addressToVerify, [abbreviatedAddressEntry, [addressEntry, coordinate]], addressesMatched)
					if (len(indices) > 0):
						matched = True
		return matched			
		
	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def addressTermsFilter(self, address):
		words = address.split(" ")
		newAddress = []	
		
		#Avoid evaluating numbers
		if (not words[0].isnumeric()):
			
			#Do not evaluate only stopwords
			onlyStopWords = True
			for word in words:
				if (not word in self.stopwords): onlyStopWords = False
			
			if (not onlyStopWords):
				#Removing address category terms
				for index, token in enumerate(words):
					if (token != "" and token != " "): 
						if (token.lower() not in self.keyWordsEncoded): 
							newAddress = words[index: len(words)]
							break
							
		#Remover acentos e cedilhas
		return (self.remover_acentos(" ".join(newAddress)))

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def removeAddressCategory(self, address):
		newAddress = []
		words = address.split(" ")

		#Removing address category terms
		for index, token in enumerate(words):
			if (token != "" and token != " "): 
				if (token.lower() not in self.keyWordsEncoded): 
					newAddress = words[index: len(words)]
					break
				
		return (" ".join(newAddress))

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def stopWordsFilter(self, addressToVerify):
		toContinue = True
		
		wordsTest = str(addressToVerify).split(" ")			
		stopwordsCount = 0
		lowercaseWords = 0
		
		#Conditions to avoid be evaluated
		if (wordsTest[0].isnumeric()): toContinue = False
		if (wordsTest[0] in self.stopwords): toContinue = False
		
		return toContinue

	#------------------------------------------------------
	# Function
	# @params:
	# @author: Monica
	#------------------------------------------------------
	def verifyAddress(self, address):
		addressesMatched = {}
		result = []
		indices = None
		matched = False
		
		address = self.addressTermsFilter(address)
		if (address == "" or address == " "): return None
		
		#Extraindo key
		addressToVerify = str(address)
		key = self.extractKey(addressToVerify)
		
		#Verificando endereço sem abreviações
		matched = self.verifyCompleteAddress(key, addressToVerify, addressesMatched)
			
		#Verificando possíveis abreviações
		if (not matched and key in self.dicionario):
			matched = self.verifyAbbreviatedAddress(key, addressToVerify, addressesMatched)
		
		#Verificando possíveis termos utilizando apenas o primeiro termo da expressão
		if (not matched and key[0] in self.dicionario):
			matched = self.verifyCompleteAddress(key[0], addressToVerify, addressesMatched)

		#Casamento aproximado
		if (not matched and key[0] in self.dicionario):
			matched = self.verifyApproximatedAddress(key[0], addressToVerify, addressesMatched)
			
		distanceVector = sorted(addressesMatched)

		# Resultado com mais de uma distancia de edicao
		if (len(addressesMatched) > 1):
			i = 0
			#Escolhendo o conj de menor distancia de edicao
			while (len(result) == 0 and i < len(addressesMatched)):
				if (i in addressesMatched): result.append(addressesMatched[distanceVector[i]])
				else : i = i + 1
			
			#Resultados com menor distancia de edição
			if (len(result) > 1): result = result[0]
			elif (len(result)== 1): result = result[0][0]

		
		# Resultado apenas uma distancia de edicao
		elif (len(addressesMatched) > 0):			
			
			#Resultados com menor distancia de edição
			if (len(list(addressesMatched.values())[0]) == 1):
				result = list(addressesMatched.values())[0][0]
			else:
				result = list(addressesMatched.values())[0]

		# Sem resultados
		else:
			result = None
					
		if (result != None and type(result) is not list): print (">>>>> ERRO1")
		if (result != None and (type(result[0]) is list and len(result) <= 1)):print (">>>>>> ERRO2")
		if (result != None and (type(result[0]) is not list and type(result[0]) is not str)): print (">>>>>>> ERRO3")
		
		return result

	#------------------------------------------------------
	# Function
	# @params:
	# @author: http://wiki.python.org.br/RemovedorDeAcentos#CA-ee056743639a7a1f3c8dac71f09c13863c354b09_18
	#------------------------------------------------------
	def remover_acentos(self, txt, codif='utf-8'):
		result = []
		
		words = str(txt).split(" ")
		for word in words:
			i = "".join(x for x in unicodedata.normalize('NFKD', word) if x in string.ascii_letters).upper()
			if (i != ''): result.append(i)
		return " ".join(result)
		
		try:
			txt = normalize('NFKD', txt.decode(codif)).encode('ASCII','ignore').upper()
		except Exception:
			txt = txt.encode('utf-8')
			txt = normalize('NFKD', txt.decode(codif)).encode('ASCII','ignore').upper()
		return txt

