#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#

import csv
import jinja2 as j2
import json

from copy import deepcopy, copy
from typing import NamedTuple

import common.qualtrics as qs
import common.utilities as utils


DEFAULT_SURVEY = "SV_9HcwQ4EhfsTlnJr"

logger = utils.get_logger()

env = j2.Environment(
    # loader=j2.PackageLoader('common', 'sql_templates'),
    loader=j2.FileSystemLoader('.'),
)

like_rephrasing_question_dict = {
    "QuestionText": None,
    "DataExportTag": None,  # "Q1"
    "QuestionType": "MC",
    "Selector": "SAVR",
    "SubSelector": "TX",
    "Configuration": {"QuestionDescriptionOption": "UseText", "Autoscale": {"YScale": {"Name": "yesNo", "Type": "likert", "Reverse": False}}},
    # "QuestionDescription": None,  # Ok to leave as None. Was: "Rephrased indicator...",
    "Choices": {"1": {"Display": "yes"}, "2": {"Display": "no"}},
    "ChoiceOrder": ["1", "2"],
    "Validation": {"Settings": {"ForceResponse": "OFF", "ForceResponseType": "ON", "Type": "None"}},
    "Language": [],
    # "NextChoiceId": 3,
    # "NextAnswerId": 1,
    # "QuestionID": None,  # "QID1",  Note: question ID cannot be set via the API
    "DataVisibility": {"Private": False, "Hidden": False},
    # "QuestionText_Unsafe": None,  # Ok to leave as None. Was: "<strong>Rephrased indicator:..."
}

comment_question = {
    'QuestionText': 'Do you have any comments on the rephrased indicator?',
    'DefaultChoices': False,
    'DataExportTag': 'Q100',
    'QuestionType': 'TE',
    'Selector': 'ML',
    'Configuration': {'QuestionDescriptionOption': 'UseText', 'InputWidth': 658, 'InputHeight': 208},
    'QuestionDescription': 'Do you have any comments on the rephrased indicator?',
    'Validation': {'Settings': {'ForceResponse': 'OFF', 'ForceResponseType': 'ON', 'Type': 'None'}},
    'GradingData': [], 'Language': [],
    # 'NextChoiceId': 4,
    # 'NextAnswerId': 1,
    'SearchSource': {'AllowFreeResponse': 'false'},
    'QuestionText_Unsafe': 'Do you have any comments on the rephrased indicator?'
}

indicator_block_template = {
    'Type': 'Standard',
    'Description': None, #'Block 1',
    'ID': None, #'BL_50uVt2AAm2dc097',
    'BlockElements': [{'Type': 'Question', 'QuestionID': None}, {'Type': 'Question', 'QuestionID': None}]
}


precise_indicator_phrasing_question_template = env.get_template('precise_indicator_phrasing_question.j2')


class IndicatorPhrasingQuestion:
    def __init__(self, data_export_tag, original_phrasing, rephrased_indicator, explanatory_terms=None, rationale_for_change=None):
        self.data_export_tag = data_export_tag
        self.original_phrasing = original_phrasing
        self.rephrased_indicator = rephrased_indicator
        self.explanatory_terms = explanatory_terms
        self.rationale_for_change = rationale_for_change
        self.question_text_template = precise_indicator_phrasing_question_template
        self.question_dict = deepcopy(like_rephrasing_question_dict)
        self.block_template = deepcopy(indicator_block_template)

    def rendered_question_text(self):
        return "{original_phrasing}{rephrased_indicator}{explanatory_terms}{rationale_for_change}".format(
            # self.question_text_template.render(
            original_phrasing=self.original_phrasing,
            rephrased_indicator=self.rephrased_indicator,
            explanatory_terms=self.explanatory_terms,
            rationale_for_change=self.rationale_for_change,
        )

    def rendered_question(self):
        question = self.question_dict
        question["QuestionText"] = self.rendered_question_text()
        question["DataExportTag"] = self.data_export_tag
        # logger.debug('rendered_question', extra=question)
        return question

    # def rendered_block(self):
    #     block = self.block_template
    #     block['BlockElements'][0]['QuestionID'] = self.id
    #     return block


class CsvParser:
    def __init__(self, input_filename):
        self.filename = input_filename

    def parse_into_question_list(self):
        """
        Converts csv data into a list of IndicatorPhrasingQuestion objects

        Returns:
            List of IndicatorPhrasingQuestion objects

        """
        null_symbols = ['-']
        optional_columns = ['Explanatory terms ', 'Notes on rationale for rephrasing']
        question_list = list()
        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:

                # transform null_symbols into None for all optional columns
                for column in optional_columns:
                    if row[column].strip() in null_symbols:
                        row[column] = None

                question = IndicatorPhrasingQuestion(
                    data_export_tag=f"Q{row['Indicator #']}",
                    original_phrasing=row['Original phrasing'],
                    rephrased_indicator=row['Rephrased indicator'],
                    explanatory_terms=row['Explanatory terms '],
                    rationale_for_change=row['Notes on rationale for rephrasing'],
                )
                question_list.append(question)
        logger.debug("Question list parsed from csv", extra={
            'question_list': [
                [x.data_export_tag, x.original_phrasing, x.rephrased_indicator, x.explanatory_terms, x.rationale_for_change] for x in question_list
            ]})
        return question_list


class SurveyUpdateManager:
    def __init__(self, questions_dict, survey_id=DEFAULT_SURVEY):
        """
        Args:
            questions_dict: Dictionary of questions indexed by "DataExportTag"
            survey_id:
        """
        self.survey_client = qs.SurveyDefinitionsClient(survey_id)
        self.survey = self.survey_client.get_survey()['result']
        self.new_questions = questions_dict

        self.tag2id_map = dict()
        self.questions_to_update = dict()
        self.questions_to_add = dict()
        self.questions_to_delete = dict()

    def _update_tag2id_map(self, questions):
        """
        We can control the DataExportTag of a question, but not its ID, so we need a mapping between these keys.
        This function updates the map with values from a dictionary of questions.

        Args:
            questions (dict): Dictionary of questions indexed by "QuestionID"

        Returns:
            Updated self.tag2id_map dictionary

        """
        for k, v in questions.items():
            self.tag2id_map[v["DataExportTag"]] = k
        return self.tag2id_map

    def add_questions(self):
        responses = list()
        for _, q in self.questions_to_add.items():
            responses.append(self.survey_client.create_question(data=q))
        return responses

    def update_questions(self):
        responses = list()
        for _, q in self.questions_to_update.items():
            responses.append(self.survey_client.update_question(q["QuestionID"], data=q))
        return responses

    def delete_questions(self):
        responses = list()
        for _, q in self.questions_to_delete.items():
            responses.append(self.survey_client.delete_question(q["QuestionID"]))
        return responses

    def parse_questions(self, interactive=False):
        """
        Args:
            interactive: If True, asks for confirmation of changes before applying to survey

        Returns:

        """
        def covert_key_from_id_to_tag(questions):
            return {v["DataExportTag"]: v for _, v in questions.items()}

        def question_text_is_identical(q1, q2):
            return q1["QuestionText"] == q2["QuestionText"]

        static_questions = {'Q100': comment_question}
        existing_questions = covert_key_from_id_to_tag(self.survey['Questions'])
        self.questions_to_delete = {k: v for k, v in existing_questions.items()}  # if k not in static_questions.keys()}  #[v for k, v in existing_questions.items() ]
        for group in [self.new_questions, static_questions]:
            for k, v in group.items():
                if k not in existing_questions.keys():
                    self.questions_to_add[k] = v
                else:
                    del self.questions_to_delete[k]  #self.questions_to_delete.remove(existing_questions[k])
                    if not question_text_is_identical(v, existing_questions[k]):
                        v["QuestionID"] = existing_questions[k]["QuestionID"]
                        self.questions_to_update[k] = v

        for verb, question_dict in [('add', self.questions_to_add), ('update', self.questions_to_update), ('delete', self.questions_to_delete)]:
            print(f"{len(question_dict.keys())} questions to {verb}:")
            for _, v in question_dict.items():
                print(f"QuestionID: {v.get('QuestionID')}; DataExportTag: {v['DataExportTag']}; question: {v}\n")
            print("\n")

        if interactive:
            i = input("Would you like to apply the changes above? [y/N]")
            if i not in ['y', 'Y']:
                print('No changes applied to survey')
                return None

        add_responses = self.add_questions()
        logger.info('Responses from self.add_questions', extra={'responses': add_responses})
        update_responses = self.update_questions()
        logger.info('Responses from self.update_questions', extra={'responses': update_responses})
        delete_responses = self.delete_questions()
        logger.info('Responses from self.delete_questions', extra={'responses': delete_responses})


def main(interactive=False):
    """
    Args:
        interactive: If True, asks for confirmation of changes before applying to survey
    """

    csv_parser = CsvParser('qualtrics-import-data-v01.csv')
    question_list = csv_parser.parse_into_question_list()
    rendered_questions_dict = {x.data_export_tag: x.rendered_question() for x in question_list}
    logger.debug('rendered_questions_dict', extra=rendered_questions_dict)
    update_manager = SurveyUpdateManager(rendered_questions_dict, survey_id="SV_9HcwQ4EhfsTlnJr")
    update_manager.parse_questions(interactive)


    # for id, question in rendered_questions_by_id.items():
    #
    # qid3 = questions['QID3']
    # edited_q = deepcopy(qid3)
    #
    # edited_q["QuestionDescription"] = None
    #
    # qs.update_question('QID3', edited_q)
    # print(qid3)

    # for q in questions:
    #     print(q.rendered_question())
    #     print('\n\n')


if __name__ == "__main__":
    main()
