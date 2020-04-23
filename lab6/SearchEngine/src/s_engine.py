import time
import os
from datetime import timedelta

import numpy as np
import scipy as sp
from scipy import sparse

import heapq
import itertools

from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
import nltk

NORMED = 0
SVD = 1
NOIDF = 2

articles_path = "resources/articles"
index_map_path = "resources/map.txt"
u_path = "resources/svd/u.npy"
dvt_path = "resources/svd/dvt.npy"
idf_path = "resources/svd/idf.npy"
terms_matrix_path = "resources/sparse/terms_matrix.npz"
terms_matrix_noidf_path = "resources/sparse/terms_matrix_noidf.npz"
paths = ["resources/svd", "resources/sparse"]


try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find("corpora/words")
except LookupError:
    nltk.download('words')

s_words = set(stopwords.words("english"))
allowed_words_set = set(nltk.corpus.words.words())

def get_all_txt(path):
    list_of_files = []
    for r, _, files in os.walk(path):
        for f in files:
            if f.endswith(".txt") and os.path.getsize(os.path.join(r,f)) > 0: 
                list_of_files.append(os.path.join(r,f))
    return list_of_files

    
def article_reader(file_name):
    with open(file_name, 'r') as file:
        for line in file.readlines():
            for word in line.split(" "):
                if word and (word not in s_words) and (word in allowed_words_set) and (not word.isnumeric()):
                    yield word

                    
def word_trim(word):
    stemmer = PorterStemmer()
    return stemmer.stem(word)
    

class SearchEngine:
    def __init__(self, preprocess=False, k=None):
        self.filenames = get_all_txt(articles_path)
        self.files_count = len(self.filenames)
            

        self.word_map = {}
        self.index_map = None
        self.bag_of_words = None
        self.terms_matrix_noidf = None
        self.terms_matrix = None
        self.idf_m = None

        self.u = None
        self.dvt = None
        
        if preprocess:
            if not os.path.isdir("resources/articles"):
                raise("Cannot run engine without ./resources/articles")
            for p in paths:
                if not os.path.isdir(p):
                    os.mkdir(p)
            self.compute_bag_of_words()
            self.create_mappings()
            open(index_map_path, "w").writelines(f"{word}\n" for word in self.index_map)
            self.words_count = len(self.index_map)

            if k is not None:
                self.current_k = k
            else:
                cand_k = int(self.words_count / 50)
                if cand_k > 5:
                    if cand_k < self.files_count:
                        self.current_k = cand_k
                    else:
                        self.current_k = self.files_count
                else:
                    self.current_k = 5
            
            self.compute_terms_matrix()
            sparse.save_npz(terms_matrix_path, self.terms_matrix)
            sparse.save_npz(terms_matrix_noidf_path, self.terms_matrix_noidf)
            np.save(idf_path, self.idf_m)
            
            self.compute_svd()
            np.save(u_path, self.u)
            np.save(dvt_path, self.dvt)
        
        else:
            self.u = np.load(u_path)
            self.dvt = np.load(dvt_path)
            self.idf_m = np.load(idf_path)
            self.index_map = [word.rstrip() for word in open(index_map_path, "r").readlines()]
            for (i, word) in enumerate(self.index_map):
                self.word_map[word] = i
            self.terms_matrix = sparse.load_npz(terms_matrix_path)
            self.terms_matrix_noidf = sparse.load_npz(terms_matrix_noidf_path)
            self.words_count = len(self.index_map)

            if k is not None:
                self.current_k = k
            else:
                cand_k = int(self.words_count / 50)
                if cand_k < 5:
                    self.current_k = 5
                if cand_k < self.files_count:
                    self.current_k = cand_k
                else:
                    self.current_k = self.files_count

            print(self.words_count)
    
    
    def compute_bag_of_words(self):
        print("Computing bag of words...")
        start = time.time()
        self.bag_of_words = set()
        for file in self.filenames:
            for word in article_reader(file):
                self.bag_of_words.add(word_trim(word))
        print(f"Done in {timedelta(seconds=(time.time()-start))}.\n__________________________")


    def create_mappings(self):
        print("Creating mappings...")
        start = time.time()
        self.index_map = []
        for (i, word) in enumerate(self.bag_of_words):
            self.index_map.append(word)
            self.word_map[word] = i
        print(f"Done in {timedelta(seconds=(time.time()-start))}")
        print(f"Words quantity: {len(self.index_map)}")
        print("__________________________")


    def compute_terms_matrix(self):
        tmp_matrix = sparse.lil_matrix((self.words_count, self.files_count), dtype=np.float32)
        print("Terms matrix computing...")
        start = time.time()
        for i, file_name in enumerate(self.filenames):
            for word in article_reader(file_name):
                tmp_matrix[self.word_map[word_trim(word)], i] += 1
        
        self.terms_matrix = tmp_matrix.tocsr()
        self.terms_matrix_noidf = tmp_matrix.tocsr()
        print(f"Done in {timedelta(seconds=(time.time()-start))}.\n__________________________")
        
        print("IDF formatting...")
        start = time.time()
        self.idf()
        self.idf_matrix_format()
        print(f"Done in {timedelta(seconds=(time.time()-start))}.\n__________________________")
        
        print("Terms matrix normalizing...")
        start = time.time()
        d_norms = sparse.linalg.norm(self.terms_matrix, axis=0)
        d_norms_noidf = sparse.linalg.norm(self.terms_matrix_noidf, axis=0)
        
        non_zero_tmp = self.terms_matrix.nonzero()
        non_zero = itertools.zip_longest(non_zero_tmp[0], non_zero_tmp[1])
        for (row, col) in non_zero:
            self.terms_matrix[row, col] = self.terms_matrix[row, col] / d_norms[col]
            self.terms_matrix_noidf[row, col] = self.terms_matrix_noidf[row, col] / d_norms_noidf[col]
        print(f"Done in {timedelta(seconds=(time.time()-start))}.\n__________________________")
        
        
    def compute_svd(self):
        print("Computing SVD decomposition...")
        start = time.time()
        self.u, d, vt = sparse.linalg.svds(self.terms_matrix,k=self.current_k)
        print(f"Done in {timedelta(seconds=(time.time()-start))}.\n__________________________")
        
        print("Computing D @ V.T...")
        start = time.time()
        self.dvt = sparse.diags(d).dot(vt)
        print(f"Done in {timedelta(seconds=(time.time()-start))}.\n__________________________")
        
        print("Preparing D @ V.T to give normalized Ak matrix...")
        start = time.time()
        for col in range(self.files_count):
            norm = np.linalg.norm(self.u @ self.dvt[:,col])
            self.dvt[:,col] /= norm
        print(f"Done in {timedelta(seconds=(time.time()-start))}.\n__________________________")


    def words_frequency(self, words):
        result = sparse.lil_matrix((1, self.words_count), dtype=np.float32)
        for word in words:
            trimmed = word_trim(word)
            if trimmed in self.word_map:
                result[0, self.word_map[trimmed]] += 1
        return result.tocsr()


    def idf(self):
        self.idf_m = np.zeros(self.words_count, dtype=np.float32)
        
        non_zero_tmp = self.terms_matrix.nonzero()
        non_zero = itertools.zip_longest(non_zero_tmp[0], non_zero_tmp[1])
        for (row_n, col_n) in non_zero:
            self.idf_m[row_n] += 1
        
        for row_n in range(self.words_count):
            self.idf_m[row_n] = np.log(self.files_count / self.idf_m[row_n])


    def idf_matrix_format(self):
        non_zero_tmp = self.terms_matrix.nonzero()
        non_zero = itertools.zip_longest(non_zero_tmp[0], non_zero_tmp[1])
        for (row_n, col_n) in non_zero:
            self.terms_matrix[row_n, col_n] = self.terms_matrix[row_n, col_n] * self.idf_m[row_n]


    def calculate_probability_normed(self, key_words):
        q_vec = sparse.csr_matrix(self.words_frequency(key_words).multiply(self.idf_m))
        
        q_norm = sparse.linalg.norm(q_vec)
        if q_norm == 0:
            return None
        q_vec = q_vec / q_norm
        
        return sparse.csr_matrix.dot(q_vec, self.terms_matrix)


    def calculate_probability_noidf(self, key_words):
        q_vec = sparse.csr_matrix(self.words_frequency(key_words))
        
        q_norm = sparse.linalg.norm(q_vec)
        if q_norm == 0:
            return None
        q_vec = q_vec / q_norm
        
        return sparse.csr_matrix.dot(q_vec, self.terms_matrix_noidf)
        
    
    def calculate_probability_svd(self, key_words):        
        q_vec = sparse.csr_matrix(self.words_frequency(key_words).multiply(self.idf_m))
        q_norm = sparse.linalg.norm(q_vec)
        if q_norm == 0:
            return None
        q_vec = q_vec / q_norm
        
        to_return = sparse.csr_matrix(q_vec).dot(self.u).dot(self.dvt)
        return to_return
        

    def find_n_articles(self, key_words, n, mode=NORMED):
        if self.terms_matrix is None:
            raise("Terms Matrix not calculated")
        
        if mode == NORMED:
            probs = self.calculate_probability_normed(key_words)
        elif mode == SVD:
            probs = self.calculate_probability_svd(key_words)
        elif mode == NOIDF:
            probs = self.calculate_probability_noidf(key_words)
        else:
            raise("Chosen search mode is invalid")
        
        if probs is None:
            return []
        results = [(self.filenames[i], probs[0, i]) for i in probs.nonzero()[1]]
        return heapq.nlargest(n, results, key=lambda t: t[1])
