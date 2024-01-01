import datetime
import os.path
import os
import time
# import pygame
import sys
import threading
import time
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock, mainthread
from kivy.uix.popup import Popup
from  kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.audio import SoundLoader



from queue import Queue

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

kivy.require("2.2.1")

# Permssions needed to access Google Calendar
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
# initialize pygame mixer

 
# Get Calendar ID from file



class MainScreen(Screen):
    def __init__(self, app, **kwargs): 
        super(MainScreen, self).__init__(**kwargs)
        self.app = app
        self.add_widget(self.app.create_main_layout())


class SettingsScreen(Screen):
    def __init__(self, app, **kwargs): 
        super(SettingsScreen, self).__init__(**kwargs)
        self.app = app
        self.settings_layout = self.app.create_settings_layout()
        self.add_widget(self.settings_layout)
                
    def on_pre_enter(self, *args):
        calendar_id = self.app.get_calendar_id()
        volume_level = self.app.get_stored_volume()
        
        
        self.app.calendar_id_input.text = calendar_id if calendar_id else ""
        self.app.volume_input.text = str(volume_level) if volume_level else ""
        
class DevModeScreen(Screen):
    def __init__(self, app, **kwargs):
        super(DevModeScreen, self).__init__(**kwargs)
        self.app = app
        self.DevMode_layout = self.app.create_DevMode_layout()
        self.add_widget(self.DevMode_layout)
    
        

class CalendarAlarmApp(App):

        def create_main_layout(self):
                
                layout = BoxLayout(orientation="vertical")
                
                self.header_label = Label(text="Main View", size_hint_y=0.1)
                layout.add_widget(self.header_label)
                
                self.event_label = Label(text="No Events", size_hint_y=0.7)
                layout.add_widget(self.event_label)
                
                stop_button = Button(text="Stop Alarm", size_hint_y=0.1)
                stop_button.bind(on_press=self.stop_alarm)
                layout.add_widget(stop_button)
                

                toggle_button = Button(text="Go to Settings", size_hint_y=0.1)
                toggle_button.bind(on_press=self.toggle_layout)
                layout.add_widget(toggle_button)
                
                return layout
            
        def create_settings_layout(self):
            layout = BoxLayout(orientation="vertical")
            
            self.header_label = Label(text="Settings View", size_hint_y=0.1)
            layout.add_widget(self.header_label)
            
            self.calendar_id_input = TextInput(hint_text="Enter Calendar ID", size_hint_y=0.1)
            save_calendar_id_button = Button(text="Save Calendar ID", size_hint_y=0.1)          
            save_calendar_id_button.bind(on_press=self.save_calendar_id)
            
                                    
            self.volume_input = TextInput(hint_text="Enter volume 0.0 - 1.0", size_hint_y=0.1)   
            save_volume_button = Button(text="Save Volume", size_hint_y=0.1)
            save_volume_button.bind(on_press=self.save_volume)
 

            self.refetch_button = Button(text="Refetch Events", size_hint_y=0.3)
            self.refetch_button.bind(on_press=self.refetch_events)

            toggle_button = Button(text="Go to Dev Mode", size_hint_y=0.1)
            toggle_button.bind(on_press=self.toggle_layout)
            



            layout.add_widget(self.calendar_id_input)
            layout.add_widget(save_calendar_id_button)
            layout.add_widget(self.volume_input)
            layout.add_widget(save_volume_button)
            layout.add_widget(self.refetch_button)
        
            layout.add_widget(toggle_button)
                
            return layout
        
        def create_DevMode_layout(self):
            layout = BoxLayout(orientation="vertical")
            
            self.log_view = TextInput(text="log initialized.../n", readonly=True, background_color=(1,0,0,1), foreground_color=(1,1,1,1), size_hint_y=0.8)
            
            self.pause_button= Button(text="Pause Log", size_hint_y=0.1)
            self.pause_button.bind(on_press=self.toggle_pause)    
            
            layout.add_widget(self.log_view)            
            layout.add_widget(self.pause_button)
            
            
            toggle_button = Button(text="Go to Main", size_hint_y=0.1)
            toggle_button.bind(on_press=self.toggle_layout)
            layout.add_widget(toggle_button)
            
            return layout
        

        def build(self):
            self.log_paused = False

            self.alarm_sound = None
            self.set_volume(self.get_stored_volume())
            self.log_message("Kivy sound initialized")
            
            try:         
                self.service = self.initialize_google_service()
                self.log_message("Google Service Initialized")
            except Exception as e:
                self.log_message(f"Error initializing google service: {e}")
            self.event_queue = Queue()
            self.screen_manager = ScreenManager()
            
            self.main_screen = MainScreen(self, name="Main")
            self.settings_screen = SettingsScreen(self, name="Settings")
            self.DevMode_screen = DevModeScreen(self, name="DevMode")
            
            self.screen_manager.add_widget(self.main_screen)
            self.screen_manager.add_widget(self.settings_screen)
            self.screen_manager.add_widget(self.DevMode_screen)
            
            return self.screen_manager
        
            
        def switch_to_settings(self):
            self.settings_screen.calendar_id_input.text = f"Enter Calendar ID. Current ID: {self.get_calendar_id()}"
            self.settings_screen.volume_input.text = f"Enter volume 0.0 - 1.0. Current volume: {self.get_stored_volume()}"    
       
            self.screen_manager.current = "Settings"
        
        def switch_to_main(self):
            self.screen_manager.current = "Main"
            
        def switch_to_DevMode(self):
            self.screen_manager.current = "DevMode"
                        
           

        def toggle_layout(self, instance):
            if self.screen_manager.current == "Main":
                self.screen_manager.current = "Settings"
            elif self.screen_manager.current == "Settings":
                self.screen_manager.current = "DevMode"
            else:
                self.switch_to_main()
            
            
            self.update_event_label()
            Clock.schedule_interval(self.update_event_label, 5)
                    

        def save_calendar_id(self, instance):
            with open("CalendarID.txt", "w") as calendar_id_file:
                calendar_id_file.write(self.calendar_id_input.text)
            self.log_message(f"Calendar ID saved: {self.calendar_id_input.text}")
            
        def save_volume(self, instance):
            try:
                volume = float(self.volume_input.text)
                with open("Settings/volume_setting.txt", "w") as volume_file:
                    volume_file.write(str(volume))
                self.log_message(f"Volume saved: {volume}")

                # Apply the new volume setting immediately
                self.set_volume(volume)

            except ValueError:
                self.log_message(f"Invalid volume: {self.volume_input.text}")

        
        def load_settings(self):
            try:
                with open("calendar_id.txt", "r") as calendar_id_file:
                    self.calendar_id_input.text = calendar_id_file.read()
                with open("Settings/volume_setting.txt", "r") as volume_file:
                    self.volume_input.text = volume_file.read()
            except FileNotFoundError:
                self.log_message("Settings files not found")
        
        
        def on_start(self):
            super().on_start()
            self.load_settings()
            self.fetch_and_update_events()
            try:
                self.start_event_check_thread()
                self.log_message("Event check thread called from on_start successfully")
            except Exception as e:
                self.log_message(f"Error starting event check thread from on_start: {e}")
            self.log_message("Event check thread started")
            self.update_event_label()
            self.log_message("update_event_label method called from on_start")
            self.log_message("on_start method completed")
        
        @mainthread
        def log_message(self, message):
            """ Append Message to log view """
            if not self.log_paused:
                if hasattr(self, "log_view"):
                    self.log_view.text += message + "\n"
                else:
                    print("log_view not initialized:", message)
        
        def toggle_pause(self, instance):
            """ Toogle the pause state of the log """
            self.log_paused = not self.log_paused
            self.pause_button.text = "Resume Log" if self.log_paused else "Pause Log"
        
        def initialize_google_service(self):
            creds = None
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json", SCOPES)
                    creds = flow.run_local_server(port=0)
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
            return build("calendar", "v3", credentials=creds)
            
        def start_event_check_thread(self):
            try:
                self.log_message("Starting event check thread")
                event_thread = threading.Thread(target=self.check_events, args=(self.service, self.event_queue), daemon=True)
                event_thread.start()    
                self.log_message("Event check thread started successfully")
                
                if event_thread.is_alive():
                    self.log_message("Event check thread is running")
                else:
                    self.log_message("Event check thread is not running")
                    
            except Exception as e:
                self.log_message(f"Error starting event check thread: {e}")
            
            
        def update_event_label(self, *args):
            self.log_message("Attempt to update event label")
            if not self.event_queue.empty():
                events = self.event_queue.get()
                event_texts = []
                for event in events:
                    summary = event.get('summary', 'No title')
                    start = event['start'].get('dateTime', event['start'].get('date','No Start Time'))
                    event_info = f"{summary} at {start}"
                    event_texts.append(event_info)
                self.event_label.text = "\n".join(event_texts) if event_texts else "No Events"
                self.log_message("Event label updated")
        
        def show_confirmation_popup(self, confirm_callback):
            box = BoxLayout(orientation='vertical', spacing=10, padding=10)
            box.add_widget(Label(text="Are you sure you want to refetch events?"))
            
            btn_layout = BoxLayout(orientation="horizontal", spacing=10)
            yes_button = Button(text="Yes")
            yes_button.bind(on_press=lambda x: self.dismiss_popup(confirm_callback))
            btn_layout.add_widget(yes_button)
            
            no_button = Button(text="No")
            no_button.bind(on_press=lambda x: self.dismiss_popup())
            btn_layout.add_widget(no_button)
            
            
            box.add_widget(btn_layout)
                        
            self.popup = Popup(title="Confirm Refetch",
                                    content=box,
                                    size_hint=(None, None),
                                    size=(400, 200))
            self.popup.open()
            
        def dismiss_popup(self, confirm_callback=None):
            if confirm_callback:
                confirm_callback()
            self.popup.dismiss()       
       
       
        def refetch_events(self, instance):
        # Logic to refetch events
            self.show_confirmation_popup(self.perform_refetch)

        def perform_refetch(self):
            try:
                
                events = self.fetch_events(self.service)
                if events:
                    self.event_queue.put(events)
                    self.log_message("Events refetched successfully")
                else:
                    self.log_message("No events fetched")
            except Exception as e:
                self.log_message(f"Error in perform_refetch: {e}")
        
        def play_alarm_sound(self, sound_file, volume=None):
            try:
                self.log_message("Attempting to load sound")
                self.alarm_sound = SoundLoader.load(sound_file)
                if self.alarm_sound:
                    if volume is not None:
                        self.alarm_sound.volume = volume
                    else:
                        self.alarm_sound.volume = self.get_stored_volume()

                    self.alarm_sound.loop = True
                    self.log_message("Attempting to play sound")
                    self.alarm_sound.play()
                    self.log_message("Sound played successfully")
            except Exception as e:
                self.log_message(f"Error playing sound: {e}")



        def stop_alarm(self, instance):
            if self.alarm_sound:
                self.log_message("Attempting to stop alarm")
                self.alarm_sound.stop()
                self.log_message("Alarm stopped successfully")

        # Function for stopping alarm 

                
        def set_volume(self, volume_level=None):
            if volume_level is None:
                volume_level = self.get_stored_volume()
            else:
                with open("Settings/volume_setting.txt", "w") as file:
                    file.write(str(volume_level))

            if self.alarm_sound:
                self.alarm_sound.volume = volume_level
            else:
                # Load a default sound file with the specified volume if not already loaded
                self.play_alarm_sound("Assets/Alarm_sound.mp3", volume_level)
                self.alarm_sound.stop()  # Stop it immediately as it's for volume setting purpose

            self.log_message(f"Volume set to {volume_level}")
    



        def get_calendar_id(self):
            try:
                with open("CalendarID.txt", "r") as file:
                    return file.read().strip()
            except Exception as e:
                return ""


        def get_stored_volume(self):
            try:
                with open("Settings/volume_setting.txt", "r") as file:
                    volume = float(file.read().strip())
                    print(f"Read volume: {volume}")
                    return volume
            except Exception as e:
                print(f"Error reading volume setting: {e}")
                return 0.5 # default volume


        # Function for updating volume
        def update_volume(self):
            volume_level = self.get_stored_volume()
            self.log_message(f"Updating volume to {volume_level}")
            if self.alarm_sound:
                self.alarm_sound.volume = volume_level

            
        # Function for checking events using fetch_events()
        def check_events(self, service, event_queue):
            self.log_message("Entered check_events method")
            try:
                last_fetch_time = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
                fetch_inverval = datetime.timedelta(minutes=10)
                check_interval = 15 # 0.25 minute
                events = []

                
                while True:
                    try:
                        
                        now = datetime.datetime.now(datetime.timezone.utc)
                        self.update_volume()
                        
                        if now - last_fetch_time >= fetch_inverval:
                            self.log_message("Fetching events in check_events")
                            events = self.fetch_events(service)
                            if events:
                                event_queue.put(events)
                                self.log_message(f"{len(events)} events fetched successfully")
                            else:
                                self.log_message("No new events to fetch")
                            
                            last_fetch_time = now
                        try:    
                            for event in events:
                                start_str = event["start"].get("dateTime", event["start"].get("date"))
                                start = datetime.datetime.fromisoformat(start_str)
                                self.log_message(f"Current time: {now}, Event start time: {start}")
                                if now >= start:
                                    self.log_message(f"Event: {event.get('summary')} is due. Attempting to play alarm sound")
                                    try:

                                        self.play_alarm_sound("Assets/Alarm_sound.mp3")
                                    except Exception as e:
                                        self.log_message(f"Error in playing alarm sound for event {event.get('summary')}: {e}")
                                    events.remove(event)
                        except Exception as e:
                            self.log_message(f"Error inside check_events: {e}")

                        time.sleep(check_interval)
                    except Exception as e:
                        self.log_message(f"Error in checking events: {e}")
                        time.sleep(check_interval)
            except Exception as e:
                self.log_message(f"Unexpected error in check_events: {e}")

        # Function for fetching events
        def fetch_events(self, service):
            try:
                now = datetime.datetime.utcnow().isoformat() + "Z"
                self.log_message(f"Fetching events after {now}")
                
                calendar_id = self.get_calendar_id()
                self.log_message(f"Using Calendar ID: {calendar_id}")
                
                event_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
                
                events = event_result.get("items", [])
                for event in events:
                    self.log_message(f"Event: {event.get('summary')} at {event.get('start').get('dateTime'), event.get('start').get('date')}")
                
                if not events:
                    self.log_message("No events found")
                    
                return events
            except Exception as e:
                self.log_message(f"Error fetching events: {e}")
                return []
            
        def fetch_and_update_events(self):
            try:
                events = self.fetch_events(self.service)
                if events:
                    self.event_queue.put(events)
                    self.log_message("Events fetched successfully on startup")
                
                else:
                    self.log_message("No events found on startup")
            except Exception as e:
                self.log_message(f"Error fetching events on startup: {e}")


if __name__ == "__main__":
    CalendarAlarmApp().run()
  
