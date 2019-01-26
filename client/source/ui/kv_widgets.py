# Standard Library Imports

# Third Party Imports
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView

# Local Imports


class ModalPopupButton(Button):
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


class SubmissionPopup(ModalView):
    def __init__(self, **kwargs):
        super(ModalView, self).__init__(**kwargs)


class FailedSubmissionPopup(ModalView):
    def __init__(self, message, **kwargs):
        super(ModalView, self).__init__(**kwargs)
        self.ids.failed_submission_label.text = message


class ServerShutdownPopup(ModalView):
    def __init__(self, **kwargs):
        super(ModalView, self).__init__(**kwargs)

    def on_dismiss(self):
        self.quit()


class SubmissionButton(Button):
    pass



