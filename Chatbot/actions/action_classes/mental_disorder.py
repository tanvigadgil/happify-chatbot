from typing import Any, Text, Dict, List
from matplotlib.pyplot import text
from rasa_sdk import Tracker, Action, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict

import requests

from utilities.constants import api_urls
from utilities.helpers import extract_entity

api_url= api_urls["production"]
not_yet_learn_template= 'utter_not_yet_learn_mental_disorder'

def get_mental_disorder(mental_disorder_name):
    response= requests.get(f'{api_url}/mental-disorders?name={mental_disorder_name}').json()

    if len(response['mental_disorders']) == 0:
        return None
    
    return response['mental_disorders'][0]

def get_mental_disorder_detail(mental_disorder, field):
    if field == 'short_description': 
        return mental_disorder['short_description']

    elif field == 'types':
        types= ''

        if len(mental_disorder['types']) == 0:
            types= 'Sorry, this type of data from this disorder is not yet available or maybe I don\'t understand'
        else:
            for type in mental_disorder['types']:
                types+= '- '+type['name']+'\n'
                types+= '  \u2022 '+type['short_description']+'\n'

        return types

    elif field == 'signs_and_symptoms':
        signs_and_symptoms= ''

        if len(mental_disorder['signs_and_symptoms']) == 0:
            signs_and_symptoms= 'Sorry, the data for the sign and symptoms of this disorder is not yet available or maybe I don\'t understand'
        else:
            for item in mental_disorder['signs_and_symptoms']:
                signs_and_symptoms+= '- '+item['point']+'\n'

                if len(item['description_points']) != 0: 
                    for description_point in item['description_points']:
                        signs_and_symptoms+= '  \u2022 '+description_point+'\n'

        return signs_and_symptoms

    elif field == 'causes':
        causes= ''

        if len(mental_disorder['causes']) == 0:
            causes= 'Sorry, the data for the cause of this disorder is not yet available or maybe I don\'t understand'
        else:
            for cause in mental_disorder['causes']:
                causes+= '- '+cause+'\n'
        
        return causes

    elif field == 'diagnosis':
        diagnosis= ''
        
        if len(mental_disorder['diagnosis']) == 0:
            diagnosis= 'Sorry, data on how to diagnose this disorder is not available or maybe I don\'t understand'
        else:
            for item in mental_disorder['diagnosis']:
                diagnosis+= '- '+item['point']+'\n'

                if item['description'] != '':
                    diagnosis+= '  \u2022 '+item['description']+'\n'

        return diagnosis
    
    elif field == 'complications':
        complications= ''

        if len(mental_disorder['complications']) == 0:
            complications= 'Sorry, the data for the complication effect of this disorder is not yet available or maybe I don\'t understand'
        else:
            for complication in mental_disorder['complications']:
                complications+= '- '+complication+'\n'

        return complications
    
    elif field == 'how_to_treat': 
        how_to_treat= ''

        if len(mental_disorder['how_to_treat']) == 0:
            how_to_treat= 'Sorry, the data for handling this disorder is not yet available or maybe I don\'t understand'
        else:
            for item in mental_disorder['how_to_treat']:
                how_to_treat+= '\u2022 '+item['point']+'\n'
                
                if item['description'] != '':
                    how_to_treat+= '  - '+item['description']+'\n'

                for description_point in item['description_points']:
                    how_to_treat+= '   \u2022 '+description_point+'\n'
        
        return how_to_treat
    
    elif field == 'how_to_prevent':
        how_to_prevent= ''

        if len(mental_disorder['how_to_prevent']) == 0:
            how_to_prevent= 'Sorry data how to prevent this disorder yet available or maybe I don\'t understand'
        else:
            for item in mental_disorder['how_to_prevent']:
                how_to_prevent+= item+'\n'
        
        return how_to_prevent

class ActionGetMentalDisorderList(Action):

   def name(self) -> Text:
       return 'action_get_mental_disorder_list'

   def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:        

        mental_disorders= requests.get(f'{api_url}/mental-disorders/list').json()['mental_disorders']
        response_text= ''

        for i in range(len(mental_disorders)):
            response_text+= f"{i+1}. {mental_disorders[i]['name']}\n"

        dispatcher.utter_message(text= response_text)

        return [SlotSet('explore_mental_disorder_list', mental_disorders)]

class ValidateGetExploreMentalDisorderNameForm(FormValidationAction):
    def name(self) -> Text: 
        return 'validate_get_explore_mental_disorder_name_form'

    def validate_explore_mental_disorder_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:

        mental_disorder_list= tracker.get_slot('explore_mental_disorder_list')

        try:
            mental_disorder_index= int(slot_value)
        except:
            dispatcher.utter_message(text= 'Input must be a number')
            return { 'explore_mental_disorder_name': None }

        if mental_disorder_index > len(mental_disorder_list) or mental_disorder_index < 1:
            dispatcher.utter_message(text= 'The number entered is not suitable')
            return { 'explore_mental_disorder_name': None }

        return { 'explore_mental_disorder_name': slot_value }

#In story
class ActionExploreMentalDisorderDescription(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_description'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
        buttons= [
            { 'title': 'Carry on',  'payload': '/continue_explore_mental_disorders' },
            { 'title': 'Stop', 'payload': '/stop_explore_mental_disorders' } 
        ]
           
        dispatcher.utter_message(text= f"Well, I'll explain it. For the first, namely the understanding of {mental_disorder_name}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'short_description'), buttons= buttons)

        return []

class ActionExploreMentalDisorderTypes(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_types'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
        buttons= [
            { 'title': 'Carry on',  'payload': '/continue_explore_mental_disorders' },
            { 'title': 'Stop', 'payload': '/stop_explore_mental_disorders' } 
        ]
            
        dispatcher.utter_message(text= f"Next is the type of interference {mental_disorder['name']}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'types'), buttons= buttons)

        return []

class ActionExploreMentalDisorderSignsAndsymptoms(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_signs_and_symptoms'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
        buttons= [
            { 'title': 'Carry on',  'payload': '/continue_explore_mental_disorders' },
            { 'title': 'Stop', 'payload': '/stop_explore_mental_disorders' } 
        ]
            
        dispatcher.utter_message(text= f"Next is a sign and symptom of interference {mental_disorder['name']}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'signs_and_symptoms'), buttons= buttons)

        return []

class ActionExploreMentalDisorderCauses(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_causes'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
        buttons= [
            { 'title': 'Carry on',  'payload': '/continue_explore_mental_disorders' },
            { 'title': 'Stop', 'payload': '/stop_explore_mental_disorders' } 
        ]
            
        dispatcher.utter_message(text= f"Following are the causes of interference {mental_disorder['name']}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'causes'), buttons= buttons)

        return []

class ActionExploreMentalDisorderDiagnosis(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_diagnosis'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
        buttons= [
            { 'title': 'Carry on',  'payload': '/continue_explore_mental_disorders' },
            { 'title': 'Stop', 'payload': '/stop_explore_mental_disorders' } 
        ]
            
        dispatcher.utter_message(text= f"Next is the way of diagnosing from interference {mental_disorder['name']}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'diagnosis'), buttons= buttons)            

        return []

class ActionExploreMentalDisorderComplications(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_complications'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
        buttons= [
            { 'title': 'Carry on',  'payload': '/continue_explore_mental_disorders' },
            { 'title': 'Stop', 'payload': '/stop_explore_mental_disorders' } 
        ]
            
        dispatcher.utter_message(text= f"Next is a complication that can occur from interference {mental_disorder['name']}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'complications'), buttons= buttons)          

        return []

class ActionExploreMentalDisorderHowToTreat(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_how_to_treat'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
        buttons= [
            { 'title': 'Carry on',  'payload': '/continue_explore_mental_disorders' },
            { 'title': 'Stop', 'payload': '/stop_explore_mental_disorders' } 
        ]
            
        dispatcher.utter_message(text= f"Next, namely how to handle from interference {mental_disorder['name']}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'how_to_treat'), buttons= buttons)        

        return []

class ActionExploreMentalDisorderHowToPrevent(Action):

    def name(self) -> Text:
        return 'action_explore_mental_disorder_how_to_prevent'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_index= int(tracker.get_slot('explore_mental_disorder_name'))-1
        mental_disorder_name= tracker.get_slot('explore_mental_disorder_list')[mental_disorder_index]['name']

        response= requests.get(f'{api_url}/mental-disorders/by-name/{mental_disorder_name}').json()

        if response['status'] is False:
            dispatcher.utter_message(response= not_yet_learn_template)
            return []

        mental_disorder= response['mental_disorder']
            
        dispatcher.utter_message(text= f"Lastly, which is a way to prevent or reduce disruption {mental_disorder['name']}")
        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'how_to_prevent'))        

        return []


#In rules
class ActionGetMentalDisorderDescription(Action):

    def name(self) -> Text:
        return 'action_get_mental_disorder_description'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'short_description')) 

        return [] 

class ActionGetMentalDisorderTypes(Action):
     
    def name(self) -> Text:
         return 'action_get_mental_disorder_types'

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'types'))

        return []

class ActionGetMentalDisorderSignsAndsymptoms(Action):

    def name(self) -> Text:
        return 'action_get_mental_disorder_signs_and_symptoms'
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())          

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'signs_and_symptoms'))

        return []

class ActionGetMentalDisorderCauses(Action):

    def name(self) -> Text:
        return 'action_get_mental_disorder_causes'
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())  

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'causes'))

        return []

class ActionMentalDisorderDiagnosis(Action):

    def name(self) -> Text:
        return 'action_get_mental_disorder_diagnosis'

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())  

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'diagnosis'))

        return []

class ActionGetMentalDisorderComplications(Action):

    def name(self) -> Text:
        return 'action_get_mental_disorder_complications'
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())  

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'complications'))

        return []

class ActionGetMentalDisorderHowToTreat(Action):

    def name(self) -> Text:
        return 'action_get_mental_disorder_how_to_treat'

    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())  

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'how_to_treat'))

        return []

class ActionGetMentalDisorderHowToPrevent(Action):

    def name(self) -> Text:
        return 'action_get_mental_disorder_how_to_prevent'
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mental_disorder_name= extract_entity('mental_disorder', tracker.latest_message['entities'])        
        mental_disorder= get_mental_disorder(mental_disorder_name.title())  

        dispatcher.utter_message(text= get_mental_disorder_detail(mental_disorder, 'how_to_prevent'))

        return []