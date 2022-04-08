import os
from soqal import SOQAL
import sys
import pickle

sys.path.append(os.path.abspath("retriever"))
from retriever.TfidfRetriever import *
from retriever.GoogleSearchRetriever import *
from retriever.CustomRetriever import *


sys.path.append(os.path.abspath("bert"))
from bert.Bert_model import BERT_model
from bert.evaluate import *


def accuracy_full_system(AI, dataset, args):
    with open(dataset) as f:
        dataset = json.load(f)['data']
    question_no = 0
    exact_match_1 = 0
    exact_match_3 = 0
    exact_match_5 = 0
    f1_1 = 0
    f1_3 = 0
    f1_5 = 0
    AI.ask_all(dataset, args)
    """
    for article in dataset:
        for paragraph in article['paragraphs']:
            for qa in paragraph['qas']:
                response = AI.ask(qa['question'])
                question_no = question_no + 1
                exact_match_max_1 = 0
                f1_max_1 = 0
                f1_max_3 = 0
                exact_match_max_3 = 0
                f1_max_5 = 0
                exact_match_max_5 = 0
                for answer in qa['answers']:
                    print("Question number is: " + str(question_no))
                    print("Question is: " + qa['question'])
                    print("result is: " + str(response))
                    print("ground truth is: " + str(answer['text']))
                    for i in range(len(response)):
                        if i < 1:
                            exact_match_max_1 = max(exact_match_max_1, exact_match_score(response[i], answer['text']))
                            f1_max_1 = max(f1_max_1, f1_score(response[i], answer['text']))
                        if i < 3:
                            exact_match_max_3 = max(exact_match_max_3, exact_match_score(response[i], answer['text']))
                            f1_max_3 = max(f1_max_3, f1_score(response[i], answer['text']))
                        if i < 5:
                            exact_match_max_5 = max(exact_match_max_5, exact_match_score(response[i], answer['text']))
                            f1_max_5 = max(f1_max_5, f1_score(response[i], answer['text']))

                exact_match_1 += exact_match_max_1
                f1_1 += f1_max_1
                exact_match_3 += exact_match_max_3
                f1_3 += f1_max_3
                exact_match_5 += exact_match_max_5
                f1_5 += f1_max_5

                print("exact match score 1 = " + str(exact_match_1))
                print("exact match score 3 = " + str(exact_match_3))
                print("exact match score 5 = " + str(exact_match_5))
                print("f1 score 1 = " + str(f1_1))
                print("f3 score 1 = " + str(f1_3))
                print("f5 score 1 = " + str(f1_5))
                print("percent exact match score 1 = " + str(exact_match_1 / question_no))
                print("percent exact match score 3 = " + str(exact_match_3 / question_no))
                print("percent exact match score 5 = " + str(exact_match_5 / question_no))
                print("percent f1 score 1 = " + str(f1_1 / question_no))
                print("percent f3 score 1 = " + str(f1_3 / question_no))
                print("percent f5 score 1 = " + str(f1_5 / question_no))
    print("Final exact match score 1 = " + str(exact_match_1 / question_no))
    print("Final exact match score 3 = " + str(exact_match_3 / question_no))
    print("Final exact match score 5 = " + str(exact_match_5 / question_no))
    print("Final f1 score 1 = " + str(f1_1 / question_no))
    print("Final f3 score 1 = " + str(f1_3 / question_no))
    print("Final f5 score 1 = " + str(f1_5 / question_no))
    """


def accuracy_system(AI, args):
    dataset_path = "data/tydiqa-goldp-dev-arabic.json"
    accuracy_full_system(AI, dataset_path, args)


import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help='Path to bert_config.json', required=True)
parser.add_argument('-v', '--vocab', help='Path to vocab.txt', required=True)
parser.add_argument('-o', '--output', help='Directory of model outputs', required=True)
parser.add_argument('-g', '--google', help='use tf-idf or google', required=False, default='f')
parser.add_argument('-r', '--ret-path', help='Retriever Path', required=False, default='retriever/tfidfretriever.p')
parser.add_argument('-rc', '--retCache', help='Retriever cache', required=False, default='t')
parser.add_argument('-pm', '--pre-model', help='Preprocess model', required=False, default=None)
parser.add_argument('-a', '--aggregate', help='Aggregate function', required=False, default='o')
parser.add_argument('-w', '--wiki-path', help='Wikipedia Path', required=True)



def main():
    args = parser.parse_args()
    if args.google == 't':
        base_r = pickle.load(open(args.ret_path, "rb"))
        wiki_data = pickle.load(open(args.wiki_path, "rb"))
        ret = CustomRetriever(base_r, wiki_data, 50, 10)
    else:
        base_r = pickle.load(open(args.ret_path, "rb"))
        ret = HierarchicalTfidf(base_r, 50, 50)

    red = BERT_model(args.config, args.vocab, args.output)
    AI = SOQAL(ret, red, 0.999, args.pre_model, args.aggregate)
    accuracy_system(AI, args)


if __name__ == "__main__":
    main()