import pandas as pd
from IPython.display import clear_output
import requests
from bs4 import BeautifulSoup
import urllib
from urllib.request import Request, urlopen
import re
import csv
import numpy as np
import re
from tqdm import tqdm
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from concurrent import futures
#import dateparser
import operator
import Levenshtein as lev
import random
import utils




def get_best_matching_imdb(movie_id, movie_name, list_actors, release_year) :
    mots_cles = utils.format_key_words(movie_name)#Encode le nom du film pour qu'il puisse être mis au format url
    movies_found= []
    #Accès à l'url de recherche
    url = f"https://www.imdb.com/find/?q={mots_cles}&s=tt&ttype=ft&ref_=fn_ft"

    #print(f"nom : {movie_name}, id :{movie_id}, release_year : {release_year}\nlist_actors : {list_actors}\n url : {url}")
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try :
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, 'html.parser')

        sections = soup.find_all("section",{"data-testid":"find-results-section-title"})

        #On va dans la section "titre"
        if len(sections)>0 :
            for section in sections :
                title_section = section.find("h3").text.lower()
                if "movie"  in title_section or "film" in title_section : #On est bien dans la section titre
                    divs = section.find_all("div",{"class":'ipc-metadata-list-summary-item__tc'})#Chaque div correspond à un film trouvé
                    if len(divs)>0 :
                        for div in divs :
                            data_movie_found= {'id_searched_movie':movie_id, 'titre':"", 'id':'', 'year':np.nan, 'actors' : []}

                            #Là où sont contenus le titre et l'identifiant du film traité
                            a =div.find_all("a", {"class":"ipc-metadata-list-summary-item__t", "role":"button"})#
                            if len(a)>0 :
                                data_movie_found["titre"]=a[0].text
                                data_movie_found["href"] = a[0].get("href")
                                match = re.search(r"tt\d+",data_movie_found["href"] )
                                if match:
                                    data_movie_found["id"] = match.group(0)
                                else :
                                    print("Pas d'id de film")
                                #Année :
                                label_years_actors = div.find_all("label", {"class": "ipc-metadata-list-summary-item__li", "role":"button"})
                                if len(label_years_actors)>0 :
                                    for label in label_years_actors :
                                        try :
                                            data_movie_found["year"] = int(label.text)
                                        except :
                                            data_movie_found["actors"]= label.text.split(", ")
                                movies_found.append(data_movie_found)

        if len(movies_found) == 0 :
            print(f"{movie_id} , {movie_name}, aucun résultat")
            movies_found = [{"id_searched_movie" : movie_id}]
        else :
            for movie in movies_found :
                #On calcule le score de similarité de chaque film :
                movie["score_title"], movie["score_year"], movie["score_actors"], movie["score_mean"]=utils.score_similarite(movie["titre"], movie["year"], movie["actors"], movie_name, release_year, list_actors )
            #On garde les 3 films avec le meilleur score moyen
            movies_found =  sorted(movies_found, key=lambda x: x['score_mean'], reverse=True)[:1]#On ne garde que le meilleur résultat
    except Exception as err:
        print(f"{movie_id}, {movie_name}, erreur : {err}")

    return movies_found


def get_data_box_office(movie_id, movie_href_imdb) :
    data={'movie_id': movie_id, 'href_imdb':movie_href_imdb}

    url =f"https://www.imdb.com{movie_href_imdb}"
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try :
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, 'html.parser')

        #Budget, revenues, Box office
        sections = soup.find_all("section",{"data-testid":"BoxOffice"})
        if len(sections)>0 :
            lis = sections[0].find_all("li",{"role": "presentation", "class" : "ipc-metadata-list__item"})
            if len(lis)>0 :
                for li in lis :
                    label = li.get("data-testid").split("-")[-1]
                    #label = li.find("button", {"class": "ipc-metadata-list-item__label","role":"button"}).text
                    value=np.nan
                    text= li.find("label", {"class" : "ipc-metadata-list-item__list-content-item","role":"button"}).text.replace(" ","").replace(",","")
                    match = re.search(r'\d+',text )
                    if match:
                        value = match.group()
                    data[label] = value
            else :
                print(f"Pas de li dans la section BoxOffice pour {url}")
        else :
            print(f"Pas de section BoxOffice pour {url}")


        #Pays et langue d'origine  :
        data["pays_origine"] =[]
        data["langue_origine"]= []

        sections = soup.find_all("section", {"data-testid":"Details"})
        if len(sections)>0 :

            #Pays d'origine
            try :
                lis_origin= sections[0].find("li",{'data-testid':"title-details-origin"}).find_all("li",{"role":'presentation', "class":"ipc-inline-list__item"})
            except :
                print(f"li title-details-origin pas trouvée pour {url}")

            if len(lis_origin)>0 :#Au moins un pays trouvé
                for li in lis_origin :
                    data["pays_origine"].append(li.text)
            else :
                print(f"Pas de pays d'origine pour {url}")

            #Langue d'origine
            try :
                lis_langue = sections[0].find("li",{"data-testid":'title-details-languages'}).find_all("li",{"role":"presentation","class":"ipc-inline-list__item"})
                if len(lis_langue)>0 :
                    for li in lis_langue :
                        data["langue_origine"].append(li.text)
                else :
                    print(f"Pas de langue d'origine pour {url}")
            except :
                print(f'li title-details-language pas trouvée pour {url}')

        else :
            print(f"Pas de section details pour {url}")
    except Exception as err :
        print(f"{url}, erreur : {err}")

    return data