#!/usr/bin/python
# -*- coding: utf-8 -*-
import	nltk
import 	nltk.corpus, nltk.tag, itertools
from 	nltk.util 	import ngrams
from 	unicodedata import normalize

class NLP:
	keyWordsEncoded = ['avenida', 'rua', 'bairro', 'praça', 'trevo', 'elevado', 'trincheira', 'rodovia', 'curva', 'via', 'círculo', 'circulo', 'parque', 'área', 'area', 'rotatória', 'rotatoria', 'estrada']
	
	#'em', 'na', 'altura', 'expressa', 'sentido','próximo', 'proximo', 'prox', 'próx', 'ao'

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
	# @author: http://wiki.python.org.br/RemovedorDeAcentos#CA-ee056743639a7a1f3c8dac71f09c13863c354b09_18
	#------------------------------------------------------
	def tokenEncodeDecode(self, txt, codif='utf-8'):
		try:
			txt = normalize('NFKD', txt.decode(codif)).encode('ASCII','ignore')
		except Exception:
			txt = txt.encode('utf-8')
			txt = normalize('NFKD', txt.decode(codif)).encode('ASCII','ignore')
		return txt