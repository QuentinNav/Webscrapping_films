from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import numpy as np
import time
import urllib
from bs4 import BeautifulSoup
import requests
import streamlit as st
import utils
import re
import cv2
import urllib.request
from urllib.request import Request, urlopen


def get_id_from_query(driver, query, load_text):
    load_text.text("Connexion à Allociné...")
    query = utils.format_key_words(query)
    url = f"https://www.allocine.fr/rechercher/?q={query}"
    driver.get(url)
    load_text.text("Recherche du film...")
    section = utils.search_for_a_bit(driver, "section[class='section movies-results']", 10)
    if section is None:
        load_text.text("Film non trouvé")
        return None
    load_text.text("Récupération de l'id...")
    href = section.find_element(By.CSS_SELECTOR, "a[class='xXx meta-title-link']").get_attribute('href')
    movie_id = re.sub(r"\D", "", href)
    '''load_text.text("Récupération de l'affiche...")
    poster = utils.search_for_a_bit(driver, "img[class='thumbnail-img b-loaded']", 10)
    if poster is None:
        poster = None
    else:
        poster = poster.get_attribute('src')
        req = urllib.request.urlopen(poster)
        poster = np.asarray(bytearray(req.read()), dtype=np.uint8)
        poster = cv2.imdecode(poster, -1)  # 'Load it as it is'''
    return movie_id


def get_data_home(movie_id, driver):
    url = f"https://www.allocine.fr/film/fichefilm_gen_cfilm={movie_id}.html"
    data = {}
    driver.get(url)
    time.sleep(0.3)
    data["id"] = movie_id
    data["titre"] = driver.find_element(By.XPATH, '//*[@id="content-layout"]/div[2]/div[1]').text

    try:
        text_data = driver.find_element(By.CLASS_NAME, 'meta-body-item.meta-body-info')
    except:
        print("No text data found")
        print(data["titre"].lower())

    if "Date de sortie inconnue".lower() not in text_data.text.lower():
        try:
            data["date_sortie"] = text_data.find_elements(By.CLASS_NAME, "blue-link")[0].text
        except:
            try:
                data["date_sortie"] = text_data.find_elements(By.CLASS_NAME, "date")[0].text
            except:
                pass

                # Support de sortie
    support = text_data.find_elements(By.TAG_NAME, "strong")
    if len(support) != 0:
        data["support"] = support[0].text

    # Durée
    match = re.search(r"(\d{1,2}h\s\d{1,2}min)", text_data.text)
    if match:
        data["duree"] = match.group(0)

    # Genres du films
    genres = []
    for a in text_data.find_elements(By.TAG_NAME, "a"):
        if "genre" in a.get_attribute("href"):
            genres.append(a.text)
    data["genres"] = genres

    try:
        data["synopsis"] = data["synopsis"] = \
        driver.find_elements(By.ID, "synopsis-details")[0].find_elements(By.CLASS_NAME, "content-txt")[0].text
    except:
        print(f"{data['titre']} pas de synopsis")

    try:
        divs_eval = driver.find_elements_by_class_name('rating-item-content')
        if len(divs_eval) > 0:
            for elem in divs_eval:
                if "presse" in elem.text.lower():
                    data["note_moyenne_presse"] = elem.find_elements(By.CLASS_NAME, "stareval-note")[0].text
                if "spectateur" in elem.text.lower():
                    data["note_moyenne_spectateurs"] = elem.find_elements(By.CLASS_NAME, "stareval-note")[0].text
    except Exception as exc:
        print(data["titre"])
        print(exc)

    return data


#Scrappe les données de la page casting de l'identifant de film associé en utilisant le driver en input
def get_data_casting(movie_id, driver):
    url=f"https://www.allocine.fr/film/fichefilm-{movie_id}/casting/"
    data={"movie":{}, "people":[]}
    data["movie"]["movie_id"] =movie_id

    driver.get(url)
    time.sleep(0.3)

    #Scrapping des réalisateurs :
    sections = driver.find_elements(By.CLASS_NAME, "section.casting-director")
    if len(sections)>0 :
        section = BeautifulSoup(sections[0].get_attribute("innerHTML"), 'html.parser')#On converti la section en soup bf4
        directors = section.find_all("a",{"class" : "meta-title-link"})
        if len(directors)>0 :
            directors_id= []
            for director in directors :
                id =re.sub(r"\D", "",director.get("href"))#On récupère l'id du réalisateur
                data["people"].append({"id":id, "nom":director.text})
                directors_id.append(id)
            data["movie"]["realisateurs"]= directors_id


    #Scrapping des scénarites :
    sections= driver.find_elements(By.CLASS_NAME, "section.casting-list-gql")
    if len(sections) >0:
        for section in sections :
            section = BeautifulSoup(section.get_attribute("innerHTML"),"html.parser")
            titlebars = section.find_all("h2",{"class" :"titlebar-title titlebar-title-md" })
            if len(titlebars)>0 :
                for titlebar in titlebars :
                    if titlebar.text.lower() == "scénaristes" :
                        scenarists= section.find_all("a",{"class": "xXx item link"})
                        if len(scenarists)>0 :
                            scenarists_id =[]
                            for scenarist in scenarists :
                                id= re.sub(r"\D", "",scenarist.get("href"))#On récupère l'id du scénariste
                                data["people"].append({"id":id, "nom":scenarist.text})
                                scenarists_id.append(id)
                            data["movie"]["scenaristes"]=scenarists_id


    #Scrapping des acteurs :
    sections= driver.find_elements(By.CLASS_NAME, "section.casting-actor")
    if len(sections)>0 :
        section = BeautifulSoup(sections[0].get_attribute("innerHTML"), 'html.parser')#On converti la section en soup bf4
        actors= section.find_all("a",{"class" : "meta-title-link"})
        if len(actors)>0 :
            actors_id = []
            for actor in actors :
                id =re.sub(r"\D", "",actor.get("href"))#On récupère l'id de l'acteur
                data["people"].append({"id":id, "nom":actor.text})
                actors_id.append(id)
            data["movie"]["acteurs"]=actors_id

    return data


# Renvoie une liste de dictionnaires contenant les données pour chaque review présente sur la page.
# Si pas de commentaires sur la page renvoie une liste vide
def get_data_reviews_page(id_movie, num_page):
    url = f"https://www.allocine.fr/film/fichefilm-{id_movie}/critiques/spectateurs/?page={num_page}"
    data = []
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, 'html.parser')
        sections = soup.find_all("section", {"class": "section"})

        if len(sections) != 0:
            reviews = sections[0].find_all("div", {"class": "hred review-card cf"})
            if len(reviews) != 0:
                for index, review in enumerate(reviews):
                    data_review = {"id_movie": id_movie}
                    thumbnails = review.find_all("span", {"class": "thumbnail-container"})
                    divs_note = review.find_all("span", {'class': 'stareval-note'})
                    date_container = review.find_all("span", {"class": "review-card-meta-date light"})
                    div_contenu = review.find_all("div", {"class": "content-txt review-card-content"})

                    if len(thumbnails) != 0:
                        data_review["pseudo"] = thumbnails[0].get("title")
                    if len(divs_note) != 0:
                        data_review["note"] = divs_note[0].text
                    if len(date_container) != 0:
                        try:
                            data_review["date"] = re.search(r"(?i)Publiée le (\d{1,2} \w+ \d{4})",
                                                            date_container[0].text).group(1)
                        except:
                            print(f"id : {id_movie}, page : {num_page}, review : {index}, pas de date")
                    if len(div_contenu) != 0:
                        all_text = div_contenu[0].text
                        text_no_spoils = all_text
                        spoilers = div_contenu[0].find_all("span", {"class": "spoiler-content"})
                        if len(spoilers) > 0:
                            for spoil in spoilers:
                                text_no_spoils = text_no_spoils.replace(spoil.text, "\n")
                        data_review["contenu_complet"] = all_text
                        data_review["contenu_sans_spoils"] = text_no_spoils

                    data.append(data_review)
    except Exception as err:
        print(f'id :{id_movie}, page :{num_page}, erreur : {err}')

    return data

# inputs : id du film, nombre de pages maximal que l'on souhaite scrapper
# output
def reviews_movies(id_movie, num_pages, load_text):
    data = []  #
    num_page = 1
    while True:
        load_text.text(f"Récupération des critiques - Page {num_page}")
        data_returned = get_data_reviews_page(id_movie, num_page)

        # On vérifie que des données sont retournées
        if len(data_returned) == 0:
            break
            # On vérifie que l'on ne scrappe pas 2 fois les données de la dernière page
        if len(data) != 0 and data[-1]["contenu_complet"] == data_returned[-1]["contenu_complet"]:
            break

        data += data_returned
        num_page += 1
        if num_page == num_pages:
            break

    return data



