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
from copy import deepcopy

import common.qualtrics as qs
import thiscovery_lib.utilities as utils

DEFAULT_SURVEY = "SV_9SUp48JfOurEzI1"
logger = utils.get_logger()
warning_counter = 0

env = j2.Environment(
    loader=j2.FileSystemLoader('.'),
)

# region question templates
# region dynamic questions
like_rephrasing_question_dict = {
    "QuestionText": None,
    "DataExportTag": None,  # "Q1"
    "QuestionType": "MC",
    "Selector": "SAVR",
    "SubSelector": "TX",
    "Configuration": {"QuestionDescriptionOption": "UseText", "Autoscale": {"YScale": {"Name": "yesNo", "Type": "likert", "Reverse": False}}},
    "Choices": {"1": {"Display": "yes"}, "2": {"Display": "no"}},
    "ChoiceOrder": ["1", "2"],
    "Validation": {"Settings": {"ForceResponse": "OFF", "ForceResponseType": "ON", "Type": "None"}},
    "Language": [],
    # "QuestionID": "QID1",  Note: question ID cannot be set via the API
    "DataVisibility": {"Private": False, "Hidden": False},
}
# endregion

# region repetitive questions
COMMENT_QUESTION_POSTFIX = "COM"
comment_question = {
    'QuestionText': 'Do you have any comments on the rephrased indicator?',
    'DefaultChoices': False,
    'DataExportTag': None,
    'QuestionType': 'TE',
    'Selector': 'ML',
    'Configuration': {'QuestionDescriptionOption': 'UseText', 'InputWidth': 658, 'InputHeight': 208},
    'QuestionDescription': 'Do you have any comments on the rephrased indicator?',
    'Validation': {'Settings': {'ForceResponse': 'OFF', 'ForceResponseType': 'ON', 'Type': 'None'}},
    'GradingData': [], 'Language': [],
    'SearchSource': {'AllowFreeResponse': 'false'},
    'QuestionText_Unsafe': 'Do you have any comments on the rephrased indicator?'
}
# endregion
# endregion

indicator_block_template = {
    'Type': 'Standard',
    'Description': 'Untitled block',
    'BlockElements': [{'Type': 'Question', 'QuestionID': None}, {'Type': 'Question', 'QuestionID': None}]
}

precise_indicator_phrasing_question_template = env.get_template('precise_indicator_phrasing_question.j2')


class IndicatorPhrasingQuestion:
    def __init__(self, data_export_tag, original_phrasing, rephrased_indicator, explanatory_terms=None,
                 rationale_for_change=None):
        self.data_export_tag = data_export_tag
        self.original_phrasing = original_phrasing
        self.rephrased_indicator = rephrased_indicator
        self.explanatory_terms = explanatory_terms
        self.rationale_for_change = rationale_for_change
        self.question_text_template = precise_indicator_phrasing_question_template
        self.question_dict = deepcopy(like_rephrasing_question_dict)

    def rendered_question_text(self):
        return self.question_text_template.render(
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
    def __init__(self, questions_dict, survey_id=None, survey_name=None):
        """
        Args:
            questions_dict: Dictionary of questions indexed by "DataExportTag"
            survey_id: If None, create a new survey
            survey_name: Name of new survey, if a survey is being created
        """
        self.survey_client = qs.SurveyDefinitionsClient(survey_id=survey_id)

        if survey_id is None:
            if survey_name == "Test survey":
                from random import randrange
                survey_name = f"Test survey {randrange(99999)}"
            self.survey_client.create_survey(survey_name)
            print(f"Created new survey: {survey_name}")

        self.survey = self.survey_client.get_survey()['result']
        self.input_questions = questions_dict

        self.comment_box_questions = dict()
        for k, v in self.input_questions.items():
            com_q = deepcopy(comment_question)
            com_q.update({'DataExportTag': f"{k}{COMMENT_QUESTION_POSTFIX}"})
            self.comment_box_questions[f"{k}{COMMENT_QUESTION_POSTFIX}"] = com_q

        self.questions_to_update = dict()
        self.questions_to_add = dict()
        self.questions_to_delete = dict()
        self.questions_not_to_touch = dict()

        self.blocks_to_update = dict()
        self.blocks_to_add = dict()
        self.blocks_to_delete = dict()
        self.blocks_not_to_touch = dict()

        self.question_ids = list()
        self.thrash_block_id = None

    # region block methods
    def add_blocks(self):
        """
        Qualtrics' "Create block" API method (https://api.qualtrics.com/reference#create-block) does not accept the BlockElements parameter,
        so this function creates the new block without it and then immediately updates it with the required Elements.

        Returns:
            Dictionary of responses from the create and update phases: {'create_response': x, 'update_response': y}
        """
        responses = dict()
        for k, v in self.blocks_to_add.items():
            block_elements = v.pop("BlockElements")
            create_response = self.survey_client.create_block(data=v)
            block_id = create_response['result']["BlockID"]
            v["BlockElements"] = block_elements
            update_response = self.survey_client.update_block(block_id, data=v)
            responses[k] = {'create_response': create_response, 'update_response': update_response}
        return responses

    def update_blocks(self):
        responses = dict()
        for k, v in self.blocks_to_update.items():
            responses[k] = self.survey_client.update_block(v['ID'], data=v)
        return responses

    def delete_blocks(self):
        responses = dict()
        for k, v in self.blocks_to_delete.items():
            responses[k] = self.survey_client.delete_block(v['ID'])
        return responses
    # endregion

    # region question methods
    def add_questions(self):
        responses = dict()
        for k, q in self.questions_to_add.items():
            responses[k] = self.survey_client.create_question(data=q)
        return responses

    def update_questions(self):
        responses = dict()
        for k, q in self.questions_to_update.items():
            responses[k] = self.survey_client.update_question(q["QuestionID"], data=q)
        return responses

    def delete_questions(self):
        responses = dict()
        for k, q in self.questions_to_delete.items():
            responses[k] = self.survey_client.delete_question(q["QuestionID"])
        return responses
    # endregion

    def parse_questions(self, interactive=False):
        """
        Args:
            interactive: If True, asks for confirmation of changes before applying to survey

        Returns:
            Tuple of responses (dict objects) of requests to add, update and delete questions:
            (add_responses, update_responses, delete_responses)
        """
        def covert_key_from_id_to_tag(questions):
            return {v["DataExportTag"]: v for _, v in questions.items()}

        def question_text_is_identical(q1, q2):
            return q1["QuestionText"] == q2["QuestionText"]

        if self.survey['Questions']:
            existing_questions = covert_key_from_id_to_tag(self.survey['Questions'])
        else:
            existing_questions = dict()
        self.questions_to_delete = {k: v for k, v in existing_questions.items()}
        for group in [self.input_questions, self.comment_box_questions]:
            for k, v in group.items():
                if k not in existing_questions.keys():
                    self.questions_to_add[k] = v
                else:
                    del self.questions_to_delete[k]
                    v["QuestionID"] = existing_questions[k]["QuestionID"]
                    if not question_text_is_identical(v, existing_questions[k]):
                        self.questions_to_update[k] = v
                    else:
                        self.questions_not_to_touch[k] = v

        for verb, question_dict in [('add', self.questions_to_add), ('update', self.questions_to_update),
                                    ('delete', self.questions_to_delete), ('leave untouched', self.questions_not_to_touch)]:
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

        # update added questions with Qualtrics QuestionID
        for k, v in add_responses.items():
            question = self.questions_to_add[k]
            question['QuestionID'] = v['result']['QuestionID']

        return add_responses, update_responses, delete_responses

    def parse_blocks(self):
        def covert_key_from_block_id_to_question_id(blocks, survey_update_manager):
            converted_blocks = dict()
            for k_, v_ in blocks.items():

                # skip the Trash block
                if v_["Type"] == "Trash":
                    logger.debug(f'Skipped Trash block {k_}')
                    survey_update_manager.thrash_block_id = k_
                    continue

                try:
                    converted_blocks[
                        # v_['BlockElements'][0]['QuestionID']
                        v_['Description']  # description also holds the QuestionID and works for empty blocks (that had all their questions deleted)
                    ] = {**v_, 'block_id': k_}
                except KeyError:
                    logger.warning(f'Block {k_} was not created by this script; it will be ignored', extra={'block definition': v_})
                    global warning_counter
                    warning_counter += 1
            return converted_blocks

        def block_elements_are_identical(b1, b2):
            return b1["BlockElements"] == b2["BlockElements"]

        self.survey = self.survey_client.get_survey()['result']  # question updates can change the structure of the blocks, so refresh self.survey
        existing_blocks = covert_key_from_block_id_to_question_id(self.survey['Blocks'], self)
        self.blocks_to_delete = deepcopy(existing_blocks)

        main_questions_for_blocks = {**self.questions_to_add, **self.questions_to_update, **self.questions_not_to_touch}
        self.question_ids = [v['QuestionID'] for _, v in main_questions_for_blocks.items()]

        for k, v in self.comment_box_questions.items():
            del main_questions_for_blocks[k]

        for k, v in main_questions_for_blocks.items():
            question_id = v['QuestionID']
            block_elements_dict = {'BlockElements': [
                {'Type': 'Question', 'QuestionID': question_id},
                {'Type': 'Question', 'QuestionID': self.comment_box_questions[f"{k}{COMMENT_QUESTION_POSTFIX}"]['QuestionID']}
            ]}
            edited_block = deepcopy(indicator_block_template)
            edited_block.update({**block_elements_dict, 'Description': question_id})
            if question_id not in existing_blocks.keys():
                self.blocks_to_add[question_id] = edited_block
            else:
                del self.blocks_to_delete[question_id]
                edited_block["ID"] = existing_blocks[question_id]["ID"]
                if not block_elements_are_identical(block_elements_dict, existing_blocks[question_id]):
                    self.blocks_to_update[question_id] = edited_block
                else:
                    self.blocks_not_to_touch[question_id] = edited_block

        for verb, block_dict in [('add', self.blocks_to_add), ('update', self.blocks_to_update), ('delete', self.blocks_to_delete)]:
            print(f"{len(block_dict.keys())} blocks to {verb}:")
            for _, v in block_dict.items():
                print(f"ID: {v.get('ID')}; BlockElements: {v['BlockElements']}; block: {v}\n")
            print("\n")

        add_responses = self.add_blocks()
        logger.info('Responses from self.add_blocks', extra={'responses': add_responses})
        update_responses = self.update_blocks()
        logger.info('Responses from self.update_blocks', extra={'responses': update_responses})
        delete_responses = self.delete_blocks()
        logger.info('Responses from self.delete_blocks', extra={'responses': delete_responses})

        return add_responses, update_responses, delete_responses

    def remove_questions_managed_by_this_script_from_thrash_block(self):
        self.survey = self.survey_client.get_survey()['result']  # refresh self.survey
        thrash_block = self.survey['Blocks'][self.thrash_block_id]
        try:
            edited_block_elements = [x for x in thrash_block['BlockElements'] if x['QuestionID'] not in self.question_ids]
        except KeyError as err:
            print(f"thrash_block: {thrash_block}")
            raise err

        thrash_block.update({'BlockElements': edited_block_elements})
        return self.survey_client.update_block(self.thrash_block_id, data=thrash_block)

    def update_survey(self, interactive=False):
        """
        This is the main routine of this class.

        Returns:
            Tuple of responses from the parse questions and parse blocks phases
        """
        parse_questions_results = self.parse_questions(interactive)
        parse_blocks_results = self.parse_blocks()
        cleanup_result = ({"cleanup_result": self.remove_questions_managed_by_this_script_from_thrash_block()},)
        return parse_questions_results, parse_blocks_results, cleanup_result


def main(survey_id=None, survey_name=None, input_dataset='qualtrics-import-data-v01.csv', interactive=False):
    """
    Args:
        survey_id: If None, a new survey will be created; otherwise survey matching survey_id will be updated
        survey_name: If survey_id is None, a new survey will be created using this name.
        input_dataset: File containing survey questions
        interactive: If True, asks for confirmation of changes before applying to survey
    """
    csv_parser = CsvParser(input_dataset)
    question_list = csv_parser.parse_into_question_list()
    rendered_questions_dict = {x.data_export_tag: x.rendered_question() for x in question_list}
    logger.debug('rendered_questions_dict', extra=rendered_questions_dict)
    update_manager = SurveyUpdateManager(rendered_questions_dict, survey_id=survey_id, survey_name=survey_name)
    update_successful = True
    results = update_manager.update_survey(interactive)
    for entity in results:
        for verb in entity:
            if verb:
                for _, v in verb.items():
                    try:
                        if v['meta']['httpStatus'] != '200 - OK':
                            update_successful = False
                    except KeyError:  # add_block responses have a different structure
                        if v['create_response']['meta']['httpStatus'] != '200 - OK':
                            update_successful = False
                        if v['update_response']['meta']['httpStatus'] != '200 - OK':
                            update_successful = False

    warning_message = ""
    if warning_counter:
        warning_message = f" ({warning_counter} warnings were issued; see log for details)"

    if update_successful:
        print(f"Survey updated successfully{warning_message}")
    else:
        print(f"Survey update failed{warning_message}")


if __name__ == "__main__":
    """
    Pass either survey_id to update an existing survey or survey_name to create a new survey.
    If survey_name == "Test survey", the survey created will be named "Test survey XXXXX", where
    XXXXX is a random 5 digit integer. 
    """
    main(
        # survey_id=DEFAULT_SURVEY,
        survey_name="Test survey",
        input_dataset='qualtrics-import-data-v01.csv',
        # interactive=True,
    )
