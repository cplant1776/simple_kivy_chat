from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty


class UserButton(Button):
    def __init__(self, **kwargs):
        super(Button, self).__init__(**kwargs)
        self.on_touch_down = self.mouse_click

    def mouse_click(self, touch):
        if self.collide_point(touch.x, touch.y):
            if touch.button == 'left':
                self.popup = PopMenu(touch, name=self.text)
                self.popup.open()


class PopMenu(object):
    context_menu = ObjectProperty()

    def __init__(self, touch, name):
        context_menu = ContextMenu()
        self.popup = PopModal(touch, name)
        self.popup.add_widget(context_menu)
        # self.add_widget(ContextMenu)

    def open(self):
        self.popup.open()


class ContextMenu(BoxLayout):
    def __init__(self, **kwargs):
        super(ContextMenu, self).__init__(**kwargs)


class PopModal(ModalView):
    touch = ObjectProperty()

    def __init__(self, touch, name, **kwargs):
        super(ModalView, self).__init__(**kwargs)
        self.touch = touch
        self.name = name



