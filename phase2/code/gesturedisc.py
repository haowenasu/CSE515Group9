import sys
import glob, os
import numpy as np
import math
import json
import csv
import ast
from collections import Counter
#from sets import Set
import pickle as pk
from sklearn.decomposition import PCA
from sklearn.decomposition import TruncatedSVD
from sklearn.decomposition import NMF
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.preprocessing import normalize
from scipy import spatial
from gestureeddtw import *

folder = sys.argv[1]
vecoption = sys.argv[2] # tf, tfidf
option = sys.argv[3]    # dotp, pca, svd, nmf, lda, ed, dtw
topp = int(sys.argv[4])

os.chdir(folder)

# load string, time series reprsentations
words = {}
for filename in glob.glob('*.wrd'):
    fn = os.path.splitext(filename)[0]
    with open(filename) as json_file:
        data = json.load(json_file)
        words[fn] = data

# load vector representations
if vecoption == 'tf':
    filename = folder + '/tf.txt'
elif vecoption == 'tfidf':
    filename = folder + '/tfidf.txt'
else:
    print('wrong vector model name')
with open(filename) as json_file:
    vec = json.load(json_file)

wordset = set()
gestureset = set()

for key, value in vec.items():
    li = ast.literal_eval(key)
    gestureset.add(li[0])
    wordset.add((li[1], li[2], li[3]))

w2i = {}
for idx, word in enumerate(wordset):
    w2i[word] = idx

gesturelist = sorted([int(v) for v in gestureset])
f2i = {} # map from document to index
i2f = {} # map from index to document
for idx, finset in enumerate(gesturelist):
    f2i[str(finset)] = idx
    i2f[idx] = str(finset)

# transform vector in dictionary to a matrix (row: word, column: file)
features = [[0.0] * len(w2i) for i in range(len(f2i))]
for key, val in vec.items():
    li = ast.literal_eval(key)
    features[f2i[li[0]]][w2i[(li[1], li[2], li[3])]] = val
print(len(features), len(features[0]))
X = np.array(features)

distmatrix = [[0.0] * len(f2i) for _ in range(len(f2i))]
dumpfile = vecoption + option + ".pkl"
if option == 'dotp':
    for i in range(len(f2i)):
        fea1 = features[i]
        for j in range(i, len(f2i)):
            fea2 = features[j]
            distmatrix[i][j] = distmatrix[j][i] = np.dot(fea1, fea2)
elif option == 'pca':
    pca_reload = pk.load(open(dumpfile,'rb'))
    X_reduced = pca_reload .transform(X)
    for i in range(len(f2i)):
        fea1 = X_reduced[i]
        for j in range(i, len(f2i)):
            fea2 = X_reduced[j]
            distmatrix[i][j] = distmatrix[j][i] = 1 - spatial.distance.cosine(fea1, fea2)
elif option == 'svd':
    svd_reload = pk.load(open(dumpfile,'rb'))
    X_reduced = svd_reload.transform(X)
    for i in range(len(f2i)):
        fea1 = X_reduced[i]
        for j in range(i, len(f2i)):
            fea2 = X_reduced[j]
            distmatrix[i][j] = distmatrix[j][i] = 1 - spatial.distance.cosine(fea1, fea2)
elif option == 'nmf':
    nmf_reload = pk.load(open(dumpfile,'rb'))
    X_reduced = nmf_reload.transform(X)
    for i in range(len(f2i)):
        fea1 = X_reduced[i]
        for j in range(i, len(f2i)):
            fea2 = X_reduced[j]
            distmatrix[i][j] = distmatrix[j][i] = 1 - spatial.distance.cosine(fea1, fea2)
elif option == 'lda':
    lda_reload = pk.load(open(dumpfile,'rb'))
    X_reduced = lda_reload.transform(X)
    for i in range(len(f2i)):
        fea1 = X_reduced[i]
        for j in range(i, len(f2i)):
            fea2 = X_reduced[j]
            distmatrix[i][j] = distmatrix[j][i] = 1 - spatial.distance.cosine(fea1, fea2)
elif option == 'ed':
    pass
elif option == 'dtw':
    datakey = 'winavg'
    for i in range(len(f2i)):
        gesture1 = words[i2f[i]]
        for j in range(i, len(f2i)):
            gesture2 = words[i2f[j]]
            series1 = []
            series2 = []
            avg1, avg2 = [], []
            std1, std2 = [], []
            for component, data in gesture2.items():
                for sensor, wins in data.items():
                    series2.append([v for k, v in sorted(wins[datakey].items(), key=lambda item: int(item[0]))])
                    series1.append([v for k, v in sorted(gesture1[component][sensor][datakey].items(), key=lambda item: int(item[0]))])
                    avg1.append(gesture1[component][sensor]['avg'])
                    avg2.append(wins['avg'])
                    std1.append(gesture1[component][sensor]['std'])
                    std2.append(wins['std'])
            distmatrix[i][j] = distmatrix[j][i] = dtw(series1, series2, avg1, avg2, std1, std2)

# convert distance to similarity
if option == 'ed' or option == 'dtw':
    mx, mn = max(max(distmatrix)), min(min(distmatrix))
    scale = mx - mn
    distmatrix = [[1 - (ele - mn) / scale for ele in row] for row in distmatrix]

# decomposition using SVD
u,s,v = np.linalg.svd(distmatrix)
print(len(u), len(u[0]))
print(u[:, 0 : topp])
print(s)
print([np.argmax(a) for a in u[ :, 0 : topp]])

# decomposition using NMF