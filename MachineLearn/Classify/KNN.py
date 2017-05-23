#--*--coding=utf-8--*--
from numpy import *
import operator
import matplotlib
import matplotlib.pyplot as plt

def createDataSet():
	group=array([[1.0,1.1],[1.0,1.0],[0,0],[0,0.1]])
	labels=['A','A','B','B']
	return group, labels

#for every point in our dataset:
#    calculate the distance between X and the current point
#    sort the distance in increasing order
#    take k items with lowest distence to X
#	 find the majority class among these items
# 	 return the majority class as our prediction for the class of X
#
#

def classify_KNN(x,dataSet,labels,k):
	dataSetSize=dataSet.shape[0]
	diffMat=tile(x,(dataSetSize,1))-dataSet
	sqDiffMat=diffMat**2
	sqDistance=sqDiffMat.sum(axis=1)
	distences=sqDistance**0.5
	sortedDistIndicies=distences.argsort()
	classCount={}
	for i in range(k):
		votelabel=labels[sortedDistIndicies[i]]
		classCount[votelabel]=classCount.get(votelabel,0)+1
	sortedClassCount=sorted(classCount.items(),key=operator.itemgetter(1),reverse=True)
	return sortedClassCount[0][0]

def file2matrix(filename):
	fr=open(filename)
	numberOfLines=len(fr.readlines())
	returnMat=zeros((numberOfLines,4))
	classLabelVector=[]
	fr=open(filename)
	index=0
	for line in fr.readlines():
		line=line.strip()
		listFromLine=line.split('\t')
		returnMat[index,:] = listFromLine[0:4]
		classLabelVector.append(listFromLine[-1])
		index += 1
	return returnMat,classLabelVector


#if __name__ == '__main__':
#	g,l=createDataSet()
#	classify_KNN([0,0],g,l,3)