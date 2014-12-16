import collections
import heapq
import math
import operator

__author__ = 'Daniel'

# get all posts from database
def get_all_posts():
    rows = []
    for row in db((db.posts.source==db.rssfeeds.source) & (db.posts.category==db.rssfeeds.category)).select(db.posts.ALL):
        text = row.text
        text = re.sub('\n', ' ', text)
        text = re.sub('\s+', ' ', text)
        rows.append(text)
    return rows

# delete from heap the element with value el
def deleteFromHeap(heap, el):
    index = heap.index(el*(-1))
    heap[index] = heap[-1]
    heap.pop()
    heapq._siftup(heap, index)

#returns the frequency of term in post
def term_frequency(term, post):
    total = post.count(term)
    return 1.0 * total / len(post)

#calculates indf for term in all the posts
def inverse_document_frequency(term, posts):
    total = 1
    for post in posts:
        if term in post:
            total = total + 1
    return math.log(1.0 * len(posts) / total)

#uses term_frequency and inverse_doc_frequency to calculate the top 12 keywords for a given post
def tf_idf(post, posts_splitted):
    tokens = {}
    sets = []
    for postw in posts_splitted:
        sets.append(set(postw))
    for term in post:
        w = term_frequency(term, post) * inverse_document_frequency(term, sets)
        tokens[term] = w
    sortedTFIDF = sorted(tokens.items(), key=operator.itemgetter(1), reverse=True)
    elems = collections.defaultdict(lambda: 0)
    if len(sortedTFIDF) > 13:
        for j in range(12):
            term = sortedTFIDF[j][0]
            weight = sortedTFIDF[j][1]
           # print term, ' <-> ', weight
            elems[term] = weight
        return elems
    return {}

# cosine similarity between two vectors d1 and d2
def similar(d1, d2):
    #presmetaj gorna suma od formulata
    sumagore = 0
    for n in d1:
        if n in d2:
            sumagore = sumagore + d1[n]*d2[n]
    #ako gornata suma e 0 nema potreba dolnite da se izminuvat i presmetuvat
    if sumagore == 0:
        return 0
    #presmetuvanje na dolnite sumi za dvata vektori soodvetno, za normalizacija
    sumadole1 = 0.0
    sumadole2 = 0.0
    for br in d1.values():
        sumadole1 += br*br
    for br in d2.values():
        sumadole2 += br*br
    sumadole1 = math.sqrt(sumadole1)
    sumadole2 = math.sqrt(sumadole2)
    #gorna / (dolna1 + dolna2)
    return 1.0 * sumagore  / sumadole1 / sumadole2

def merge_texts(post1, post2, posts_splitted):
    result = post1 + post2
    posts_splitted.append(result)
    res = tf_idf(result, posts_splitted)
    return res

# pocetno presmetuvanje na similarity za sekoj so sekoj
def fillInitHeap(vectors, simVec, vecSim, heap):
    N = len(vectors)
    for i in range(N):
        for j in range(i + 1, N):
            d1 = vectors[i]
            d2 = vectors[j]
            score = similar(d1, d2)
            if score > 0.6:
                #print i, '<->', j, ' ', score
                simVec[score] = simVec.get(score, [])+[[i, j]]
                vecSim[i] = vecSim.get(i, []) + [score]
                vecSim[j] = vecSim.get(j, []) + [score]
                heapq.heappush(heap, score*(-1))


#greska
def hac(heap, vectors, simVec, vecSim, posts_splitted):
    N = len(vectors)
    hashMerged = {}
    K = len(vectors)
    deleted = []
    while(heap):
        resultVector = getBestSimilarity(simVec, vecSim, heap)
        deleted = deleted + resultVector
        newVector = merge_texts(posts_splitted[resultVector[0]], posts_splitted[resultVector[1]], posts_splitted)
        vectors.append(newVector)
        for i in range(N):
            if not i in deleted:
                d1 = vectors[i]
                score = similar(d1, newVector)
                if score > 0.6:
                    print i, '<->', resultVector[0],' ' , resultVector[1], ' ', score
                    #TODO: TUKA E GRESKATA
                    simVec[score] = simVec.get(score, [])+[[i, K]]
                    vecSim[i] = vecSim.get(i, []) + [score]
                    vecSim[K] = vecSim.get(K, []) + [score]
                    heapq.heappush(heap, score*(-1))

        hashMerged[K] = resultVector
        K = K+1
    return hashMerged

# return the largest value for similarity between two vectors
def getBestSimilarity(simVec, vecSim, heap):
    value = heapq.heappop(heap) * (-1)
    #TODO: VO HAC e loguckata greska tuka dava index out of bound
    resultVector = simVec[value].pop(0)

    vecSim[resultVector[0]].remove(value)
    vecSim[resultVector[1]].remove(value)

    if vecSim[resultVector[0]] != []:
        for el in vecSim[resultVector[0]]:
            deleteFromHeap(heap, el)
            vecSim[resultVector[0]].remove(el)
            pars = []
            for par in simVec[el]:
                if resultVector[0] in par:
                    simVec[el].remove(par)
                    pars = pars + par
            for item in pars:
                if item != resultVector[0]:
                    vecSim[item].remove(el)


    if vecSim[resultVector[1]] != []:
        for el in vecSim[resultVector[1]]:
            deleteFromHeap(heap, el)
            vecSim[resultVector[1]].remove(el)
            pars = []
            for par in simVec[el]:
                if resultVector[1] in par:
                    simVec[el].remove(par)
                    pars = pars + par
            for item in pars:
                if item != resultVector[1]:
                    vecSim[item].remove(el)
    return resultVector

#majka i tatko na site funkcii
def clustering(posts):
    posts_splitted = []
    vectors = []
    simVec = {}
    vecSim = {}
    heap = []
    for post in posts:
        posts_splitted.append(post.split(' '))
    print 'posts splitted'
    for i in range(400):
        print 'index: ', i
        vectors.append(tf_idf(posts_splitted[i], posts_splitted))
    print 'tf-idf finished'
    fillInitHeap(vectors, simVec, vecSim, heap)
    result = hac(heap, vectors, simVec, vecSim, posts_splitted)
    for key in result:
        print key, ' ', result[key]