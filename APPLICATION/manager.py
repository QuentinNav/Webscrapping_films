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

def get_data(query, load_text):
    options = webdriver.ChromeOptions()
    options.add_argument('-headless')
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    movie_id = allocine.get_id_from_query(driver, query, load_text)
    if movie_id is None:
        load_text.text("Film pas trouvé sur Allociné")
        return None
    st.text(movie_id)
    load_text.text("Récupération des données du film...")
    home_data = allocine.get_data_home(movie_id, driver)
    st.text(home_data)
    load_text.text("Récupération des données du casting...")
    casting_data = allocine.get_data_casting(movie_id, driver)
    st.text(casting_data)
    load_text.text("Récupération des critiques...")
    allo_reviews_data = allocine.reviews_movies(movie_id, 4, load_text)
    st.text(allo_reviews_data)
    load_text.text("Récupération du film sur IMDB...")
    list_actors = utils.convert_ids_to_people(casting_data['movie']['acteurs'], casting_data['people'])
    best_matching_imdb = imdb.get_best_matching_imdb(movie_id, home_data['titre'], list_actors,
                                                     int(home_data['date_sortie'].split(' ')[-1]))
    st.text(best_matching_imdb)
    if len(best_matching_imdb) == 0:
        load_text.text("Film pas trouvé sur IMDB")
        return None
    best_matching_imdb = best_matching_imdb[0]
    if best_matching_imdb['score_mean'] <= .66:
        load_text.text("Film pas trouvé sur IMDB")
        return None
    load_text.text("Récupération du box office...")
    box_office_data = imdb.get_data_box_office(movie_id, best_matching_imdb['href'])
    st.text(box_office_data)
    load_text.text("Connexion à SensCritique...")
    list_reals = utils.convert_ids_to_people(casting_data['movie']['realisateurs'], casting_data['people'])
    sc_reviews_data = sens_critique.get_data_from_sens_critique(driver, home_data['titre'],
                                                                int(home_data['date_sortie'].split(' ')[-1]),
                                                                list_reals, load_text)
    if sc_reviews_data is None:
        load_text.text("Film pas trouvé sur SensCritique")
        return None
    if sc_reviews_data['score_mean'] <= .66:
        load_text.text("Film pas trouvé sur SensCritique")
        return None
    st.text(sc_reviews_data)
    return {'home': home_data, 'casting': casting_data, 'box_office': box_office_data, 'allo_reviews': allo_reviews_data, 'sc_reviews': sc_reviews_data}

def show_info(data):
    st.markdown("<style>body { font-size: 30px;}</style>", unsafe_allow_html=True)
    st.markdown(data['home']['titre'])
    st.markdown("<style>body { font-size: 15px;}</style>", unsafe_allow_html=True)
    st.markdown(f"Sorti le {data['home']['date_sortie']}")
    st.markdown(data['home']['duree'])
    st.markdown(f"Box office : {data['box_office']['cumulativeworldwidegross']} $")
    st.markdown(", ".join(data['home']['genres']))
    st.markdown(f"Pays d'origine : {', '.join(data['box_office']['langue_origine'])}")
    st.markdown(f"Langue(s) d'origine : {', '.join(data['box_office']['pays_origine'])}")
    list_reals = utils.convert_ids_to_people(data['casting']['movie']['realisateurs'], data['casting']['people'])
    list_actors = utils.convert_ids_to_people(data['casting']['movie']['acteurs'], data['casting']['people'])
    list_scenars = utils.convert_ids_to_people(data['casting']['movie']['scenaristes'], data['casting']['people'])
    st.markdown(f"Réalisateur(ice)(s) : {', '.join(list_reals)}")
    st.markdown(f"Acteur(ice)(s) : {', '.join(list_actors)}")
    st.markdown(f"Scénariste(s) : {', '.join(list_scenars)}")
    st.markdown(f"Synopsis : {data['home']['synopsis']}")
    st.markdown(f"Critique par {data['allo_reviews'][0]['pseudo']} sur Allociné :")
    st.markdown(f"Note : {data['allo_reviews'][0]['note']} / 5.0")
    st.markdown(data['allo_reviews'][0]['contenu_sans_spoils'])
    st.markdown(f"Critique par {data['sc_reviews']['critiques_sc'][0]['auteur_critique_sc']} sur SensCritique :")
    st.markdown(data['sc_reviews']['critiques_sc'][0]['titre_critique_sc'])
    st.markdown(f"Note : {data['sc_reviews']['critiques_sc'][0]['note_critique_sc']} / 10.0")
    st.markdown(data['sc_reviews']['critiques_sc'][0]['contenu_critique_sc'])


