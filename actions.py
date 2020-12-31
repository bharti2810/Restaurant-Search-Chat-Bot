# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/core/actions/#custom-actions/


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
# Import the email modules we'll need
from email.message import EmailMessage
import zomatopy
import json
import requests
# Import smtplib for the email sending function
import smtplib
from concurrent.futures import ThreadPoolExecutor

response_top10 = ''


class ActionSearchRestaurants(Action):
    def name(self):
        return 'action_search_restaurants'

    def run(self, dispatcher, tracker, domain):
        print("inside action search restaurant")
        config = {"user_key": "f4924dc9ad672ee8c4f8c84743301af5"}
        zomato = zomatopy.initialize_app(config)

        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        budget_min = tracker.get_slot('budgetmin')
        budget_max = tracker.get_slot('budgetmax')

        print('location; {}, cuisine: {}, budgetmin: {}, budgetmax: {}'.format(loc, cuisine, budget_min, budget_max))

        if not loc:
            return [SlotSet('location', loc), SlotSet('restaurant_exist', False)]

        results, lat, lon = self.get_location_suggestions(loc, zomato)
        print('result {}'.format(results))
        budget_restaurant_sorted = []
        if results == 0:
            restaurant_exist = False
            dispatcher.utter_message("Sorry, no results found in this location:(" + "\n")
        else:
            restaruant_list = self.get_restaurants(lat, lon, int(budget_min), int(budget_max), cuisine)
            print(restaruant_list)
            #print(type(restaruant_list[]))
            budget_restaurant = [restaurant for restaurant in restaruant_list if (
                        int((restaurant['restaurant']['average_cost_for_two']) > int(budget_min)) & (
                            int(restaurant['restaurant']['average_cost_for_two']) <= int(budget_max)))]
            print(type(budget_min))
            print(type(budget_max))

            budget_restaurant_sorted = sorted(budget_restaurant,
                                              key=lambda x: float(x['restaurant']['user_rating']['aggregate_rating']),
                                              reverse=True)

            response = ''
            global response_top10
            if response_top10:
                response_top10 = ''

        restaurant_exist = False

        if len(budget_restaurant_sorted) == 0:
            dispatcher.utter_message("No Restaurants found for the given price range under this location...")
            return
        else:
            top10_restaurant = budget_restaurant_sorted[:10]

        for index, restaurant in enumerate(top10_restaurant[:5]):
            response = response + str(index + 1) + ". " + restaurant['restaurant']['name'] + " in " + \
                       restaurant['restaurant']['location'][
                           'address'] + " and the average price for two people here is: " + str(
                restaurant['restaurant']['average_cost_for_two']) + " Rs. with rating " + \
                       str(restaurant['restaurant']['user_rating']['aggregate_rating']) + "\n" + "\n"

        for index, restaurant in enumerate(top10_restaurant):
            response_top10 = response_top10 + str(index + 1) + ". " + restaurant['restaurant']['name'] + " in " + \
                             restaurant['restaurant']['location'][
                                 'address'] + " And the average price for two people here is: " + str(
                restaurant['restaurant']['average_cost_for_two']) + " Rs. with rating " + \
                             restaurant['restaurant']['user_rating']['aggregate_rating'] + "\n" + "\n"

        dispatcher.utter_message("Showing you top rated restaurants:\n{}\n\n\n".format(response))

        return [SlotSet('location', loc), SlotSet('restaurant_exist', restaurant_exist)]


    def get_location_suggestions(self, loc, zomato):
        location_detail = zomato.get_location(loc, 1)
        d1 = json.loads(location_detail)
        print("d1 = " + str(d1))
        if "location_suggestions" in d1:
            lat = d1["location_suggestions"][0]["latitude"]
            lon = d1["location_suggestions"][0]["longitude"]
            results = len(d1["location_suggestions"])
            print("d1 = " + str(d1))
            print("results = : " + str(results))

        else:
            print("sorry, we don't operate in this city")
            
            results, lat, lon = 0, 0, 0
        return results, lat, lon

    def get_restaurants(self, lat, lon, budgetmin, budgetmax, cuisine):
        cuisines_dict = {
            'american': 1,
            'chinese': 25,
            'italian': 55,
            'mexican': 73,
            'north indian': 50,
            'south indian': 85
        }
        d_rest = []
        executor = ThreadPoolExecutor(max_workers=5)
        for res_key in range(0, 101, 20):
            executor.submit(retrieve_restaurant, lat, lon, cuisines_dict, cuisine, res_key, d_rest)
        executor.shutdown()
        return d_rest


def retrieve_restaurant(lat, lon, cuisines_dict, cuisine, res_key, d_rest):
    base_url = "https://developers.zomato.com/api/v2.1/"
    headers = {'Accept': 'application/json', 'user-key': '564d4320b0c8134c8339d303993e1e3b'}
    try:
        results = (requests.get(base_url + "search?" + "&lat=" + str(lat) + "&lon=" + str(lon) + "&cuisines=" + str(
            cuisines_dict.get(cuisine)) + "&start=" + str(res_key) + "&count=20", headers=headers).content).decode(
            "utf-8")
    except:
        return
    d = json.loads(results)
    d_rest.extend(d['restaurants'])


class ActionValidateCityName(Action):
    """This action is to validate user provided city name"""

    def name(self):
        # identifier of the action
        return 'action_validate_location'

    def run(self, dispatcher, tracker, domain):
        loc = tracker.get_slot('location')
        print('location name: {}'.format(loc))

        if not loc:
            dispatcher.utter_message("Please enter a location")
            return [SlotSet('location_ok', False)]

        allowed_cities = ['Agra', 'Ahmedabad', 'Ajmer', 'Aligarh', 'Amravati', 'Amritsar', 'Asansol', 'Aurangabad',
                          'Bangalore', 'Bareilly', 'Belgaum', 'Bhavnagar', 'Bhilai', 'Bhiwandi', 'Bhopal',
                          'Bhubaneswar', 'Bijapur', 'Bikaner',
                          'Bilaspur', 'Bokaro Steel City', 'Chandigarh', 'Chennai', 'Coimbatore', 'Cuttack', 'Dehradun',
                          'Delhi', 'Dhanbad',
                          'Durgapur', 'Erode', 'Faridabad', 'Firozabad', 'Ghaziabad', 'Goa', 'Gorakhpur', 'Gulbarga',
                          'Guntur', 'Gurgaon',
                          'Guwahati', 'Gwalior', 'Hamirpur', 'Hubli-Dharwad', 'Hyderabad', 'Indore', 'Jabalpur',
                          'Jaipur', 'Jalandhar', 'Jammu',
                          'Jamnagar', 'Jamshedpur', 'Jhansi', 'Jodhpur', 'Kakinada', 'Kannur', 'Kanpur', 'Kochi',
                          'Kolhapur', 'Kolkata',
                          'Kollam', 'Kozhikode', 'Kurnool', 'Lucknow', 'Ludhiana', 'Madurai', 'Malappuram', 'Mangalore',
                          'Mathura', 'Meerut',
                          'Moradabad', 'Mumbai', 'Mysore', 'Nagpur', 'Nanded', 'Nashik', 'Nellore', 'Noida', 'Patna',
                          'Pondicherry', 'Prayagraj',
                          'Pune', 'Purulia', 'Raipur', 'Rajahmundry', 'Rajkot', 'Ranchi', 'Rourkela', 'Salem', 'Sangli',
                          'Shimla', 'Siliguri',
                          'Solapur', 'Srinagar', 'Surat', 'Thiruvananthapuram', 'Thrissur', 'Tiruchirappalli',
                          'Tiruppur', 'Ujjain', 'Vadodara',
                          'Varanasi', 'Vasai-Virar City', 'Vellore', 'Vijayawada', 'Visakhapatnam', 'Warangal']

        if not (loc.title() in allowed_cities):
            dispatcher.utter_message("sorry, we don't operate in this city")
            return [SlotSet('location_ok', False)]
        return [SlotSet('location_ok', True), SlotSet('location', loc)]


class SendEmailAction(Action):
    def name(self):
        return 'action_send_email'

    def run(self, dispatcher, tracker, domain):
        to_email_id = tracker.get_slot("email_id")

        if not to_email_id:
            # dispatcher.utter_message('Good Bye')
            return

        location = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')

        global response_top10
        email_sub = self.get_email_subject(location, cuisine)
        email_body = 'Hi User,\nPlease find top {} restaurants in {}.\n\n{}Sincerely,\nFoodie Bot 1.0 by Bharti and Kaustubh'.format(
            cuisine, location, response_top10)

        self.send_email(to_email_id, email_sub, email_body)

        dispatcher.utter_message('Restaurants list has been sent to your email id. Enjoy!!')

    def send_email(self, to_email_id, email_sub, email_body):
        sender_email_add = 'kaustubh.bhargav@gmail.com'
        passowrd = 'KbB1993$#'

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email_add, passowrd)

        email = EmailMessage()
        email['Subject'] = email_sub
        email['To'] = to_email_id
        email['From'] = 'Foodie Bot 1.0 <{}>'.format(sender_email_add)
        email.set_content(email_body)

        server.send_message(email)
        server.quit()

    def get_email_subject(self, location, cuisine):
        return 'Top {} restaurants in {}'.format(cuisine.title(), location.title())


class ActionValidateCuisineName(Action):
    """This action is to validate user provided cuisine name"""

    def name(self):
        # identifier of the action
        return 'action_validate_cuisine'

    def run(self, dispatcher, tracker, domain):
        cuisine = tracker.get_slot('cuisine')
        print('cuisine name: {}'.format(cuisine))

        if not cuisine:
            dispatcher.utter_message("Please enter a cuisine")
            return [SlotSet('cuisine_ok', False)]

        allowed_cuisine = ['American', 'Chinese', 'Italian', 'Mexican', 'North Indian', 'South Indian']

        if not (cuisine.title() in allowed_cuisine):
            dispatcher.utter_message("sorry, we don't serve this cuisine")
            return [SlotSet('cuisine_ok', False)]
        return [SlotSet('cuisine_ok', True), SlotSet('cuisine', cuisine)]
