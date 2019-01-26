# Standard Library Imports
import os.path
import queue
import threading

# Third Party Imports
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder

# Local Imports
import client.source.ui.screens as screens
from client.source.client_protocol import ClientProtocol

KV_FILE = 'client.kv'
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


def load_kv_file(kv):
    """Loads master kv file in ./kv"""
    # Workaround because kivy had trouble with relative paths
    os.chdir("kv")
    Builder.load_file(kv)
    os.chdir("..")


class ClientApp(App):

    def on_stop(self):
        """Tell server the client closed unexpectedly"""
        print("I stopped!")
        self.client_protocol.send_closed_command()
        quit()

    def build(self):
        """Start main loop"""
        thread_shared_data = queue.Queue()
        self.client_protocol = ClientProtocol(thread_shared_data)
        self.client_protocol.run_listener_thread()

        print('Loading interface...')
        load_kv_file(KV_FILE)
        return screens.RootScreen(client_protocol=self.client_protocol)


if __name__ == "__main__":
    ClientApp().run()


# TODO: Move exit function to a global scale instead of class scale (does nothing at the moment)
# TODO: Make chat screen pretty