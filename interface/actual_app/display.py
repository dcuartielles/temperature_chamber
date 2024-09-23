from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class RealTimeDisplay(BoxLayout):
    def __init__(self, **kwargs):
        super(RealTimeDisplay, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        # create label to display data
        self.label = Label(text="waiting for data...", font_size='20sp')
        self.add_widget(self.label)

    def update_label(self, text):
        self.label.text = text
