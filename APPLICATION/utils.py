import urllib
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import pandas as pd
import numpy as np
import Levenshtein as lev

import streamlit as st
import sens_critique
import allocine
import imdb
from selenium import webdriver
import utils




def format_key_words(movie_name):
    return urllib.parse.quote(movie_name)


def search_for_a_bit(driver, css_selector, seconds):
    start_time = time.time()
    while time.time() - seconds < start_time:
        try:
            element = driver.find_element(By.CSS_SELECTOR, css_selector)
            return element
        except:
            pass
    return None


def find_on_page(driver, xpath):
    while True:
        try:
            box = driver.find_element(By.XPATH, xpath)
            return box
        except:
            pass

def list_to_lower(list_strings):
    for i in range(len(list_strings)):
        list_strings[i] = list_strings[i].lower()
    return list_strings


def convert_ids_to_people(ids, people):
    dict_id_people = pd.DataFrame(people).set_index("id")["nom"].to_dict()
    liste_people = []
    for id in ids:
        nom = dict_id_people[id]
        liste_people.append(nom)
    return liste_people

# Renvoie le score de similarité entre 2 strings
def string_similarity(name1, name2):
    distance = lev.distance(name1, name2)
    min_length = min(len(name1), len(name2))
    result = (min_length - distance) / min_length
    return result * (result > 0)


# Calcul un score de similarité entre 2 années à partir de la distance en celles-ci
# On considère que s'il y a 3 années ou plus d'écart le score est de 0
def year_similarity(year1, year2):
    max = 5
    dif = abs(year1 - year2) / max
    score = 1 - (dif)
    return score * (score > 0)


# Calcul le score de similarité relié aux acteurs présents dans les 2 films
def actors_similarity(list_actors1, list_actors2):
    if type(list_actors2) == str:  # On s'assure que le deuxième paramètre est bien une liste
        list_actors2 = [list_actors2]
    if type(list_actors2) == tuple:
        list_actors2 = list(list_actors2)
    list_actors1 = list_to_lower(list_actors1)
    list_actors2 = list_to_lower(list_actors2)
    score = 0
    for actor in list_actors1:
        if actor in list_actors2:
            score += 1 / len(list_actors1)
        else:  # Au cas où l'orthographe ne serait pas exactement la même
            score += max([string_similarity(actor, actor2) for actor2 in list_actors2]) / len(list_actors1)
    return score


def score_similarite(name_imdb, year_imdb, actors_imdb, name, year, actors):
    title_score = string_similarity(name_imdb.lower(), name.lower()) if name_imdb != "" else 0
    year_score = year_similarity(year_imdb, year) if ~np.isnan(year_imdb) else 0

    if actors_imdb != [] and len(actors) > 0:
        actors_score = actors_similarity(actors_imdb, actors)
    elif actors_imdb == [] and len(actors) == 0:
        actors_score = 1
    else:
        actors_score = 0
    mean_score = (title_score + year_score + actors_score) / 3
    return title_score, year_score, actors_score, mean_score







