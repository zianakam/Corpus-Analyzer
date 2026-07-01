from convokit import Corpus, TextParser, PolitenessStrategies, Coordination
from convokit.text_processing import TextProcessor
from convokit.convokitPipeline import ConvokitPipeline
from datetime import datetime

import pandas as pd
import re
import contractions
import numpy as np
import datetime

class DataFarm():
    feature_list = ['feature_politeness_==Please==', 'feature_politeness_==Please_start==', 
                    'feature_politeness_==HASHEDGE==', 'feature_politeness_==Indirect_(btw)==', 
                    'feature_politeness_==Hedges==', 'feature_politeness_==Factuality==', 
                    'feature_politeness_==Deference==', 'feature_politeness_==Gratitude==', 
                    'feature_politeness_==Apologizing==', 'feature_politeness_==1st_person_pl.==', 
                    'feature_politeness_==1st_person==', 'feature_politeness_==1st_person_start==', 
                    'feature_politeness_==2nd_person==', 'feature_politeness_==2nd_person_start==', 
                    'feature_politeness_==Indirect_(greeting)==', 'feature_politeness_==Direct_question==', 
                    'feature_politeness_==Direct_start==', 'feature_politeness_==HASPOSITIVE==', 
                    'feature_politeness_==HASNEGATIVE==', 'feature_politeness_==SUBJUNCTIVE==', 
                    'feature_politeness_==INDICATIVE==', 'meta.age_of_acquisition', 
                    'meta.concreteness', 'meta.familiarity', 'meta.imageability']
    ps_parser = TextParser(verbosity=1000)
    ps = PolitenessStrategies()     
    coord = Coordination()

    psycho_df = pd.read_csv("assets/psycholing-word-scores.csv", index_col="WORD")


    def __init__(self, unzipped_path):
        """
        :param unzipped_path: Path to uploaded Corpus
        :return: Set and pre-processed Corpus object
        """
        self.corpus = Corpus(filename=unzipped_path)

    def pre_process(self):
        """
        Pre-processes utterances in Corpus object
        """
        # Psycholinguistics
        clean_prep_compute = ConvokitPipeline([
            ('clean', TextProcessor(self.clean_text, output_field='clean_text')),
            ('prep', TextProcessor(proc_fn=self.prep_text, output_field='psycho_text')),
            ('parse', TextProcessor(proc_fn=self.psycho_utt_computation, input_field='psycho_text', 
                output_field=['age_of_acquisition', 'concreteness', 'familiarity', 'imageability']))
            ])
        self.corpus = clean_prep_compute.transform(self.corpus)    

        # Politeness Strategies
        self.corpus = self.ps_parser.transform(self.corpus)
        self.corpus = self.ps.transform(self.corpus, markers=True) 

        # Coordination
        self.coord.fit_transform(self.corpus)


    def clean_text(self, text):
        """
        Removes double quotation marks from text

        :param text: The text to process
        :return: The processed text
        """
        # Affects feature extraction for non-prepped text
        text = str(text).strip('\"')

        return text


    def prep_text(self, text):
        """
        Removes punctuation, expands contractions, and separates text 
        into a series of words for extraction purposes

        :param text: The text to process
        :return: The processed text
        """
        # Use contractions.fix to expand the shortened words
        text = contractions.fix(text)

        # Remove all punctuation except apostrophes
        text = re.sub(r"[^\w\d'\s]+", '', text)

        # Split str into lower-case list of words
        text = text.lower().split()

        return text
    

    def psycho_utt_computation(self, text):
        """
        Calculates per-utterance scores of psycholinguistic features

        :param text: The utterance to process
        :return: The relevant scores
        """
        # Find words in text that have a psycholinguistic score
        found_words = []

        for word in text:
            if word in self.psycho_df.index:
                found_words.append(word)    

        # Compute psycholinguistic score
        if len(found_words) == 0:
            return np.zeros(4, dtype=float)
        
        # Grab sum and count of each feature score
        scores = self.psycho_df.loc[found_words].sum()
        counts = self.psycho_df.loc[found_words].ne(0).sum() 

        # Replace 0 counts with 1 to prevent division by 0 error
        average = scores.values / counts.replace(0, 1).values
        average = average.round(2)

        return average
    

    def create_speaker_dfs(self):
        """
        Creates Dataframe of feature scores for speakers overall and speakers 
        over time.

        :return: Dataframe of speaker scores
        :return: Dataframe of speaker scores over time
        :return: Dataframe of speaker scores including built-in Corpus metadata
        """
        speaker_df = pd.DataFrame()
        speaker_time_df = pd.DataFrame()
        speaker_meta_df = pd.DataFrame()

        for speaker in self.corpus.iter_speakers():
            utt_df = speaker.get_utterances_dataframe()
        
            individ_scores = self.calc_speaker_scores(speaker, utt_df)
            speaker_df = pd.concat([speaker_df, individ_scores], axis=0)

            time_scores = self.calc_time_scores(speaker, utt_df)
            speaker_time_df = pd.concat([speaker_time_df, time_scores], axis=0)

            metadata = self.get_metadata(speaker, 'speaker')
            speaker_meta_df = pd.concat([speaker_meta_df, metadata], axis=0)


        speaker_meta_df.reset_index(drop=True, inplace=True)
        speaker_meta_df.insert(0, 'speaker_id', speaker_meta_df.pop('speaker_id'))

        speaker_df.reset_index(drop=True, inplace=True)
        speaker_df = speaker_df.fillna(0) 

        if 'time' in speaker_time_df.columns:
            speaker_time_df.reset_index(drop=True, inplace=True)
        else:
            speaker_time_df.reset_index(drop=False, inplace=True)

        # Remove extra apostrophes from last columns
        psycho_cols = ['meta.age_of_acquisition', 'meta.concreteness', 'meta.familiarity', 'meta.imageability']
        speaker_time_df[psycho_cols] = speaker_time_df[psycho_cols].astype(str).replace("'", "", regex=True) 
        # Convert psycho columns to float type
        speaker_time_df[psycho_cols] = speaker_time_df[psycho_cols].astype(float).round(2)
        # Fill null values -- excluding Time & ID column
        speaker_time_df[self.feature_list] = speaker_time_df[self.feature_list].astype(float).fillna(0.0)

        return speaker_df, speaker_time_df, speaker_meta_df

    
    def calc_speaker_scores(self, speaker, utt_df):
        """
        Calculates feature scores for a speaker

        :param speaker: A ConvoKit speaker object
        :param utt_df: A Dataframe of utterances
        :return: Linguistic feature scores
        """
        coord_scores = pd.Series([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 
                                 index=["article", "auxverb", "conj", "adverb", 
                                        "ppron", "ipron", "preps", "quant"],
                                dtype='float')

        if "coord" in speaker.meta:
            # Grab average of coordination scores from conversing with different participants
            coord_scores = pd.DataFrame(speaker.meta["coord"]).T
            coord_scores = coord_scores.mean(skipna=True).round(2)

        # Split politeness strategies features into their own separate columns
        politeness_strategies = pd.DataFrame(utt_df['meta.politeness_strategies'].tolist(), index=utt_df.index)
        utt_df = pd.concat([utt_df.drop("meta.politeness_strategies", axis=1), 
                                politeness_strategies], axis=1)
        
        # Calculate average feature scores per section
        ps_psycho_scores = utt_df[self.feature_list].astype(float)
        ps_psycho_scores = ps_psycho_scores.mean(skipna=True).round(2)

        # Append results to speaker df
        scores = pd.concat([ps_psycho_scores.to_frame().T, coord_scores.to_frame().T], axis=1)
        scores.insert(loc=0, column='speaker_id', value=speaker.id)

        return scores
    

    def calc_time_scores(self, speaker, utt_df):
        """
        Calculates feature scores in different subsections of the conversation

        :param speaker: A ConvoKit speaker object
        :param utt_df: A Dataframe of utterances
        :return: Linguistic feature scores
        """
        scores = pd.DataFrame()

        if utt_df["timestamp"].isnull().all():
            # Return DataFrame with 0 values for all feature scores
            scores = pd.DataFrame(0, index=np.arange(5), columns=self.feature_list)
            scores.insert(loc=0, column='speaker_id', value=utt_df.index[0])
            scores.insert(loc=1, column='time', value=np.arange(1, 6))
        else: 
            # Fill missing values
            utt_df["timestamp"] = utt_df["timestamp"].fillna("0")
            vectorized_format = np.vectorize(self.format_timestamp)
            utt_df["timestamp"] = vectorized_format(utt_df["timestamp"])

            # Split conversation into 5 sections according to timestamp
            interval = (utt_df["timestamp"].max() - utt_df["timestamp"].min()) / 5

            # Sort data into those 5 sections 
            bins = [utt_df["timestamp"].min()] + [utt_df["timestamp"].min() + i * interval for i in range(1, 6)]
            utt_df["time"] = pd.cut(utt_df["timestamp"], bins=bins, labels=[1, 2, 3, 4, 5], include_lowest=True)

            # Split politeness strategies features into their own separate columns
            politeness_strategies = pd.DataFrame(utt_df['meta.politeness_strategies'].tolist(), index=utt_df.index)
            utt_df = pd.concat([utt_df.drop("meta.politeness_strategies", axis=1), 
                                    politeness_strategies], axis=1)
            
            scores = utt_df.groupby("time", observed=False)[self.feature_list]
            scores = scores.mean().round(2)
            scores.insert(loc=0, column='speaker_id', value=speaker.id)
        
        return scores
    
    
    def get_metadata(self, corpus_object, type):
        """
        Extracts metadata from a corpus object

        :param corpus_object: A ConvoKit speaker or conversation object
        :param type: The type of object ('speaker' or 'conversation')
        :return: A DataFrame of metadata
        """
        metadata = pd.DataFrame(corpus_object.meta, index=[0])

        if 'coord' in metadata.columns:
            metadata.drop(['coord'], inplace=True, axis=1)

        metadata = metadata.add_prefix('meta.')

        metadata.columns = metadata.columns.str.lower()
        metadata.columns = metadata.columns.str.replace(' ', '_')

        if type == 'speaker':
            metadata['speaker_id'] = corpus_object.id
        elif type == 'conversation':
            metadata['group_id'] = corpus_object.id

        metadata = metadata[:1].reset_index(drop=True)

        return metadata


    def format_timestamp(self, timestamp):
        """
        Checks if timestamp value matches the designated format, else 
        formats it and returns

        :param timestamp: A timestamp
        :return: Formatted timestamp
        """
        pattern = '{:02d}:{:02d}:{:04.01f}'
        match = re.match(pattern, timestamp)

        if match:
            return timestamp
        else: 
            try:
                hours = 0
                minutes = 0
                seconds = 0

                # Remove extra special characters
                timestamp = timestamp.strip(":\"\'")

                if timestamp.count(":") == 2:
                    hours, minutes, seconds = timestamp.split(":")
                elif timestamp.count(":") == 1:
                    minutes, seconds = timestamp.split(":")
                else:
                    seconds = timestamp

                timestamp = datetime.timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds))

                return timestamp
            
            except ValueError:
                print("Unexpected timestamp format: ", timestamp)
                return datetime.timedelta(hours=0, minutes=0, seconds=0.0)
        

    def create_group_dfs(self, speaker_df, speaker_time_df):
        """
        Creates a Dataframe of feature scores for group conversations overall & over time.

        :param speaker_df: Dataframe of speaker feature scores
        :param speaker_time_df: Dataframe of speaker feature scores over time
        :return: Dataframe of group feature scores
        :return: Dataframe of group feature scores over time
        :return: Dataframe of group metadata information
        """
        group_df = pd.DataFrame()
        group_time_df = pd.DataFrame()
        group_meta_df = pd.DataFrame()

        for conversation in self.corpus.iter_conversations():
            speakers_list = conversation.get_speaker_ids()
        
            group_scores = self.calc_group_scores(speaker_df, speakers_list, conversation)
            group_df = pd.concat([group_df, group_scores], axis=0)

            group_time_scores = self.calc_group_time_scores(speaker_time_df, speakers_list, conversation)
            group_time_df = pd.concat([group_time_df, group_time_scores], axis=0)

            metadata = self.get_metadata(conversation, 'conversation')
            group_meta_df = pd.concat([group_meta_df, metadata], axis=0)

        
        group_meta_df.reset_index(drop=True, inplace=True)
        group_meta_df.insert(0, 'group_id', group_meta_df.pop('group_id'))
        
        if 'time' in group_time_df.columns:
            group_time_df.reset_index(drop=True, inplace=True)
        else:
            group_time_df.reset_index(drop=False, inplace=True)
        
        return group_df, group_time_df, group_meta_df
    

    def calc_group_scores(self, speaker_df, speakers_list, conversation):
        """
        Calculates feature scores for a group

        :param speaker_df: Dataframe of speaker feature scores
        :param speakers_list: List of speaker ids in the conversation
        :param conversation: The "group" (conversation) Convokit object 
        :return: Linguistic feature scores
        """
        # Filter speaker df by conversation
        filter = speaker_df["speaker_id"].isin(speakers_list)
        filtered_df = speaker_df[filter]

        # Remove speaker ID column
        filtered_df = filtered_df.drop("speaker_id", axis=1)

        # Grab group average 
        scores = filtered_df.mean(skipna=True).round(2)
        scores = scores.to_frame().T
        scores.insert(loc=0, column='group_id', value=conversation.id)
        
        return scores


    def calc_group_time_scores(self, speaker_df, speakers_list, conversation):
        """
        Calculates feature scores for a group over time

        :param speaker_df: Dataframe of speaker feature scores
        :param speakers_list: List of speaker ids in the conversation
        :param conversation: The "group" (conversation) Convokit object 
        :return: Linguistic feature scores
        """
        # Grab just the feature scores
        speaker_features = speaker_df.drop(['time', 'speaker_id'], inplace=False, axis=1)
        # If all feature scores are empty
        if (speaker_features == 0).all(axis=None):
            # Return DataFrame with 0 values for all feature scores
            scores = pd.DataFrame(0, index=np.arange(5), columns=self.feature_list)
            scores.insert(loc=0, column='group_id', value=conversation.id)
            scores.insert(loc=1, column='time', value=np.arange(1, 6))

            return scores

        # Filter speaker df by conversation
        filter = speaker_df["speaker_id"].isin(speakers_list)
        filtered_df = speaker_df[filter]

        # Remove speaker ID column
        filtered_df = filtered_df.drop("speaker_id", axis=1)

        # Grab group average at each time interval
        scores = filtered_df.groupby("time", observed=False).mean()
        scores = scores.astype(float).round(2)
        scores.insert(loc=0, column='group_id', value=conversation.id)

        return scores
    

    def format_utt_df(self, utt_df):
        """
        Fix the formatting of the generated utterance Dataframe

        :param utt_df: A Dataframe of utterances
        :return: A Dataframe of utterances
        """
        # Explode dictionary values into individual columns
        ps_feats = pd.DataFrame(utt_df['meta.politeness_strategies'].tolist(), index=utt_df.index)
        ps_markers = pd.DataFrame(utt_df['meta.politeness_markers'].tolist(), index=utt_df.index)

        # Re-combine into original df, drop irrelevant columns  
        utt_df = pd.concat([utt_df.drop(['meta.politeness_strategies', 'meta.politeness_markers',
                                         'meta.parsed', 'meta.liwc-categories', 'meta.psycho_text', 'vectors'], axis=1), 
                                ps_feats, ps_markers], axis=1)

        # Format timestamp values
        utt_df["timestamp"] = utt_df["timestamp"].fillna("0")
        vectorized_format = np.vectorize(self.format_timestamp)
        utt_df["timestamp"] = vectorized_format(utt_df["timestamp"])

        utt_df = utt_df.convert_dtypes()
        
        return utt_df
    

    def clean_columns(self, df):
        """
        Tidy the Dataframe columns

        :param df: A Dataframe 
        :return: A Dataframe
        """
        # Remove extra values  
        df.columns = df.columns.str.replace(r'==|^feature_politeness_==|^meta.', '', regex=True) 
        # Add '_' to separate column names 
        df.columns = df.columns.str.replace(r'(HAS)', r'\1_', regex=True) 
        # Lower column names
        df.columns = df.columns.str.lower() 
        df.rename(columns={'auxverb': 'auxiliary_verb', 'conj': 'conjunction', 'ppron': 'personal_pronoun', 
                           'ipron': 'impersonal_pronoun', 'preps': 'preposition', 'quant': 'quantifier', 
                           '1st_person_pl.': '1st_person_plural'}, inplace=True)
        
        return df
    