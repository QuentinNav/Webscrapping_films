# Imports
import streamlit as st
import sens_critique
import allocine
import imdb
from selenium import webdriver
import utils
import manager


st.title("CINEAVIS")
st.markdown('Quentin NAVARRE, Edouard BERTRAND, DIA1')

query = st.text_input("Quel film allons-nous décrypter aujourd'hui ?")

if query:
    load_text = st.text("Chargement...")
    data = manager.get_data(query, load_text)
    if data is None:
        load_text.text('Erreur')
    else:
        load_text.text('Succès')
        manager.show_info(data)



#actors = ['5188', '2448', '2381', '55851', '3441', '32251', '5038', '24463']
#people = [{'id': '296', 'nom': 'Elia Kazan'}, {'id': '37754', 'nom': 'John Steinbeck'}, {'id': '78318', 'nom': 'Paul Osborn'}, {'id': '5188', 'nom': 'James Dean'}, {'id': '2448', 'nom': 'Julie Harris'}, {'id': '2381', 'nom': 'Raymond Massey'}, {'id': '55851', 'nom': 'Richard Davalos'}, {'id': '3441', 'nom': 'Burl Ives'}, {'id': '32251', 'nom': 'Jo Van Fleet'}, {'id': '5038', 'nom': 'Albert Dekker'}, {'id': '24463', 'nom': 'Lois Smith'}]
#result = utils.convert_ids_to_people(actors, people)





#movie_id, poster = allocine.get_id_from_query("A l'est d'eden")
#print(poster)
    #title, rating, reviews = sens_critique.get_data_from_sens_critique(query)
    #st.markdown(title)
    #st.markdown(rating)
    #for review in reviews:
    #    st.markdown(review[0])
    #    st.markdown(review[1])
    #    st.markdown(review[2])
    #    st.markdown(review[3])

#title, rating, reviews = sens_critique.get_data_from_sens_critique('avatar')




