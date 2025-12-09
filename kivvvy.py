import json
import os
import hashlib
from functools import partial

from kivy import Config
# Configs are usually set before any Kivy module is imported
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
# Consolidated imports for ScreenManager and its transitions. SlideTransition is kept for usage in Python logic.
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.properties import StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.dropdown import DropDown
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView

# ---------- File utils ----------
USERS_FILE = 'users.json'
BOOKS_FILE = 'books.json'


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        admin = {'username': 'admin', 'password': sha256('admin'), 'is_admin': True}
        data = {'users': [admin]}
        with open(USERS_FILE, 'w') as f:
            json.dump(data, f, indent=2)


def load_users():
    ensure_users_file()
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def ensure_books_file():
    if not os.path.exists(BOOKS_FILE):
        sample = {
            'genres': {
                'Fiction': [
                    {'title': 'The Last Garden', 'author': 'A. Author', 'desc': 'A charming tale of...'},
                    {'title': 'Wind and Stars', 'author': 'E. Writer', 'desc': 'Space meets...'}
                ],
                'Science': [
                    {'title': 'Quantum Patterns', 'author': 'Dr. Q', 'desc': 'An introduction to...'},
                ],
                'Mystery': [
                    {'title': 'The Missing Key', 'author': 'Sleuth', 'desc': 'A whodunit set in...'}
                ]
            }
        }
        with open(BOOKS_FILE, 'w') as f:
            json.dump(sample, f, indent=2)


def load_books():
    ensure_books_file()
    with open(BOOKS_FILE, 'r') as f:
        return json.load(f)

# ---------- Hover behavior (Python) ----------
class HoverBehavior(Widget):
    hovered = BooleanProperty(False)
    border_point = ObjectProperty(None)
    __events__ = ('on_enter', 'on_leave')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        inside = self.collide_point(*self.to_widget(*pos))
        if inside and not self.hovered:
            self.hovered = True
            try:
                self.dispatch('on_enter')
            except Exception:
                pass
        elif not inside and self.hovered:
            self.hovered = False
            try:
                self.dispatch('on_leave')
            except Exception:
                pass

    def on_enter(self):
        pass

    def on_leave(self):
        pass

# ---------- Kivy UI (KV string) ----------
KV = r'''
<BoxLabel@Label>:
    size_hint_y: None
    height: self.texture_size[1] + dp(12)

<HoverButton@ButtonBehavior+Label+HoverBehavior>:
    padding: dp(10), dp(8)
    canvas.before:
        Color:
            rgba: (.9, .9, .9, .2) if self.hovered else (1,1,1,0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

<AvatarButton@ButtonBehavior+Image>:
    size_hint: None, None
    size: dp(44), dp(44)

<LoginScreen>:
    name: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(24)
        spacing: dp(12)
        canvas.before:
            Color:
                rgba: 0.95, 0.98, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: 'Welcome to BookShelf'
            font_size: '26sp'
            size_hint_y: None
            height: dp(50)
        GridLayout:
            cols: 1
            size_hint_y: None
            height: dp(220)
            spacing: dp(8)
            TextInput:
                id: login_user
                hint_text: 'Username'
                multiline: False
            TextInput:
                id: login_pass
                hint_text: 'Password'
                password: True
                multiline: False
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(8)
                Button:
                    text: 'Login'
                    on_release: root.do_login(login_user.text, login_pass.text, False)
                Button:
                    text: 'Login as Admin'
                    on_release: root.do_login(login_user.text, login_pass.text, True)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: 'Register'
                on_release: root.manager.transition.direction = 'left'; root.manager.current = 'register'
            Button:
                text: 'Cancel'
                on_release: app.stop()

<RegisterScreen>:
    name: 'register'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(24)
        spacing: dp(12)
        Label:
            text: 'Create account'
            font_size: '22sp'
        TextInput:
            id: reg_user
            hint_text: 'Choose username'
            multiline: False
        TextInput:
            id: reg_pass
            hint_text: 'Choose password'
            password: True
            multiline: False
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: 'Sign Up'
                on_release: root.do_register(reg_user.text, reg_pass.text)
            Button:
                text: 'Back'
                on_release: root.manager.transition.direction = 'right'; root.manager.current = 'login'

<BookItem>:
    index: 0
    title: ''
    author: ''
    size_hint_y: None
    height: dp(72)
    canvas.before:
        Color:
            rgba: (.98, .98, .98, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [6]
    BoxLayout:
        padding: dp(8)
        spacing: dp(8)
        orientation: 'horizontal'
        Image:
            source: 'atlas://data/images/defaulttheme/filechooser_icon'
            size_hint_x: None
            width: dp(48)
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: root.title
                halign: 'left'
                valign: 'middle'
                text_size: self.size
            Label:
                text: root.author
                font_size: '12sp'
                color: .4,.4,.4,1
        Button:
            text: 'Open'
            size_hint_x: None
            width: dp(80)
            on_release: app.open_book(root.genre, root.title)

<BookListScreen>:
    name: 'books'
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: dp(8)
            spacing: dp(8)
            Label:
                text: 'BookShelf'
                font_size: '20sp'
                size_hint_x: None
                width: dp(150)
            TextInput:
                id: search_input
                hint_text: 'Search books...'
                on_text: root.filter_books(self.text)
            Spinner:
                id: genre_spinner
                text: 'All Genres'
                values: root.genre_values
                size_hint_x: None
                width: dp(150)
                on_text: root.change_genre(self.text)
            Widget:
            AvatarButton:
                id: avatar_btn
                source: 'atlas://data/images/defaulttheme/checkbox_on'
                on_release: root.toggle_avatar_menu(self)
        BoxLayout:
            spacing: dp(8)
            padding: dp(8)
            orientation: 'horizontal'
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: None
                width: dp(160)
                Label:
                    text: 'Genres'
                    size_hint_y: None
                    height: dp(30)
                ScrollView:
                    GridLayout:
                        id: genre_list
                        cols: 1
                        size_hint_y: None
                        height: self.minimum_height
                        row_default_height: dp(40)
            BoxLayout:
                orientation: 'vertical'
                RecycleView:
                    id: rv
                    viewclass: 'BookItem'
                    data: []
                    RecycleBoxLayout:
                        default_size: None, dp(80)
                        default_size_hint: 1, None
                        size_hint_y: None
                        height: self.minimum_height
                        orientation: 'vertical'

<BookDetailScreen>:
    name: 'detail'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(8)
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            Button:
                text: '< Back'
                size_hint_x: None
                width: dp(80)
                on_release: root.manager.transition.direction = 'right'; root.manager.current = 'books'
            Label:
                text: root.book_title
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: root.book_author
                size_hint_y: None
                height: dp(30)
            Label:
                text: root.book_desc

<RootScreenManager>:
    # REMOVED: transition: SlideTransition()
    # Kivy will now use the default NoTransition, resolving the NameError.
    LoginScreen:
    RegisterScreen:
    BookListScreen:
    BookDetailScreen:
'''

# ---------- Kivy Widgets / Screens ----------

class LoginScreen(Screen):
    def do_login(self, username, password, admin_only=False):
        username = username.strip()
        password = password.strip()
        if not username or not password:
            App.get_running_app().show_message('Please enter username and password')
            return
        data = load_users()
        for u in data.get('users', []):
            if u['username'] == username and u['password'] == sha256(password):
                if admin_only and not u.get('is_admin'):
                    App.get_running_app().show_message('Not an admin account')
                    return
                app = App.get_running_app()
                app.current_user = username
                app.is_admin = u.get('is_admin', False)
                # Transition is handled in Python when switching to 'books'
                app.root.transition = SlideTransition(direction='left') 
                app.root.current = 'books'
                app.root.get_screen('books').load_books()
                return
        App.get_running_app().show_message('Invalid credentials')


class RegisterScreen(Screen):
    def do_register(self, username, password):
        username = username.strip()
        password = password.strip()
        if not username or not password:
            App.get_running_app().show_message('Enter username & password')
            return
        data = load_users()
        for u in data.get('users', []):
            if u['username'] == username:
                App.get_running_app().show_message('Username already exists')
                return
        new = {'username': username, 'password': sha256(password), 'is_admin': False}
        data['users'].append(new)
        save_users(data)
        App.get_running_app().show_message('Registered! You can now login')
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'


class BookItem(RecycleDataViewBehavior, BoxLayout):
    index = None
    title = StringProperty('')
    author = StringProperty('')
    genre = StringProperty('')


class BookListScreen(Screen):
    genre_values = ListProperty(['All Genres'])
    current_genre = StringProperty('All Genres')

    def on_pre_enter(self):
        Clock.schedule_once(lambda dt: self.setup_avatar(), 0)

    def setup_avatar(self):
        btn = self.ids.get('avatar_btn')
        if not btn:
            return
        dd = DropDown()
        btn._dropdown = dd
        lbl = Button(text='Logout', size_hint_y=None, height=dp(40)) 
        lbl.bind(on_release=self._do_logout)
        dd.add_widget(lbl)

    def toggle_avatar_menu(self, widget):
        if hasattr(widget, '_dropdown'):
            widget._dropdown.open(widget)

    def _do_logout(self, *args):
        app = App.get_running_app()
        app.current_user = None
        app.is_admin = False
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'
        App.get_running_app().show_message('Logged out')

    def load_books(self):
        data = load_books()
        genres = list(data.get('genres', {}).keys())
        self.genre_values = ['All Genres'] + genres
        self.ids.genre_spinner.values = self.genre_values 
        gl = self.ids.genre_list
        gl.clear_widgets()
        for g in genres:
            b = Button(text=g, size_hint_y=None, height=dp(40)) 
            b.bind(on_release=partial(self.change_genre, g))
            gl.add_widget(b)
        self._raw_books = data.get('genres', {})
        self.display_books_from_genre('All Genres')

    def display_books_from_genre(self, genre):
        items = []
        if genre == 'All Genres':
            for g, bl in self._raw_books.items():
                for book in bl:
                    items.append({'title': book['title'], 'author': book.get('author',''), 'genre': g})
        else:
            for book in self._raw_books.get(genre, []):
                items.append({'title': book['title'], 'author': book.get('author',''), 'genre': genre})
        self.ids.rv.data = items

    def filter_books(self, text):
        text = text.strip().lower()
        if not text:
            self.display_books_from_genre(self.current_genre)
            return
        filtered = []
        if self.current_genre == 'All Genres':
            for g, bl in self._raw_books.items():
                for book in bl:
                    if text in book['title'].lower() or text in book.get('author','').lower():
                        filtered.append({'title': book['title'], 'author': book.get('author',''), 'genre': g})
        else:
            for book in self._raw_books.get(self.current_genre, []):
                if text in book['title'].lower() or text in book.get('author','').lower():
                    filtered.append({'title': book['title'], 'author': book.get('author',''), 'genre': self.current_genre})
        self.ids.rv.data = filtered

    def change_genre(self, genre, *args):
        if isinstance(genre, str):
            self.current_genre = genre
        else:
            self.current_genre = genre.text
        self.ids.genre_spinner.text = self.current_genre
        self.display_books_from_genre(self.current_genre)


class BookDetailScreen(Screen):
    book_title = StringProperty('')
    book_author = StringProperty('')
    book_desc = StringProperty('')


class RootScreenManager(ScreenManager):
    pass

# **NOTE:** The original error-causing line from the KV string is now removed.
# The code remains cleaner if Builder.load_string(KV) is placed before the App class definition,
# as shown in the last attempt, but to follow your original structure while removing the component:

class BookApp(App):
    current_user = StringProperty(None)
    is_admin = BooleanProperty(False)

    def build(self):
        ensure_books_file()
        ensure_users_file()
        self.icon = None
        # The Builder must load the KV string before RootScreenManager is instantiated.
        # This placement is still technically risky, but works if the KV definition
        # doesn't rely on global factory references before this point.
        Builder.load_string(KV) 
        sm = RootScreenManager()
        return sm

    def show_message(self, text):
        print(text)

    def open_book(self, genre, title):
        books = load_books().get('genres', {})
        for b in books.get(genre, []):
            if b['title'] == title:
                s = self.root.get_screen('detail')
                s.book_title = b['title']
                s.book_author = 'by ' + b.get('author', '')
                s.book_desc = b.get('desc', '')
                # Note: FadeTransition is still used in Python
                self.root.transition = FadeTransition(direction='left')
                self.root.current = 'detail'
                return
        self.show_message('Book not found')


if __name__ == '__main__':
    BookApp().run()