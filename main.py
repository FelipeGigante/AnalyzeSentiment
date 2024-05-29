from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import os
import dotenv

class ReviewApp(App):
    def build(self):
        dotenv.load_dotenv(dotenv.find_dotenv())
        self.api_key = os.getenv("api_key")
        self.title = 'Google Reviews Sentiment Analysis'
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.label = Label(text='Digite o nome ou endereço do lugar:', color=(1, 1, 1, 1), font_size=18)
        layout.add_widget(self.label)
        
        self.input = TextInput(multiline=False, size_hint_y=None, height=40, background_color=(0.1, 0.5, 0.6, 1), foreground_color=(1, 1, 1, 1))
        layout.add_widget(self.input)
        
        self.button = Button(text='Buscar Avaliações', size_hint_y=None, height=50, background_color=(0.1, 0.5, 0.6, 1))
        self.button.bind(on_press=self.on_button_press)
        layout.add_widget(self.button)
        
        self.result_label = Label(text='', color=(1, 1, 1, 1), font_size=16)
        layout.add_widget(self.result_label)
        
        layout.add_widget(Label())  # Spacer
        
        return layout

    def on_button_press(self, instance):
        query = self.input.text
        self.result_label.text = 'Buscando avaliações...'
        self.fetch_reviews(query)

    def fetch_reviews(self, query):
        import requests
        import pandas as pd
        from textblob import TextBlob

        def get_place_id(api_key, query):
            url_place_id = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=place_id,name&key={api_key}"
            response = requests.get(url_place_id)
            place_details = response.json()
            if place_details['candidates']:
                return place_details['candidates'][0]['place_id'], place_details['candidates'][0]['name']
            return None, None

        def get_reviews(api_key, place_id):
            url_reviews = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&language=pt-BR&key={api_key}"
            response = requests.get(url_reviews)
            place_reviews = response.json()
            return place_reviews.get('result', {}).get('reviews', [])

        def analyze_sentiments(reviews):
            reviews_list = []
            for review in reviews:
                sentiment = TextBlob(review['text']).sentiment.polarity
                sentiment_label = 'Positive' if sentiment > 0 else 'Neutral' if sentiment == 0 else 'Negative'
                reviews_list.append([review['author_name'], review['rating'], review['text'], review['time'], sentiment_label])
            return pd.DataFrame(reviews_list, columns=['Author', 'Rating', 'Text', 'Time', 'Sentiment'])

        place_id, place_name = get_place_id(self.api_key, query)
        if place_id:
            reviews = get_reviews(self.api_key, place_id)
            if reviews:
                df = analyze_sentiments(reviews)
                self.result_label.text = df.to_string()
            else:
                self.result_label.text = "Nenhuma avaliação encontrada para este lugar."
        else:
            self.result_label.text = "Nenhum lugar encontrado com essa consulta."

if __name__ == '__main__':
    ReviewApp().run()
