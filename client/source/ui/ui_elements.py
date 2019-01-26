# Standard Library Imports

# Third Party Imports
from kivy.uix.label import Label
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.scrollview import ScrollView

# Local Imports


class ScrollableLabel(ScrollView):
    text = StringProperty('INITIAL')


class ChatLabel(Label):
    pass
