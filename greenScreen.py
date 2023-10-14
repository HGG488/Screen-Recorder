import numpy as np
from tkinter import filedialog
import tkinter as tk
import cv2
from PIL import Image, ImageTk
from tkinter import ttk
import pyautogui
import time
import threading

import os
import pygetwindow as gw
import pyaudio
import wave
class WebcamApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Webcam App")

        self.video_label = tk.Label(root)  # width=
        self.video_label.grid(row=0, column=0, rowspan=8, columnspan=4, padx=10, pady=10)

        self.capture_button = tk.Button(root, text="Start Capture", command=self.start_capture)
        self.capture_button.grid(row=0, column=4, columnspan=1, padx=10, pady=10)

        self.stop_button = tk.Button(root, text="Stop Capture", command=self.stop_capture, state=tk.DISABLED)
        self.stop_button.grid(row=1, column=4, columnspan=1, padx=10, pady=5)

        self.record_button = tk.Button(root, text="Record", command=self.toggle_record)
        self.record_button.grid(row=2, column=4, columnspan=1, padx=10, pady=10)

        self.load_button = tk.Button(root, text="Load Backround", command=self.load_image)
        self.load_button.grid(row=3, column=4, columnspan=1, padx=10, pady=10)

        self.webcamOn = tk.BooleanVar()
        self.webcam_CB = tk.Checkbutton(root, text="Webcam", variable=self.webcamOn, command=self.webcamChange)
        self.webcam_CB.grid(row=4, column=4, columnspan=1, padx=10, pady=10)

        self.greenScreenOn = tk.BooleanVar()
        self.greenScreen_CB = tk.Checkbutton(root, text="GreenScreen", variable=self.greenScreenOn,
                                             command=self.greenScreenChange)
        self.greenScreen_CB.grid(row=5, column=4, columnspan=1, padx=10, pady=10)

        self.transparentOn = tk.BooleanVar()
        self.transparent_CB = tk.Checkbutton(root, text="Transparent Backround", variable=self.transparentOn)
        self.transparent_CB.grid(row=6, column=4, columnspan=1, padx=10, pady=10)

        self.audioOn = tk.BooleanVar()
        self.audio_CB = tk.Checkbutton(root, text="Audio", variable=self.audioOn)
        self.audio_CB.grid(row=7, column=4, columnspan=1, padx=10, pady=10)

        self.color_var = tk.StringVar()
        self.result_label = tk.Label(root, text="Color:")
        self.result_label.grid(row=8, column=0, padx=10, pady=5)

        self.color_dropdown = ttk.Combobox(root, textvariable=self.color_var,
                                           values=["Red", "Blue", "Green", "Yellow", "Purple", "Black", "White"],
                                           state="readonly")
        self.color_dropdown.grid(row=9, column=0, padx=10, pady=5)

        self.color_dropdown.bind("<<ComboboxSelected>>", self.update_hsv_range)

        self.screen_var = tk.StringVar()
        self.screen_label = tk.Label(root, text="Capture:")
        self.screen_label.grid(row=8, column=1, padx=10, pady=5)

        self.screen_dropdown = ttk.Combobox(root, textvariable=self.screen_var,
                                            values=["Entire Screen", "Specified Window"],
                                            state="readonly")
        self.screen_dropdown.grid(row=9, column=1, padx=10, pady=5)
        self.screen_dropdown.bind("<<ComboboxSelected>>", self.windowsChange)

        self.windows_var = tk.StringVar()
        self.windows_label = tk.Label(root, text="Windows:")
        self.windows_label.grid(row=8, column=2, padx=10, pady=5)
        self.windows =  list(filter(str.strip, gw.getAllTitles()))


        self.windows_dropdown = ttk.Combobox(root, textvariable=self.windows_var,
                                             values=self.windows,
                                             state="readonly")
        self.windows_dropdown.grid(row=9, column=2, padx=10, pady=5)

        self.position_var = tk.StringVar()
        self.position_label = tk.Label(root, text="Webcam Position:")
        self.position_label.grid(row=8, column=3, padx=10, pady=5)
        self.positions = ["top-left", "top-right", "bottom-left", "bottom-right"]
        self.positions_dropdown = ttk.Combobox(root, textvariable=self.position_var,
                                               values=self.positions,
                                               state="readonly")
        self.positions_dropdown.grid(row=9, column=3, padx=10, pady=5)

        self.screenshot_button = tk.Button(root, text="Take a Screenshot", command=self.take_screenshot)
        self.screenshot_button.grid(row=8, column=4, padx=10, pady=10)

        self.save_button = tk.Button(root, text="Change Saving Directory", command=self.change_saving_directory)
        self.save_button.grid(row=9, column=4, padx=70, pady=10)

        self.lower_bound = np.array([30, 20, 20])
        self.upper_bound = np.array([95, 255, 255])
        self.backround = None
        self.cap = None
        self.is_capturing = False
        self.recording = False
        self.out = None
        self.audioOn.set(False)  # Set the default value of the audio checkbox to False

        # Create an instance of PyAudio for audio recording
        self.audio = pyaudio.PyAudio()
        self.audio_stream = None
        self.start_time = 0
        self.update_timer_thread = threading.Thread(target=self.update_timer)
        self.update_timer_thread.daemon = True
        self.update_timer_thread.start()
        self.color_var.set("Green")  # Set default color value
        self.screen_var.set("Entire Screen")
        self.windows_var.set("Webcam App")
        self.position_var.set("top-left")
        self.greenScreenOn.set(False)
        self.webcamOn.set(False)
        self.color_dropdown.config(state=tk.DISABLED)
        self.greenScreen_CB.config(state=tk.DISABLED)
        self.transparent_CB.config(state=tk.DISABLED)
        self.positions_dropdown.config(state=tk.DISABLED)
        self.windows_dropdown.config(state=tk.DISABLED)
        self.load_button.config(state=tk.DISABLED)
        self.record_button.config(state=tk.DISABLED)
        self.screenshot_button.config(state=tk.DISABLED)
        self.update_hsv_range(self)  # Update HSV range initially
        self.SCREEN_SIZE = tuple(pyautogui.size())
        self.IMAGE_SIZE = ((self.SCREEN_SIZE[0] // 4 * 3) // 4 * 3), ((self.SCREEN_SIZE[1] // 4 * 3) // 4 * 3)
        self.blank_frame = np.zeros((self.IMAGE_SIZE[1], self.IMAGE_SIZE[0], 3), dtype=np.uint8)
        self.blank_photo = ImageTk.PhotoImage(image=Image.fromarray(self.blank_frame))
        self.video_label.config(image=self.blank_photo)
        self.video_label.image = self.blank_photo
        self.screenshot=None
        self.save_path=os.getcwd()
        self.NOTHING = 0

        self.ENTIRE_SCREEN = 1
        self.CERTAIN_WINDOW = 2
        self.captureState = self.ENTIRE_SCREEN
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.audio_settings = {
            'channels': 2,  # Mono audio
            'rate': 48000,  # Sample rate (Hz)
            'frames_per_buffer': 1024,
            'format': pyaudio.paInt16
        }



    def toggle_record(self):
        if not self.recording:
            if self.audioOn.get():
                self.start_audio_recording()
            self.start_recording()

        else:
            self.stop_recording()
            # if self.audioOn.get():
            #     self.stop_audio_recording()

    def start_audio_recording(self):
        print("start audio")
        if not self.audio_stream and self.audioOn.get():

            audio_format = pyaudio.paInt16  # Adjust as needed
            channels = 2  # Adjust as needed
            sample_rate = 48000  # Adjust as needed
            chunk_size = 1024  # Adjust as needed

            self.audio_stream = self.audio.open(
                format=audio_format,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=8,
                output_device_index=1,
                frames_per_buffer=chunk_size
            )

        if self.audio_stream is not None:
            self.audio_frames = []

    def stop_audio_recording(self):
        if self.audio_stream:
            print("daaa wa")
            self.save_audio()
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None

    def change_saving_directory(self):
        new_directory = filedialog.askdirectory()
        if new_directory:
            self.save_path = new_directory
    def update_button_text(self, text="Record"):
        self.record_button.configure(text=text)
    def start_recording(self):
        print(self.SCREEN_SIZE)
        self.out = cv2.VideoWriter(self.save_path+'/output.avi', cv2.VideoWriter_fourcc(*'XVID'), 20.0, (self.IMAGE_SIZE[0], self.IMAGE_SIZE[1]))
        self.recording = True
        self.start_time = time.time()
        self.record_button.config(text="Stop Recording")

    def stop_recording(self):
        if self.recording:
            self.recording = False

            self.out.release()

            if self.audioOn.get():
                self.stop_audio_recording()
            # input_video_path = self.save_path + '/output.avi'
            # input_audio_path = self.save_path + '/audio.wav'
            # output_path = self.save_path + '/output1.mp4'
            # ffmpeg_command = [
            #     'ffmpeg',
            #     '-i', input_video_path,
            #     '-i', input_audio_path,
            #     '-c:v', 'copy',
            #     '-c:a', 'aac',
            #     '-strict', 'experimental',
            #     output_path
            # ]
            #
            # subprocess.run(ffmpeg_command, check=True)
            #
            # # Clean up temporary files
            # os.remove(input_video_path)
            # os.remove(input_audio_path)


            self.record_button.config(text="Record")
            self.audio_frames = []



            # input_path = self.save_path+'/output.avi'  # Replace with your input AVI file path
            # output_path = self.save_path+'/output.mp4'  # Replace with your desired output MP4 file path

            #self.convert_avi_to_mp4(input_path, output_path)
            #os.remove(self.save_path + '/output.avi')

    # def convert_avi_to_mp4(self,input_path, output_path):
    #     try:
    #         # Use FFmpeg to convert the video
    #         path=r"C:\Users\georg\AppData\Local\Programs\Python\Python310\Lib\site-packages"
    #         command = [path, '-i', input_path, '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', '-strict',
    #                    'experimental', output_path]
    #         subprocess.run(command, check=True)
    #         print("Conversion successful!")
    #     except subprocess.CalledProcessError as e:
    #         print("Error during conversion:", e)
    def save_audio(self):
        if self.audio_frames:
            file_path = os.path.join(self.save_path, 'audio.wav')
            try:
                with wave.open(file_path, 'wb') as wf:
                    wf.setnchannels(self.audio_settings['channels'])
                    wf.setsampwidth(self.audio.get_sample_size(self.audio_settings['format']))
                    wf.setframerate(self.audio_settings['rate'])
                    wf.writeframes(b''.join(self.audio_frames))
                print(f"Audio saved to {file_path}")
            except Exception as e:
                print(f"Error saving audio: {e}")
    def update_timer(self):
        while True:
            if self.recording:
                elapsed_time = int(time.time() - self.start_time)
                self.update_button_text(f"Recording: {elapsed_time} sec")
            time.sleep(1)
    def take_screenshot(self):
        if self.is_capturing:
            cv2.imwrite(self.save_path+"/image.png",cv2.cvtColor(self.screenshot,cv2.COLOR_BGR2RGB))


    def start_capture(self):

        self.is_capturing = True
        self.record_button.config(state=tk.NORMAL)
        self.capture_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.screenshot_button.config(state=tk.NORMAL)

        self.update_video()

    def update_hsv_range(self, event):
        color_name = self.color_var.get()
        hsv_ranges = {
            "Red": ((0, 25, 25), (10, 255, 255)),
            "Blue": ((80, 25, 25), (130, 255, 255)),
            "Green": ((35, 25, 25), (80, 255, 255)),
            "Yellow": ((13, 20, 20), (35, 255, 255)),
            "Purple": ((125, 25, 25), (160, 255, 255)),
            "Black": ((0, 0, 0), (180, 255, 30)),
            "White": ((0, 0, 231), (180, 18, 255))
        }

        self.lower_bound, self.upper_bound = np.array(hsv_ranges[color_name])

    def stop_capture(self):
        self.is_capturing = False

        self.record_button.config(state=tk.NORMAL)

        self.capture_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.screenshot_button.config(state=tk.DISABLED)
        self.video_label.config(image=None)

    def update_video(self):

        if self.is_capturing:
            mask = np.zeros((640, 480, 3), dtype=np.uint8)
            window = gw.getWindowsWithTitle(self.windows_var.get())[0]
            if self.screen_var.get()=="Specified Window" and window.isActive:



                left, top, width, height = window.left, window.top, window.width, window.height

                print(self.windows_var.get())

                img = pyautogui.screenshot(region=(left, top, width, height))
                img = np.array(img)
                img = cv2.resize(img, (self.IMAGE_SIZE[0], self.IMAGE_SIZE[1]))


            else:

                img = pyautogui.screenshot()
                img = np.array(img)
                img = cv2.resize(img, (self.IMAGE_SIZE[0], self.IMAGE_SIZE[1]))

            if self.webcamOn.get():
                ret, frame = self.cap.read()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hsv_image = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
                if self.greenScreenOn.get():
                    mask = cv2.inRange(hsv_image, self.lower_bound, self.upper_bound)
                    if self.color_var.get() == "Red":
                        mask1 = cv2.inRange(hsv_image, np.array([175, 25, 25]), np.array([180, 255, 255]))
                        mask = mask + mask1
                    if not self.transparentOn.get():
                        if self.backround is not None:
                            self.backround = cv2.resize(self.backround, (frame.shape[1], frame.shape[0]))
                            frame[mask == 255] = self.backround[mask == 255]


                frame = cv2.resize(frame, (self.SCREEN_SIZE[0] // 5, self.SCREEN_SIZE[1] // 4))
                fr_height, fr_width, _ = frame.shape

            if self.webcamOn.get():
                if self.transparentOn.get():
                    mask = cv2.resize(mask, (self.SCREEN_SIZE[0] // 5, self.SCREEN_SIZE[1] // 4))
                    mask_height, mask_width = mask.shape
                    img1 = img.copy()
                    mask1 = np.zeros((self.IMAGE_SIZE[1], self.IMAGE_SIZE[0]), dtype=np.uint8)
                    match self.position_var.get():
                        case "top-left":
                            mask1[0:mask_height, 0: mask_width] = mask[0:mask_height, 0: mask_width]
                            img[0:fr_height, 0: fr_width, :] = frame[0:fr_height, 0: fr_width, :]
                        case "top-right":
                            mask1[0:mask_height:,self.IMAGE_SIZE[0]- mask_width:] = mask[0:mask_height,  0:mask_width]
                            img[0:fr_height, self.IMAGE_SIZE[0]-fr_width:, :] = frame[0:fr_height,  0:fr_width, :]
                        case "bottom-left":
                            mask1[self.IMAGE_SIZE[1]-mask_height:, 0: mask_width] = mask[0:mask_height, 0: mask_width]
                            img[self.IMAGE_SIZE[1]-fr_height:, 0: fr_width, :] = frame[0:fr_height, 0: fr_width, :]
                        case "bottom-right":
                            mask1[self.IMAGE_SIZE[1]-mask_height:, self.IMAGE_SIZE[0]-mask_width:] = mask[0:mask_height,0: mask_width]
                            img[self.IMAGE_SIZE[1]-fr_height:, self.IMAGE_SIZE[0]-fr_width:, :] = frame[0:fr_height, 0: fr_width, :]
                    img[mask1 == 255] = img1[mask1 == 255]

                else:
                    match self.position_var.get():
                        case "top-left":

                            img[0:fr_height, 0: fr_width, :] = frame[0:fr_height, 0: fr_width, :]
                        case "top-right":

                            img[0:fr_height,self.IMAGE_SIZE[0]-fr_width:, :] = frame[0:fr_height, 0:fr_width, :]
                        case "bottom-left":

                            img[self.IMAGE_SIZE[1]-fr_height:, 0: fr_width, :] = frame[0:fr_height, 0: fr_width, :]
                        case "bottom-right":

                            img[self.IMAGE_SIZE[1]-fr_height:,self.IMAGE_SIZE[0]- fr_width:, :] = frame[0:fr_height,0: fr_width, :]


            if self.recording:

                img1=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                self.out.write(img1)
                if self.audioOn.get():
                    if self.audio_stream.read :
                        audio_data = self.audio_stream.read(1024)
                        self.audio_frames.append(audio_data)
            self.screenshot=img
            photo = ImageTk.PhotoImage(image=Image.fromarray(img))
            self.video_label.config(image=photo)
            self.video_label.image = photo
            delay = 33


        else:

            self.video_label.config(image=self.blank_photo)
            self.video_label.image = self.blank_photo
            delay = 33
        self.root.after(delay, self.update_video)  # Update every 10 milliseconds

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if file_path:
            self.backround = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)

    def on_closing(self):
        if self.cap is not None:
            self.cap.release()
        if self.out is not None:
            self.out.release()

        cv2.destroyAllWindows()
        self.root.destroy()

    def webcamChange(self):
        if self.webcamOn.get():
            self.cap = cv2.VideoCapture(0)
            self.greenScreen_CB.config(state=tk.NORMAL)


            if self.greenScreenOn.get():
                self.color_dropdown.config(state="readonly")
            self.positions_dropdown.config(state="readonly")

        else:
            self.greenScreen_CB.config(state=tk.DISABLED)
            self.transparent_CB.config(state=tk.DISABLED)
            self.load_button.config(state=tk.DISABLED)
            self.color_dropdown.config(state=tk.DISABLED)
            self.positions_dropdown.config(state=tk.DISABLED)
            self.greenScreenOn.set(False)
            self.transparentOn.set(False)
            self.cap.release()

    def greenScreenChange(self):
        if self.greenScreenOn.get():
            self.color_dropdown.config(state="readonly")
            self.load_button.config(state=tk.NORMAL)
            self.transparent_CB.config(state=tk.NORMAL)
        else:
            self.color_dropdown.config(state=tk.DISABLED)
            self.load_button.config(state=tk.DISABLED)
            self.transparent_CB.config(state=tk.DISABLED)

    def windowsChange(self, event):
        if self.screen_var.get() == "Specified Window":
            self.windows_dropdown.config(state="readonly")
        else:
            self.windows_dropdown.config(state=tk.DISABLED)


def main():
    SCREEN_SIZE = tuple(pyautogui.size())
    root = tk.Tk()
    root.geometry(f"{SCREEN_SIZE[0] // 4 * 3}x{SCREEN_SIZE[1] // 4 * 3}")  # Set initial size
    root.resizable(False, False)
    app = WebcamApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
