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




def get_data_from_sens_critique(driver, a_titre, a_date, a_reals, load_text):
    query = utils.format_key_words(a_titre)
    url = f"https://www.senscritique.com/search?query={query}&size=16"
    driver.get(url)
    '''cookies_box = find_on_page(driver, '//*[@id="didomi-notice-agree-button"]')
    cookies_box.click()'''
    load_text.text("Récupération du film...")
    time.sleep(3)
    movie_container_results = driver.find_elements(By.CSS_SELECTOR,
                                                   "div[class='ExplorerProductCard__Container-sc-1fw1q8r-0 gkhVSD']")
    if movie_container_results == None:
        return None

    detailed_scores = []
    similarity_scores = []
    rates = []
    for i in range(len(movie_container_results)):
        div = movie_container_results[i]
        try:
            title_element = div.find_element(By.CSS_SELECTOR,
                                             "a[class='Text__SCText-sc-kgt5u3-0 Link__SecondaryLink-sc-1vfcbn2-1 jbJnwO eDKWEX']")
            title = title_element.text
        except:
            title = ""
        try:
            rating_element = div.find_element(By.CSS_SELECTOR, "*[data-testid='Rating']")
            rate = float(rating_element.text)
        except:
            rate = np.NAN
        try:
            desc_element = div.find_element(By.CSS_SELECTOR, "p[data-testid='product-explorer-creator']")
            desc = desc_element.text
        except:
            desc = "Film"
        desc = desc.split(' · ')
        if len(desc) == 2:
            date = int(desc[1])
        else:
            date = -1000
        desc = desc[0].split('Film de ')
        if len(desc) == 2:
            producers = desc[1].split(', ')
        else:
            producers = []
        detailed_score = utils.score_similarite(a_titre, a_date, a_reals, title, date, producers)
        mean_score = detailed_score[3]
        detailed_scores.append(detailed_score)
        similarity_scores.append(mean_score)
        rates.append(rate)
    container = movie_container_results[np.argmax(similarity_scores)]
    movie_link = container.find_element(By.CSS_SELECTOR,
                                        "a[class='Text__SCText-sc-kgt5u3-0 Link__SecondaryLink-sc-1vfcbn2-1 jbJnwO eDKWEX']")
    sc_id = "/".join(movie_link.get_attribute('href').split('/')[-2:])
    rating = rates[np.argmax(similarity_scores)]
    mean_similarity = similarity_scores[np.argmax(similarity_scores)]
    load_text.text("Recherche des critiques - Page 1")
    driver.get(f"https:www.senscritique.com/film/{sc_id}/critiques")
    review_elements = driver.find_elements(By.LINK_TEXT, "Lire la critique")
    review_ids = [review_element.get_attribute('href').split('/')[-1] for review_element in review_elements]
    i = 0
    for i in range(2):
        try:
            next_page = driver.find_elements(By.CSS_SELECTOR, f"span[data-testid='click-{i + 2}']")[0]
        except:
            # print(f'FAILED AT FINDING {i+2}')
            break
        driver.execute_script("window.scrollTo(0, 400)")
        time.sleep(.3)
        next_page.click()
        load_text.text(f"Recherche des critiques - Page {i+2}")
        # print("passing")
        while all(item in review_elements for item in driver.find_elements(By.LINK_TEXT, "Lire la critique")):
            pass
        # print("found")
        review_elements = driver.find_elements(By.LINK_TEXT, "Lire la critique")
        for element in review_elements:
            if element.get_attribute('href').split('/')[-1] not in review_ids:
                review_ids.append(element.get_attribute('href').split('/')[-1])
    load_text.text('Récupération des critiques...')
    # GET REVIEWS CONTENT
    review_titles = []
    review_authors = []
    review_ratings = []
    review_bodys = []
    for r_id in review_ids:
        response = requests.get(f"https://www.senscritique.com/film/{sc_id.split('/')[0]}/critique/{r_id}")
        review_soup = BeautifulSoup(response.content, 'html.parser')
        review_title = review_soup.find('h1').text
        review_author = review_soup.find('a',
                                         class_='Text__SCText-sc-kgt5u3-0 Username__WrapperUsername-sc-19yskas-1 hrLruW').text
        review_rating = int(review_soup.find('div', class_='Rating__UserRating-sc-1rkvzid-2 fylBAF').text)
        review_body = review_soup.find('div', class_='Content__Container-sc-1a6ct0l-0 kJVhmZ').text
        review_titles.append(review_title)
        review_authors.append(review_author)
        review_ratings.append(review_rating)
        review_bodys.append(review_body)
        reviews = list(zip(review_titles, review_authors, review_ratings, review_bodys))
        reviews = [{'titre_critique_sc': a[0], 'auteur_critique_sc': a[1], 'note_critique_sc': a[2],'contenu_critique_sc': a[3]} for a in reviews]
    return {"titre_sc" : title, "note_sc" : rating, "score_mean": mean_similarity, "critiques_sc": reviews}
    #reviews.append([review_ids, review_titles, review_authors, review_ratings, review_bodys])



    '''# GET MOVIE IDS AND RATINGS
    for i_titre in range(len(titres[0:10])):
        new_id = None
        rating = None
        search_box = find_on_page('//*[@id="search"]')
        search_box.send_keys(Keys.CONTROL + "A")
        search_box.send_keys(Keys.BACK_SPACE)
        search_box.send_keys(titres[i_titre])
        search_box.send_keys(Keys.ENTER)
        while new_first_id == last_first_id:
            try:
                movie_link = find_on_page('//*[@id="__next"]/div[1]/main/div[1]/div/div[2]/div[5]/div[1]/div[2]/h3/a')
                new_first_id = "/".join(movie_link.get_attribute('href').split('/')[-2:])
            except:
                pass
        last_first_id = new_first_id
        movie_container_results = driver.find_elements(By.CSS_SELECTOR,
                                                       "div[class='ExplorerProductCard__Container-sc-1fw1q8r-0 gkhVSD']")
        detailed_scores = []
        similarity_scores = []
        rates = []
        for i in range(len(movie_container_results)):
            div = movie_container_results[i]
            try:
                title_element = div.find_element(By.CSS_SELECTOR,
                                                 "a[class='Text__SCText-sc-kgt5u3-0 Link__SecondaryLink-sc-1vfcbn2-1 jbJnwO eDKWEX']")
                title = title_element.text
            except:
                title = ""
            try:
                rating_element = div.find_element(By.CSS_SELECTOR, "*[data-testid='Rating']")
                rate = float(rating_element.text)
            except:
                rate = np.NAN
            try:
                desc_element = div.find_element(By.CSS_SELECTOR, "p[data-testid='product-explorer-creator']")
                desc = desc_element.text
            except:
                desc = "Film"
            desc = desc.split(' · ')
            if len(desc) == 2:
                date = int(desc[1])
            else:
                date = -1000
            desc = desc[0].split('Film de ')
            if len(desc) == 2:
                producers = desc[1].split(', ')
            else:
                producers = []
            detailed_score = score_similarite(titres[i_titre], dates[i_titre], reals[i_titre], title, date, producers)
            mean_score = detailed_score[3]
            detailed_scores.append(detailed_score)
            similarity_scores.append(mean_score)
            rates.append(rate)
        container = movie_container_results[np.argmax(similarity_scores)]
        movie_link = container.find_element(By.CSS_SELECTOR,
                                            "a[class='Text__SCText-sc-kgt5u3-0 Link__SecondaryLink-sc-1vfcbn2-1 jbJnwO eDKWEX']")
        new_id = "/".join(movie_link.get_attribute('href').split('/')[-2:])
        movie_ids.append(new_id)
        rating = rates[np.argmax(similarity_scores)]
        movie_ratings.append(rating)

    print(movie_ids)
    print(movie_ratings)'''

