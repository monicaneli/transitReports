#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, string, operator
from nlp import NLP
from ner import NER
from topicClassification import TopicClassification
 
class Classification:
	nlp = None
	ner = None
	topicModel = None
	abreviacoesList = [['próx', 'próximo'], ['próx.', 'próximo'], ['prox', 'próximo'], ['prox.', 'próximo'], ['px', 'próximo'], ['px.', 'próximo'], ['av', 'Avenida'], ['av.', 'Avenida'], ['pça', 'Praça'], ['sent', 'sentido'], ['sent.', 'sentido'], ['dª', 'Dona'], ['dª.', 'Dona'], ['d.ª', 'Dona'], ['sta', 'Santa'], ['vdt', 'Viaduto'], ['vdt.', 'Viaduto'], ['c\\', 'com'], ['p\\', 'para'], ['nº', 'número'], ['ref', 'referência'], ['ref.', 'referência'], ['elv', 'Elevado'], ['sra', 'Senhora'], ['gde', 'Grande'], ['prof', 'Professor'], ['prof.', 'Professor'], ['vtr', 'viatura'], ['vtr.', 'viatura'], ['r.', 'Rua']]
	
	def __init__(self, gazetteer, datasetFile, annotatedEntities, vocabularyFile):
		self.nlp = NLP()
		self.ner = NER(gazetteer, annotatedEntities)
		self.topicModel = TopicClassification(datasetFile, vocabularyFile)

	def preprocessing (self, sentence):		
		
		newSentence = sentence
		newSentence = re.sub('R\.', 'Rua', newSentence)

		#Remover termos ['RT', 'Km\h', 'km' , 'mm', 13h40, 30 min]		
		newSentence = re.sub('\d+\s*km/h', ' ', newSentence, flags=re.I)
		newSentence = re.sub('\d+\s*km', ' ', newSentence, flags=re.I)
		newSentence = re.sub('\d+h\d+', ' ', newSentence, flags=re.I)
		newSentence = re.sub('\d+h ', ' ', newSentence, flags=re.I)
		newSentence = re.sub('\d+hrs ', ' ', newSentence, flags=re.I)
		newSentence = re.sub('\d+\s*mm', ' ', newSentence)
		newSentence = re.sub('\s*RT ', ' ', newSentence)
		newSentence = re.sub('\d+\s*min\s', ' ', newSentence)	
		newSentence = re.sub(r'\s(\w+)…', ' ', newSentence)
		
		#BR 040 para BR040
		p = re.compile('BR\s*\d+')
		lista = p.findall(newSentence)
		for item in lista: newSentence = newSentence.replace(item, item.replace(' ', ''))

		#Remover Urls
		newSentence = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', ' ', newSentence)
		
		#Remover hashtags e mençoes de usuários @user
		newSentence = re.sub(r"(?:\@|https?\://)\S+", " ", newSentence)
		newSentence = re.sub(r"(#.*?)\s", " ", newSentence)
		
		#Remover caracteres especiais
		p = re.compile('(ª|º)')
		newSentence = p.sub(' ', newSentence)		
		newSentence = re.sub('\W', ' ', newSentence)		
		
		#Remover numeros
		newSentence = re.sub(' \d+',' ', newSentence).lstrip()
		
		#Remover pontuação
		for pontuacao in string.punctuation: newSentence = newSentence.replace(pontuacao, ' ')	
		
		#Expandir abreviações
		wordsList = newSentence.lower().split(" ")
		for word in self.abreviacoesList: 
			if (word[0] in wordsList):
				newSentence = re.sub(word[0], word[1], newSentence, flags=re.I) 
		
		#Removendo espaços extras
		newSentence = re.sub(' +',' ', newSentence)		
		return newSentence

	def classify(self, sentence):
		newSentence = self.preprocessing(sentence)
		sentenceTokens = self.nlp.tokenization(newSentence)		
		results = self.ner.dictionaryNER(sentenceTokens)
		labelIOB = results[0]
		coordinate = results[1]		
		topic = self.topicModel.predictTopic(newSentence)
		labelIOBnew = self.mergeResults(sentence, newSentence, labelIOB)
		return ([labelIOB, labelIOBnew, coordinate, topic])
				
	def mergeResults(self, sentence, preprocessedSentence, labelIOB):
		#print("\n" + sentence)
		#print(preprocessedSentence)
		
		#sentenceTokens = self.nlp.tokenization(sentence)
		newSentenceTokens = sentence.split(" ")
		preprocessedSentenceTokens = self.nlp.tokenization(preprocessedSentence)
		abreviacoes = list(map(operator.itemgetter(0), self.abreviacoesList))
			
		#newSentenceTokens = sentenceTokens
		#~ for idx, token in enumerate(sentenceTokens):
			#~ if (token == '.' and idx-1 > 0 and sentenceTokens[idx-1].lower() == 'av'):
				#~ newSentenceTokens.pop(idx)
				#~ newSentenceTokens[idx-1] = newSentenceTokens[idx-1]+'.'
		
		index = 0
		newLabelIOB = ""
		skipLoop = False
		for idx, item in enumerate(newSentenceTokens):
			if (skipLoop):
				skipLoop = False
				continue
				
			
			newItem = item
			for pontuacao in string.punctuation: newItem = newItem.replace(pontuacao, '')
			#print (newItem)
			
			if (index < len(preprocessedSentenceTokens) and item not in string.punctuation):
				#print (newItem + " vs " + preprocessedSentenceTokens[index])				
				if (newItem == preprocessedSentenceTokens[index] or item.lower() in abreviacoes):
					#print("<>> " + labelIOB[index])
					newLabelIOB = newLabelIOB + labelIOB[index]
					index += 1
					
				#palavras compostas
				elif (index+1 < len(preprocessedSentenceTokens) and item.find(preprocessedSentenceTokens[index]) != -1 and item.find(preprocessedSentenceTokens[index+1]) != -1):
					#print (">>>>>" + labelIOB[index] + " vs "+ labelIOB[index+1] + " = " + self.ner.andOperationIOB(labelIOB[index], labelIOB[index+1]))
					newLabelIOB = newLabelIOB + self.ner.andOperationIOB(labelIOB[index], labelIOB[index+1])
					index += 2
					
				#BR 262 e BR262
				elif(idx+1 < len(newSentenceTokens) and preprocessedSentenceTokens[index].find(item) != -1 and preprocessedSentenceTokens[index].find(newSentenceTokens[idx+1]) != -1):
					#print (">>>>>" + labelIOB[index] + " = " + labelIOB[index])
					if (labelIOB[index] == 'B'): 
						newLabelIOB = newLabelIOB + labelIOB[index] + 'I'
					else :
						newLabelIOB = newLabelIOB + labelIOB[index] + labelIOB[index]
					index += 1
					skipLoop = True
					
				else:
					#print('O')
					newLabelIOB = newLabelIOB + 'O'
			else:
				#print('O')
				newLabelIOB = newLabelIOB + 'O'
		
		if (len( newSentenceTokens) != len(newLabelIOB)):
			print ("::::ERROO::: Size senten:: "+str(len(newSentenceTokens)) +" / size label:: " + str(len(newLabelIOB)))
		
		newLabelIOB = self.excessoes(newLabelIOB, newSentenceTokens)
		#print (self.extractAnnotatedEntities(labelIOB, preprocessedSentenceTokens))	
		#print (self.extractAnnotatedEntities(newLabelIOB, newSentenceTokens))		
		#print (preprocessedSentenceTokens)	
		#print (newSentenceTokens)	
		return newLabelIOB

	def excessoes(self, newLabelIOB, sentenceTokens):
		lastB = 0
		for idx, token in enumerate(sentenceTokens):
			
			if (newLabelIOB[idx] == 'B'): lastB = idx
			
			#Sequencia tipo BOI devido à pontuacao
			if (idx+1 < len(newLabelIOB) and token in string.punctuation and (idx-lastB) <= 2 and newLabelIOB[idx+1] == "I"):
				newLabelIOB = newLabelIOB[0:idx] + "I" + newLabelIOB[idx+1:len(newLabelIOB)]		
				
			#Sequencia BOOI devido a termos removidos do pre-processamento
			elif (newLabelIOB[idx] == "I" and (idx-lastB) > 2  and newLabelIOB[idx-1] == 'O'):
				newLabelIOB = newLabelIOB[0:lastB] + "O" + newLabelIOB[lastB+1:len(newLabelIOB)]
				newLabelIOB = newLabelIOB[0:idx] + "O" + newLabelIOB[idx+1:len(newLabelIOB)]
		return newLabelIOB
	
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

	def teste(self):		
		
		print (self.classify('20h37 (+) / R. Pitangui / R. Alabastro / Av. Silviano Brandão / Av. Flávio dos Santos.'))
		#return
		print (self.classify('@g1 era porcelanato pelo menos?'))
		 
		print (self.classify('RT @g1: Luta contra leucemia vai exigir que aluna faça #Enem2016 no hospital https://t.co/aZV9zIvp1l #G1 https://t.co/WDwwzbk5h4'))

		print (self.classify('Operação especial na rodoviária (TERGIP), de 5/2 a 13/2, para o feriado do Carnaval 2016. https://t.co/vVIl36tG6A'))
		
		print (self.classify('RT @defesacivilbh: 15h46 - Risco de chuva (20 a 40 mm), raios e ventos (até 50 km/h). Até 23h59 de terça (16). @Bombeiros_MG #BH https://t.…'))
		
		print (self.classify('RT @Bombeiros_MG: 21h - Árvore de grande porte caída na BR 262 (Anel Rod), px à PUC São Gabriel, pista obstruída. Risco de colisões. 1 vtr …'))
		
		print (self.classify('@diih__campos Boa Tarde! O Quadro de Horários de segunda-feira corresponde ao de dia atípico e terça ao de feriado.'))		
		
		print (self.classify('RT @defesacivilbh: Acréscimo de 20 a 30mm do alerta emitido totalizando 70mm até 7h de terça (24) raios e rajadas vento de até 50 km/h. htt…'))		
		
		print (self.classify('Criação da Linha 825 (Estação São Gabriel / Vitória II via UPA Nordeste) a partir de domingo, dia 21/2. Confira: https://t.co/PV2OQkx10H'))
		
		print (self.classify('RT @PRF191MG: 10h30 - RETIFICAÇÃO: BR040 negociação ficou decidido pistas principais  ficarão liberadas por 30 min e depois serão fechadas …'))
		
		print (self.classify('Participe da 5ª Reunião do Observatório da Mobilidade Urbana de BH! Inscrições pelo link https://t.co/bMsvjwaLZZ'))
		
		print (self.classify('@dannymendes10 Boa Noite! Nossa equipe esteve no local e constatou a presença da CEMIG. Local sem energia elétrica.'))
		
