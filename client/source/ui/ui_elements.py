from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import StringProperty, ObjectProperty


class ScrollableLabel(ScrollView):
    text = StringProperty('INITIAL')


class ChatLabel(Label):
    pass
