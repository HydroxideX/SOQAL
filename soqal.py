import numpy as np
import sys

import pprint
import os

from retriever_cache import retriever_cache

sys.path.append(os.path.abspath("araelectratf"))
import os.path

from bert.evaluate import *
from araElectra.pytorch.QA import QA
from araelectratf.run_finetuning import *


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


class SOQAL:
    def __init__(self, retriever, reader, beta, preprocessor_model=None, aggregate_function='o'):
        self.retriever = retriever
        self.beta = beta
        self.reader = reader
        self.retriever_cache = retriever_cache(retriever)
        
        self.retriever_cache.load_retriever_cache()
        if preprocessor_model is not None:
            print("Using preprocessing for context/question")
            self.preprocessor = QA(preprocessor_model)
        else:
            print("Not using preprocessing!")
            self.preprocessor = None
        self.aggregate = aggregate_function

    def build_quest_json_full(self, questions, list_docs):
        articles = []
        for question_index, docs in enumerate(list_docs):
            paragraphs = []
            for article_id, article in enumerate(docs):
                paragraph = {
                    'context': self.preprocessor.preprocess(article) if self.preprocessor is not None else article,
                    'qas': [{
                        'question': self.preprocessor.preprocess(
                            questions[question_index]) if self.preprocessor is not None else questions[question_index],
                        'id': "{qid}_{aid}".format(qid=question_index, aid=article_id),
                        'answers': [{
                            'text': "",
                            'answer_start': 0
                        }]
                    }]
                }
                paragraphs.append(paragraph)
            article = {
                'title': "prediction_{qid}".format(qid=question_index),
                'paragraphs': paragraphs
            }
            articles.append(article)
        return articles

    def build_quest_json(self, quest, docs):
        articles = []
        paragraphs = []
        id_i = 0
        for doc in docs:
            paragraph_context = doc
            qas = []
            id = str(id_i)
            ques = quest
            ans = ""
            answer_start = 0
            answer = {
                'text': ans,
                'answer_start': answer_start
            }
            question = {
                'question': ques,
                'id': id,
                'answers': [answer]
            }
            qas.append(question)
            paragraph = {
                'context': paragraph_context,
                'qas': qas
            }
            paragraphs.append(paragraph)
            id_i += 1
        article = {
            'title': "prediction",
            'paragraphs': paragraphs
        }
        articles.append(article)
        return articles

    def build_quest_json_araElectra(self, quest, docs):
        paragraphs = []
        id_i = 0
        for doc in docs:
            paragraph_context = doc
            qas = []
            id = str(id_i)
            ques = quest
            question = {
                'question': ques,
                'id': 'q_' + id
            }
            qas.append(question)
            paragraph = {
                'qas': qas,
                'context': paragraph_context
            }
            paragraphs.append(paragraph)
            id_i += 1
        return {"data": [{"paragraphs": paragraphs}]}

    def get_predictions_all(self, predictions_raw):
        answers_text = []
        answers_scores = []
        for key in predictions_raw:
            question_id = int(key[0:key.find("_")])
            article_id = int(key[key.find("_") + 1:])
            while len(answers_text) <= question_id:
                answers_text.append([])
                answers_scores.append([])
            # pick the first as the highest, better to pick all
            for j in range(0, min(1, len(predictions_raw))):
                pred = predictions_raw[key][j]
                pred_score = pred['start_logit'] + pred['end_logit']
                pred_answer = pred['text']
                while len(answers_text[question_id]) <= article_id:
                    answers_text[question_id].append("")
                    answers_scores[question_id].append(0)
                answers_text[question_id][article_id] = self.preprocessor.unpreprocess(pred_answer) \
                    if self.preprocessor is not None else pred_answer
                answers_scores[question_id][article_id] = pred_score
        return answers_text, answers_scores

    def get_predictions(self, predictions_raw):
        answers_text = []
        answers_scores = []
        for i in range(0, len(predictions_raw)):
            doc_ques_id = str(i)
            # pick the first as the highest, better to pick all
            for j in range(0, min(1, len(predictions_raw))):
                pred = predictions_raw[doc_ques_id][j]
                pred_score = pred['start_logit'] + pred['end_logit']
                pred_answer = pred['text']
                answers_text.append(pred_answer)
                answers_scores.append(pred_score)
        return answers_text, answers_scores

    def electra_agreggate(self, answers_text, answers_scores, docs_scores):
        pred = []
        ans_indx = np.argsort(answers_scores)[::-1]
        pred.append(answers_text[ans_indx[0]])
        pred.append(answers_text[ans_indx[1]])
        for i in range(3):
            pred.append(answers_text[i])
        return pred

    def bert_agreggate(self, answers_text, answers_scores, docs_scores):
        ans_scores = np.asarray(answers_scores)
        doc_scores = np.asarray(docs_scores)
        final_scores = (1 - self.beta) * softmax(ans_scores) + self.beta * softmax(doc_scores)
        ans_indx = np.argsort(final_scores)[::-1]
        pred = []
        for k in range(0, min(5, len(ans_indx))):
            pred.append(answers_text[ans_indx[k]])
        return pred

    def build_quest_json_full_file(self, questions, list_docs):
        articles = []
        for question_index, docs in enumerate(list_docs):
            paragraphs = []
            for article_id, article in enumerate(docs):
                paragraph = {
                    'context': self.preprocessor.preprocess(article) if self.preprocessor is not None else article,
                    'qas': [{
                        'question': self.preprocessor.preprocess(
                            questions[question_index]) if self.preprocessor is not None else questions[question_index],
                        'id': "{qid}_{aid}".format(qid=question_index, aid=article_id),
                        'answers': [{
                            'text': "",
                            'answer_start': 0
                        }]
                    }]
                }
                paragraphs.append(paragraph)
            article = {
                'title': "prediction_{qid}".format(qid=question_index),
                'paragraphs': paragraphs
            }
            articles.append(article)
        return {"data": articles, "version": "1.1"}

    def dump_new_dataset(self, args, dataset, dest):
        ground_truth = []
        questions = []
        articles = []
        articles_scores = []
        print("Retrieving Questions!")
        for article in dataset:
            for paragraph in article['paragraphs']:
                for qa in paragraph['qas']:
                    questions.append(qa['question'])
                    ground_truth.append(qa['answers'][0]['text'])
        if args.retCache == 't': self.load_retriever_cache()
        for count, question in enumerate(questions):
            print("Retrieving documents for question number {}".format(count))
            if args.retCache == 't':
                docs, doc_scores = self.get_topk_docs_scores_cache(question)
            else:
                docs, doc_scores = self.retriever.get_topk_docs_scores(question)
            articles.append(docs)
            articles_scores.append(doc_scores)
        print("Finished Retrieving documents")
        if args.retCache == 't': self.dumb_retirever_cache()
        new_dataset = self.build_quest_json_full_file(questions, articles)
        with open(dest, 'w') as f:
            json.dump(new_dataset, f)

    def test_electra(self, args, dataset, dest, model):
        ground_truth = []
        questions = []
        articles = []
        articles_scores = []
        print("Retrieving Questions!")
        for article in dataset:
            for paragraph in article['paragraphs']:
                for qa in paragraph['qas']:
                    questions.append(qa['question'])
                    ground_truth.append(qa['answers'][0]['text'])
        if args.retCache == 't': self.load_retriever_cache()
        for count, question in enumerate(questions):
            print("Retrieving documents for question number {}".format(count))
            if args.retCache == 't':
                docs, doc_scores = self.get_topk_docs_scores_cache(question)
            else:
                docs, doc_scores = self.retriever.get_topk_docs_scores(question)
            articles.append(docs)
            articles_scores.append(doc_scores)
        print("Finished Retrieving documents")
        if args.retCache == 't': self.dumb_retirever_cache()
        new_dataset = self.build_quest_json_full_file(questions, articles)
        with open(dest, 'w') as f:
            json.dump(new_dataset, f)
        print("Answering")
        answers_raw = run_evaluation(model)
        print("Aggregating")
        answers, answers_scores = self.get_predictions_all(answers_raw)
        print(str(args))
        print("Total Questions {}".format(len(articles)))
        pprint.pprint(self.aggregate_bert_all(answers, answers_scores, articles_scores, ground_truth))
        pprint.pprint(self.aggregate_electra_all(answers, answers_scores, articles_scores, ground_truth))

    def aggregate_bert_all(self, answers, answers_scores, articles_scores, ground_truth):
        question_no = len(articles_scores)
        exact_match_1 = 0
        exact_match_3 = 0
        exact_match_5 = 0
        f1_1 = 0
        f1_3 = 0
        f1_5 = 0
        for j in range(len(articles_scores)):
            exact_match_max_1 = 0
            f1_max_1 = 0
            f1_max_3 = 0
            exact_match_max_3 = 0
            f1_max_5 = 0
            exact_match_max_5 = 0
            predictions = self.bert_agreggate(answers[j], answers_scores[j], articles_scores[j])
            for i in range(len(predictions)):
                if i < 1:
                    exact_match_max_1 = max(exact_match_max_1, exact_match_score(predictions[i], ground_truth[j]))
                    f1_max_1 = max(f1_max_1, f1_score(predictions[i], ground_truth[j]))
                if i < 3:
                    exact_match_max_3 = max(exact_match_max_3, exact_match_score(predictions[i], ground_truth[j]))
                    f1_max_3 = max(f1_max_3, f1_score(predictions[i], ground_truth[j]))
                if i < 5:
                    exact_match_max_5 = max(exact_match_max_5, exact_match_score(predictions[i], ground_truth[j]))
                    f1_max_5 = max(f1_max_5, f1_score(predictions[i], ground_truth[j]))

            exact_match_1 += exact_match_max_1
            f1_1 += f1_max_1
            exact_match_3 += exact_match_max_3
            f1_3 += f1_max_3
            exact_match_5 += exact_match_max_5
            f1_5 += f1_max_5
        return {"Aggregate": "BERT Old Aggregate",
                "EM Top 1": str(100.00 * exact_match_1 / question_no),
                "EM Top 3": str(100.00 * exact_match_3 / question_no),
                "EM Top 5": str(100.00 * exact_match_5 / question_no),
                "F1 Top 1": str(100.00 * f1_1 / question_no),
                "F1 Top 3": str(100.00 * f1_3 / question_no),
                "F1 Top 5": str(100.00 * f1_5 / question_no)}

    def aggregate_electra_all(self, answers, answers_scores, articles_scores, ground_truth):
        question_no = len(articles_scores)
        exact_match_1 = 0
        exact_match_3 = 0
        exact_match_5 = 0
        f1_1 = 0
        f1_3 = 0
        f1_5 = 0
        for j in range(len(articles_scores)):
            exact_match_max_1 = 0
            f1_max_1 = 0
            f1_max_3 = 0
            exact_match_max_3 = 0
            f1_max_5 = 0
            exact_match_max_5 = 0
            predictions = self.electra_agreggate(answers[j], answers_scores[j], articles_scores[j])
            for i in range(len(predictions)):
                if i < 1:
                    exact_match_max_1 = max(exact_match_max_1, exact_match_score(predictions[i], ground_truth[j]))
                    f1_max_1 = max(f1_max_1, f1_score(predictions[i], ground_truth[j]))
                if i < 3:
                    exact_match_max_3 = max(exact_match_max_3, exact_match_score(predictions[i], ground_truth[j]))
                    f1_max_3 = max(f1_max_3, f1_score(predictions[i], ground_truth[j]))
                if i < 5:
                    exact_match_max_5 = max(exact_match_max_5, exact_match_score(predictions[i], ground_truth[j]))
                    f1_max_5 = max(f1_max_5, f1_score(predictions[i], ground_truth[j]))

            exact_match_1 += exact_match_max_1
            f1_1 += f1_max_1
            exact_match_3 += exact_match_max_3
            f1_3 += f1_max_3
            exact_match_5 += exact_match_max_5
            f1_5 += f1_max_5
        return {"Aggregate": "Electra New Aggregate",
                "EM Top 1": str(100.00 * exact_match_1 / question_no),
                "EM Top 3": str(100.00 * exact_match_3 / question_no),
                "EM Top 5": str(100.00 * exact_match_5 / question_no),
                "F1 Top 1": str(100.00 * f1_1 / question_no),
                "F1 Top 3": str(100.00 * f1_3 / question_no),
                "F1 Top 5": str(100.00 * f1_5 / question_no)}

    def ask_all(self, dataset, args):
        ground_truth = []
        questions = []
        articles = []
        articles_scores = []
        print("Retrieving Questions!")
        for article in dataset:
            all_questions_per_article = []
            for paragraph in article['paragraphs']:
                if args.ret_per_article == 'single':
                    for qa in paragraph['qas']:
                        questions.append(qa['question'])
                        ground_truth.append(qa['answers'][0]['text'])
                elif args.ret_per_article == 'paragraph':
                    all_questions_per_paragraph = []
                    for qa in paragraph['qas']:
                        all_questions_per_paragraph.append(qa['question'])
                        ground_truth.append(qa['answers'][0]['text'])
                    for qa in all_questions_per_paragraph:
                        questions.append((qa, " ".join(all_questions_per_paragraph).replace("؟", "").strip()))
                elif args.ret_per_article == 'article':
                    for qa in paragraph['qas']:
                        all_questions_per_article.append(qa['question'])
                        ground_truth.append(qa['answers'][0]['text'])
            if args.ret_per_article == 'article':
                for qa in all_questions_per_article:
                    questions.append((qa, " ".join(all_questions_per_article).replace("؟", "").strip()))

        if args.retCache == 't': self.retriever_cache.load_retriever_cache()
        for count, question in enumerate(questions):
            cur_question = question[1] if args.ret_per_article == 'paragraph' or args.ret_per_article == 'article' else question
            print("Retrieving documents for question number {}".format(count))
            print(cur_question)
            if args.retCache == 't':
                docs, doc_scores = self.retriever_cache.get_topk_docs_scores_cache(cur_question)
            else:
                docs, doc_scores = self.retriever.get_topk_docs_scores(cur_question)
            articles.append(docs)
            articles_scores.append(doc_scores)
            assert len(docs) == len(doc_scores)
        print("Finished Retrieving documents")
        if args.retCache == 't': self.retriever_cache.dumb_retirever_cache()
        if args.ret_per_article == 'single':
            new_dataset = self.build_quest_json_full(questions, articles)
        else:
            new_dataset = self.build_quest_json_full([qa[0] for qa in questions], articles)

        print("Answering")
        answers_list = self.reader.predict_batch(new_dataset)
        print("Aggregating")
        answers, answers_scores = self.get_predictions_all(answers_list)
        print(str(args))
        print("Total Questions {}".format(len(articles)))
        pprint.pprint(self.aggregate_bert_all(answers, answers_scores, articles_scores, ground_truth))
        pprint.pprint(self.aggregate_electra_all(answers, answers_scores, articles_scores, ground_truth))

    def ask(self, quest):
        docs, doc_scores = self.retriever.get_topk_docs_scores(quest)
        print("got documents")
        dataset = self.build_quest_json(quest, docs)
        print("built documents json")
        nbest = self.reader.predict_batch(dataset)
        print("got predictions from BERT")
        answers, answers_scores = self.get_predictions(nbest)
        prediction = self.bert_agreggate(answers, answers_scores, doc_scores)
        return prediction

    def ask_araelectra1(self, quest):
        docs, doc_scores = self.retriever.get_topk_docs_scores(quest)
        print("got documents")
        dataset = self.build_quest_json_araElectra(docs)
        print("built documents json")
        total_result = []
        for context in dataset:
            context = self.reader.preprocess(context)
            if len(context) < 2:
                continue
            total_result.append(self.reader.answerQuestion(question=quest, context=context))
        result = sorted(total_result, key=lambda object1: object1["score"], reverse=True)
        answers = []
        for i in range(0, 5):
            answers.append(result[i]["answer"])
        return answers

    def ask_araelectra(self, quest):
        print("Fetching documents")
        docs, doc_scores = self.retriever.get_topk_docs_scores(quest)
        dataset = self.build_quest_json_araElectra(quest, docs)
        print("Built Json document")
        total_result = self.reader.get_answer(dataset)
        print("Got Results")
        answers = []
        answer_scores = []
        for result in total_result:
            answers.append(result[0]['text'])
            answer_scores.append(result[0]['start_logit'] * result[0]['end_logit'])
        prediction = self.electra_agreggate(answers, answer_scores, doc_scores)
        return prediction


    def get_articles(self, quest):
        docs, doc_scores = self.retriever.get_topk_docs_scores(quest)
        return docs, doc_scores

    def ask_articles(self, quest, docs, doc_scores):
        dataset = self.build_quest_json(quest, docs)
        print("built documents json")
        nbest = self.reader.predict_batch(dataset)
        print("got predictions from BERT")
        answers, answers_scores = self.get_predictions(nbest)
        prediction = self.bert_agreggate(answers, answers_scores, doc_scores)
        return prediction
