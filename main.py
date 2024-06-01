import os
import threading
import requests
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock

# Carregar variáveis de ambiente
import dotenv
dotenv.load_dotenv(dotenv.find_dotenv())

# Configurar a chave da API
api_key = os.getenv("api_key")

# Função para buscar o Place ID
def get_place_id(query, api_key):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": api_key
    }
    response = requests.get(url, params=params)
    result = response.json()
    if result["status"] == "OK":
        return result["candidates"][0]["place_id"]
    return None

# Função para buscar avaliações usando o Place ID
def fetch_reviews(place_id, api_key):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "review",
        "language": "pt",  # Define o idioma para português
        "key": api_key
    }
    response = requests.get(url, params=params)
    result = response.json()
    if result["status"] == "OK" and "reviews" in result["result"]:
        return result["result"]["reviews"]
    return []

# Inicializar o Sentiment Analyzer do NLTK (VADER)
sentiment_analyzer = SentimentIntensityAnalyzer()

# Função para analisar sentimentos usando VADER
def analyze_sentiment(text):
    score = sentiment_analyzer.polarity_scores(text)["compound"]
    return "Positive" if score >= 0 else "Negative"

class ReviewApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical')

        self.title_label = Label(text='Análise de Sentimento', font_size='24sp', size_hint=(1, 0.1))
        self.input_label = Label(text='Digite o nome ou endereço do lugar:', size_hint=(1, 0.1))
        self.input_box = TextInput(hint_text='Nome ou endereço', size_hint=(1, 0.1), multiline=False)
        self.input_box.bind(on_text_validate=self.on_search)

        self.search_button = Button(text='Buscar Avaliações', size_hint=(1, 0.1))
        self.search_button.bind(on_press=self.on_search)

        self.root.add_widget(self.title_label)
        self.root.add_widget(self.input_label)
        self.root.add_widget(self.input_box)
        self.root.add_widget(self.search_button)

        self.scroll_view = ScrollView()
        self.result_layout = GridLayout(cols=3, spacing=10, size_hint_y=None, padding=(10, 10))
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        self.scroll_view.add_widget(self.result_layout)
        self.root.add_widget(self.scroll_view)

        return self.root

    def on_search(self, instance):
        place_name = self.input_box.text
        threading.Thread(target=self.fetch_and_display_reviews, args=(place_name,)).start()

    def fetch_and_display_reviews(self, place_name):
        place_id = get_place_id(place_name, api_key)
        if place_id:
            reviews = fetch_reviews(place_id, api_key)
            processed_reviews = [(self.get_first_name(review["author_name"]), review["text"], review["rating"]) for review in reviews[:8]]
            Clock.schedule_once(lambda dt: self.display_reviews(processed_reviews))
        else:
            Clock.schedule_once(lambda dt: self.display_no_reviews())

    def get_first_name(self, full_name):
        return full_name.split()[0]

    def display_reviews(self, reviews):
        self.result_layout.clear_widgets()
        for author, text, rating in reviews:
            text_short = text[:100] + "..." if len(text) > 100 else text
            author_label = Label(text=author, size_hint_y=None, height=40, font_size='16sp')
            text_label = Label(text=text_short, size_hint_y=None, height=40, font_size='16sp')
            rating_label = Label(text=str(rating) + " - " + analyze_sentiment(text), size_hint_y=None, height=40, font_size='16sp')

            self.result_layout.add_widget(author_label)
            self.result_layout.add_widget(text_label)
            self.result_layout.add_widget(rating_label)

    def display_no_reviews(self):
        self.result_layout.clear_widgets()
        no_reviews_label = Label(text="Nenhuma avaliação encontrada.", size_hint_y=None, height=40, font_size='16sp')
        self.result_layout.add_widget(no_reviews_label)

if __name__ == '__main__':
    ReviewApp().run()
