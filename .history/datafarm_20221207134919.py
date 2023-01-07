from convokit import Corpus, TextParser, PolitenessStrategies, Coordination

import os
import pandas as pd

class DataFrame:
    ps_parser = TextParser(verbosity=1000)
    ps = PolitenessStrategies() # add verbosity for loading?
    coord = Coordination()

    parent_dir = "convokitdatasets"

    def __init__(self, corpus_input):
        corpus = self.set_corpus(corpus_input)
        self.corpus = self.pre_process(corpus)


    def set_corpus(self, corpus_input):
        """
        Finds corpus folder in parent directory and sets it

        :param corpus_input: corpus folder name
        """ 
        cwd = os.getcwd()
        path = self.find_path(corpus_input) 
        corpus = Corpus(filename=os.path.join(cwd, path))
        corpus = self.pre_process(corpus)

        print('Corpus set:', corpus)

        return corpus
        

    def find_path(self, target_file):
        """
        Finds path to file in parent directory

        :param target_file: file to identify the path of
        :return: file path
        """ 
        for file_name in os.listdir(self.parent_dir):
            file_path = os.path.join(self.parent_dir, file_name)
            if target_file in file_path:
                return file_path

            
    def pre_process(self, corpus):
        """
        Pre-processes utterances in corpus

        :param corpus: processed corpus
        """ 
        # Politeness Strategies
        corpus = self.ps_parser.transform(corpus)
        corpus = self.ps.transform(corpus, markers=True) 

        # Coordination
        self.coord.fit_transform(corpus)
        self.coord.summarize(corpus)

        return corpus

        
    def create_grp_df(self, corpus):
        """
        Create dataframe containing feature scores for every group

        :param corpus: the corpus object
        :return: dataframe 
        """ 
        grp_df = self.extract_grp_ps_feats(corpus)
        grp_df = pd.concat([grp_df, self.extract_grp_coord_feats(corpus, self.spkr_df)], axis=1)

        print(grp_df)
        return grp_df


    def create_spkr_df(self, corpus):
        """
        Create dataframe containing feature scores for every speaker

        :param corpus: the corpus object
        :return: dataframe 
        """ 
        spkr_df = extract_spkr_ps_feats(corpus)
        spkr_df = pd.concat([spkr_df, extract_spkr_coord_feats(corpus)], axis=1)

        print(spkr_df)
        spkr_df.to_csv('coord-feats.csv')
        return spkr_df


    def extract_grp_ps_feats(corpus):
        """
        Calculate feature politeness scores for all groups

        :param corpus: the corpus object
        :return: dataframe of feature politeness scores for every group
        """ 
        df = pd.DataFrame()
        query = lambda q: q.get_conversation() == conversation
        group_list = []

        for conversation in corpus.iter_conversations():
            group_list.append(conversation.id)
            politeness_data = ps.summarize(corpus, query)
            df = pd.concat([df, politeness_data.to_frame().T], ignore_index=True)
        
        df.index = group_list

        return df


    def extract_grp_coord_feats(corpus, spkr_df):
        """
        Calculate feature coordination scores for all groups

        :param corpus: the corpus object
        :param corpus: a dataframe containing individual speaker coordination scores
        :return: dataframe of feature coordination scores for every group
        """ 
        coord_feats_cols = ['article', 'auxverb', 'conj', 'adverb', 'ppron', 'ipron', 'preps', 'quant']
        df = pd.DataFrame(columns=coord_feats_cols)
        group_list = []

        for conversation in corpus.iter_conversations():
            group_list.append(conversation.id)
            feat_scores = []

            for feat in coord_feats_cols:
                coord_score = 0
                coord_count = 0

                for index in spkr_df.index:
                    if index in conversation.get_speaker_ids():
                        coord_score += spkr_df.loc[index][feat]
                        coord_count += 1

                total_coord_score = average(coord_score, coord_count)
                feat_scores.append(total_coord_score)

            a_series = pd.Series(feat_scores, index=df.columns)
            df = pd.concat([df, a_series.to_frame().T], ignore_index=True)

        df.index = group_list

        print(df)
        return df


    def extract_spkr_ps_feats(corpus):
        """
        Calculate feature politeness scores for all speakers

        :param corpus: the corpus object
        :return: dataframe of feature politeness scores for every speaker
        """ 
        df = pd.DataFrame()
        query = lambda q: q.get_speaker() == speaker
        speaker_list = []

        for speaker in corpus.iter_speakers():
            speaker_list.append(speaker.id)
            politeness_data = ps.summarize(corpus, query)
            df = pd.concat([df, politeness_data.to_frame().T], ignore_index=True)

        df.index = speaker_list

        return df


    def extract_spkr_coord_feats(corpus):
        """
        Calculate feature coordination scores for all speakers

        :param corpus: the corpus object
        :return: dataframe of feature coordination scores for every speaker
        """ 
        coord_feats_cols = ['article', 'auxverb', 'conj', 'adverb', 'ppron', 'ipron', 'preps', 'quant']
        speaker_list = []
        df = pd.DataFrame(columns=coord_feats_cols) 
        
        for speaker in corpus.iter_speakers():
            feat_scores = []
            speaker_list.append(speaker.id)

            for feat in coord_feats_cols:
                coord_score = calc_feat_avg(speaker, feat)  
                feat_scores.append(coord_score)

            a_series = pd.Series(feat_scores, index=df.columns)
            df = pd.concat([df, a_series.to_frame().T], ignore_index=True)

        df.index = speaker_list

        return df


    def calc_feat_avg(speaker, feat):
        """
        Calculate the value of a particular feature coordination score 

        :param speaker: the speaker object
        :param feat: the name of the feature
        :return: average coordination score
        """ 
        coord_score = 0
        coord_count = 0

        for value in speaker.meta['coord']:
            if feat in speaker.meta['coord'][str(value)]:
                coord_score += speaker.meta['coord'][str(value)][feat]
                coord_count += 1

        coord_score = average(coord_score, coord_count)

        return coord_score


    def average(score, count):
        """
        Calculate the average of a score

        :param score: the sum of a score to calculate the average of
        :param count: the frequency of occurrence of the score
        :return: the average 
        """ 
        if count != 0:
            return round(score / count, 2)
        else:
            return 0