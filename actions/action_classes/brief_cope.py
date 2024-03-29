from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormValidationAction
from typing import Any, Text, Dict, List, Union

import json, requests

from utilities.constants import api_urls
from utilities.helpers import extract_entity

class ActionBriefCOPEResult(Action):

    def name(self) -> Text:
        return 'action_brief_cope_result'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        events= []
        answers= []

        for i in range(28): answers.append(tracker.get_slot(f'brief_cope_answer.score_{i+1}'))

        problem_focused_categories_average= {
            'active_coping': (answers[1]+answers[6])/2,
            'use_of_informational_support': (answers[9]+answers[22])/2,
            'positive_reframing': (answers[11]+answers[16])/2,
            'planning': (answers[13]+answers[24])/2
        }
        emotion_focused_categories_average= {
            'emotional_support': (answers[4]+answers[14])/2,
            'venting': (answers[8]+answers[20])/2,
            'humour': (answers[17]+answers[27])/2,
            'acceptance': (answers[19]+answers[23])/2,
            'self_blame': (answers[12]+answers[25])/2,
            'religion': (answers[21]+answers[26])/2
        }
        avoidant_categories_average= {
            'self_distraction': (answers[0]+answers[18])/2,
            'substance_use': (answers[3]+answers[10])/2, 
            'denial': (answers[2]+answers[7])/2,
            'behavioural_disengagement': (answers[5]+answers[15])/2
        }

        problem_focused_average= 0
        emotion_focused_average= 0
        avoidant_average= 0

        for key in problem_focused_categories_average: problem_focused_average+= problem_focused_categories_average[key]
        for key in emotion_focused_categories_average: emotion_focused_average+= emotion_focused_categories_average[key]
        for key in avoidant_categories_average: avoidant_average+= avoidant_categories_average[key]

        problem_focused_average/= 4
        emotion_focused_average/= 4 
        avoidant_average/= 4

        coping_strategy= ''

        if (problem_focused_average >= emotion_focused_average) and (problem_focused_average >= avoidant_average): coping_strategy= 'Problem-focused'
        elif (emotion_focused_average >= problem_focused_average) and (emotion_focused_average >= avoidant_average): coping_strategy= 'Emotion-focused'
        else: coping_strategy= 'Avoidant'

        # save_brief_cope_results = requests.post(
        #     url= f'{api_urls["production"]}/brief-cope-evaluation/save',
        #     headers= { 'Content-Type': 'application/json' },
        #     data= json.dumps({
        #         'user_id': tracker.sender_id,
        #         'coping_strategy': coping_strategy,
        #         'problem_focused': {
        #             'average': problem_focused_average,
        #             'categories': problem_focused_categories_average
        #         },
        #         'emotion_focused': {
        #             'average': emotion_focused_average,
        #             'categories': emotion_focused_categories_average
        #         },
        #         'avoidant': {
        #             'average': avoidant_average,
        #             'categories': avoidant_categories_average
        #         }
        #     })
        # )
        # response= save_brief_cope_results.json()

        # if response['status'] is False:
        #     dispatcher.utter_message(text= 'Failure to save the evaluation results, please try again')
        # else:

        dispatcher.utter_message(text= f"""Problem-focused (Focus on the problem): {problem_focused_average}
        \u2022 Active coping: {problem_focused_categories_average['active_coping']}
        \u2022 Use of informational support: {problem_focused_categories_average['use_of_informational_support']}
        \u2022 Positive reframing: {problem_focused_categories_average['positive_reframing']}
        \u2022 Planning: {problem_focused_categories_average['planning']}
        
        Emotional-focused (Focus on emotion): {emotion_focused_average}
        \u2022 Emotional support: {emotion_focused_categories_average['emotional_support']}
        \u2022 Venting: {emotion_focused_categories_average['venting']}
        \u2022 Humour: {emotion_focused_categories_average['humour']}
        \u2022 Acceptance: {emotion_focused_categories_average['acceptance']}
        \u2022 Self-blame: {emotion_focused_categories_average['self_blame']}
        \u2022 Religion: {emotion_focused_categories_average['religion']} 
        
        Avoidant (Delivering or avoidance): {avoidant_average}
        \u2022 Self-distraction: {avoidant_categories_average['self_distraction']}
        \u2022 Substance use: {avoidant_categories_average['substance_use']}
        \u2022 Denial: {avoidant_categories_average['denial']}
        \u2022 Behavioural disengagement: {avoidant_categories_average['behavioural_disengagement']}
        
        Based on the results above, Coping strategies tend to be more leading to {coping_strategy}""")
        events.append(SlotSet('current_coping_strategy', coping_strategy))

        return events

# class ActionBriefCOPEResultHistories(Action):

#     def name(self) -> Text:
#         return 'action_brief_cope_result_histories'

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         dates= extract_entity('datepicker_dates', tracker.latest_message['entities']).split('/')
#         get_brief_cope_results= requests.get(f'{api_urls["production"]}/brief-cope-evaluation/{tracker.sender_id}?start_date={dates[0]}&end_date={dates[1]}')
#         response= get_brief_cope_results.json()

#         if len(response['brief_cope_results']) == 0:
#             dispatcher.utter_message(text= 'You have never evaluated the coping strategy')
#             dispatcher.utter_message(response= 'utter_start_brief_cope.confirmation')
#         else:
#             results= ''

#             for result in response['brief_cope_results']:
#                 results+= f'Tanggal {result["created_at"]["date"]}: {result["coping_strategy"]}\n'

#             dispatcher.utter_message(text= results)

#         return []