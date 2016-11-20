import	 sys
import crawler
from classification import Classification

class Main:
	gazetteer 			= sys.argv[1]
	dataset 			= sys.argv[2]
	annotatedEntities 	= sys.argv[3]
	vocabularyFile 		= sys.argv[4]
	
	crawler.main(gazetteer, dataset, annotatedEntities, vocabularyFile)