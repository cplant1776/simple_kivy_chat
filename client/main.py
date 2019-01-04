from kivy.app import App
from kivy.lang import Builder
import os.path
import client.source.ui.screens as screens
from client.source.client_protocol import ClientProtocol
import threading
import queue
from kivy.config import Config

KV_FILE = 'client.kv'
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

def load_kv_file(kv):
    # Workaround because kivy had trouble with relative paths
    os.chdir("kv")
    Builder.load_file(kv)
    os.chdir("..")


class ClientApp(App):

    def on_stop(self):
        print("I stopped!")
        self.client_protocol.send_closed_command()

    def build(self):
        thread_shared_data = queue.Queue()
        self.client_protocol = ClientProtocol(thread_shared_data)
        self.client_protocol.run_listener_thread()

        print('Loading interface...')
        load_kv_file(KV_FILE)
        return screens.RootScreen(client_protocol=self.client_protocol)


if __name__ == "__main__":
    ClientApp().run()
