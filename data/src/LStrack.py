import math  # used to calculate max distance between points
import cv2
import numpy as np
import mouse  # used to control mouse (dragging and drawing)
import mediapipe as mp
import tkinter as tk
import threading
import keyboard
import pyautogui
import csv
import copy
import argparse
import itertools
import cv2 as cv
import time

import webbrowser

from collections import Counter
from collections import deque
from cv2 import warpPerspective  # used in warping image
from ast import literal_eval  # gets settings from file and gets literal type from str type
from LScalibrate import warpImage  # used to warp image
from playsound import playsound  # used for ping sound when changing modes
from threading import Thread  # used to thread playsound
from threading import Lock
from utils import CvFpsCalc
from model import KeyPointClassifier
from model import PointHistoryClassifier
from tkinter import ttk
import speech_recognition as sr
import pyttsx3 as tts
from time import ctime

# window = None
def save_video_source(source):
    with open("video_source.txt", "w") as file:
        file.write(str(source))

def load_video_source():
    try:
        with open("video_source.txt", "r") as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return 0  # Default to 0 if file not found or if it's invalid
    
def start(root, pointsstr, maskparamsmalformed, width, height):
        # Initialize camera

    # gets literal vals from str
    points = literal_eval(pointsstr)
    maskparamsstr = ''.join([letter for letter in maskparamsmalformed if letter not in("array()")])
    maskparams = literal_eval(maskparamsstr)

    lower, upper = np.array(maskparams[0]), np.array(maskparams[1])
    
    root.withdraw()
    global cap
    global video_source
    video_source = load_video_source()  # Load video source from file
    cap = cv2.VideoCapture(video_source)
    cap.set(15, -5) #  may have to change the 2nd arg. Only supported for some cameras. Testing with droidcam therefore cannot use this myself
    mat = warpImage(cap, points)  # creates warped image 
    hold = []  # list of points to detect when held
    count = 0
    drawmode = False 
    previous = None 
    # myHands = mp.solutions.hands.Hands(max_num_hands= 1, static_image_mode=False,min_detection_confidence=0.5)
    # drawing_utils = mp.solutions.drawing_utils
#Hands Line Var
    # x1 = y1 = x2 = y2 = 0
    def run_tkinter():
        global newwindow
        newwindow = tk.Tk()
        newwindow.title("Luna Gesture")
        newwindow.geometry("300x100")
        newwindow.resizable(width=False, height=False)
        def button_click():
            # print("Button clicked!")
            main()
        def switch_camera():
            global video_source
            video_source = (video_source + 1) % 3  # Cycle through 0, 1, 2
            save_video_source(video_source)  # Save the new video source

        button = tk.Button(newwindow, text="Hand Gesture", command=button_click, background="blue", foreground="white", font=("Helvetica", 12))
        button.pack(expand=True, fill="both")
        btn_switch = ttk.Button(newwindow, text="Switch Camera - requires restart", command=switch_camera)
        btn_switch.pack()
        newwindow.mainloop()
        return newwindow
    
    engine2 = tts.init()
    engine2.setProperty('rate', 150)  # Speed of voice
    engine2.setProperty('volume', 1.0)  # Max volume

    # Function to respond to voice commands
    def respond(voice_data):
        if 'what is your name' in voice_data:
            engine2.say('My name is Luna')
            engine2.runAndWait()
            print('My name is Luna')

        elif 'what time is it' in voice_data:
            engine2.say(f'The time is {ctime()}')
            engine2.runAndWait()
            print(ctime())

        elif 'open google' in voice_data:
            engine2.say('What do you want to search for?')
            engine2.runAndWait()
            search = recordAudio('What do you want to search for?')
            url = 'https://www.google.com/search?q=' + search
            webbrowser.open(url)
            engine2.say(f'This is what I found for {search}')
            engine2.runAndWait()

        elif 'find a location' in voice_data:
            location = recordAudio('Which location do you want to search for?')
            url = 'https://google.nl/maps/place/' + location
            webbrowser.get().open(url)
            engine2.say(f'Here is the location of {location}')
            engine2.runAndWait()

        elif 'open a new tab' in voice_data:
            engine2.say('Opening a new tab in your web browser')
            engine2.runAndWait()
            openNewTabInOperaGX()

        elif 'stop' in voice_data:
            engine2.say('Thank you, let me know if you need anything.')
            engine2.runAndWait()
            return 'stop'

    # Function to open a new tab in Opera GX
    def openNewTabInOperaGX():
        try:
            opera_gx_path = r"C:\Users\Justin Santos\AppData\Local\Programs\Opera GX\launcher.exe"
            webbrowser.register('opera', None, webbrowser.BackgroundBrowser(opera_gx_path))
            webbrowser.get('opera').open('google.com', new=2)
            print('Opened a new tab in Opera GX')
        except Exception as e:
            print(f'Error opening a new tab in Opera GX: {str(e)}')

    # Function to record audio and process commands
    def recordAudio(ask=False):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            if ask:
                engine2.say(ask)
                engine2.runAndWait()
            r.adjust_for_ambient_noise(source, duration=1)
            print("Listening for command...")
            audio = r.listen(source)

            try:
                voice_data = r.recognize_google(audio)
                return voice_data.lower()
            except sr.UnknownValueError:
                engine2.say('Sorry, I did not understand that.')
                engine2.runAndWait()
                return None
            except sr.RequestError:
                engine2.say('Sorry, the service is unavailable.')
                engine2.runAndWait()
                return None

    # Function to continuously listen for "Hey Luna"
    def listen_for_wake_word():
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            print("Waiting for 'Hey Luna'...")

            while True:
                audio = r.listen(source)
                try:
                    voice_data = r.recognize_google(audio).lower()
                    if "hey luna" in voice_data:
                        print("Wake word detected!")
                        engine2.say("How can I assist you?")
                        engine2.runAndWait()
                        listen_for_commands()  # Now listen for commands after "Hey Luna"
                except sr.UnknownValueError:
                    continue  # Ignore unrecognized audio and continue listening for "Hey Luna"
                except sr.RequestError:
                    engine2.say('Sorry, the service is unavailable.')
                    engine2.runAndWait()
                    continue

    # Function to listen for commands after wake word is detectedqwewqeqw
    def listen_for_commands():
        while True:
            command = recordAudio()  # Listen for the actual command
            if command:
                result = respond(command)
                if result == 'stop':
                    break

            engine2.say("Are you satisfied with the result, or would you like to make another request?")
            engine2.runAndWait()
            satisfied = recordAudio()

            if 'no' in satisfied:
                engine2.say("Okay, what else can I do for you?")
                engine2.runAndWait()
            elif 'yes' in satisfied:
                engine2.say("Okay, I will be on standby for 'Hey Luna'.")
                engine2.runAndWait()
                break

    # Tkinter window for activating voice assistantqwewqewq
    def run_Voice():
        global newwindow1
        newwindow1 = tk.Tk()
        newwindow1.title("Luna Voice")
        newwindow1.geometry("300x100")
        newwindow1.resizable(width=False, height=False)

        def button_click():
            threading.Thread(target=listen_for_wake_word).start()
            print("Voice assistant activated and waiting for 'Hey Luna'!")

        button = tk.Button(newwindow1, text="Luna Voice Active", command=button_click, background="pink", foreground="white", font=("Helvetica", 12))
        button.pack(expand=True, fill="both")
        newwindow1.mainloop()


    ## runs tkinter independently from the program and separately 
    # lock = threading.Lock()
    # t1=threading.Thread(target=run_tkinter,args=(lock,))
    t1 = threading.Thread(target=run_tkinter)
    t1.start()
    t2 = threading.Thread(target=run_Voice)
    t2.start()
            
    while True:
        check, frame = cap.read()
        if not check:
            break
        # generates image from mask
        frame = warpPerspective(frame, mat, (1000, 1000)) 
        hsvimg = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        maskedimg = cv2.inRange(hsvimg, lower, upper)
        image = cv2.bitwise_and(frame, frame, mask=maskedimg)


        # gets points >
        contours, rel = cv2.findContours(maskedimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # gets simple contours
        pts = None
        contourpts = []
        if len(contours) != 0:
            for contour in contours:
                if cv2.contourArea(contour) > 10:  # gets contour area for large objects on screen
                    x, y, w, h = cv2.boundingRect(contour)
                    x = (x+(x+w))//2
                    y = (y+(y+h))//2
                    
                    pts = (x, y)
                    contourpts.append(pts)

        check = set(contourpts)
        if len(check) > 1:  # confirms points using brightest point detection if multiple contours
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5,5), 0)  # converts to grayscale and gaussian blur to reduce influence of individual pixels
            minv, maxv, minl, maxl = cv2.minMaxLoc(gray)
            pts = maxl  # obtains final points var
        # < gets points  
        
        if not setHold(count, hold, pts):  # adds point tuple to hold list
            count += 1

        if pts is not None:
            if getHold(hold):  # function to see if led being held
                count = 0
                drawmode = changeMode(drawmode)  # function to change input mode

            if drawmode:
                temp = draw(pts, width, height, previous)  # drawmode function
                previous = temp  # sets previous point
            else:
               drag(pts, width, height)  # drag function
        else:  # releases mouse when LED off
            if drawmode: 
                mouse.release("left")
                previous = None
            else:
                mouse.release("left")


        # blank = np.ones((300, 300))
        # cv2.putText(blank, "Press ESC to stop Program", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 1, cv2.LINE_AA)

        # cv2.imshow("Aeolian", blank)
        cv2.imshow('Frame', frame)
        # cv2.imshow('Masked', maskedimg)
        # cv2.imshow('Image', image)
        # exits once ESC pressed or close button pressed
        if cv2.waitKey(1) & 0xFF == 27:
            newwindow.quit()
            newwindow1.quit()

            break
        
       
        # if cv2.getWindowProperty("Aeolian", cv2.WND_PROP_VISIBLE) < 1:
        #     break



 
    newwindow.quit()
    newwindow.deiconify()
    newwindow1.quit()
    newwindow1.deiconify()
    cap.release()
    cv2.destroyAllWindows()
    root.deiconify()




def close_Tkinter():
    # newwindow.deiconify()
    pass

    
def setHold(count, hold, pts):
    if count < 20:
        hold.append(pts)
        return False
    else:
        hold.append(pts)  # appends latest point and remove oldest point (keeps track of points on latest 20 frames)
        hold.pop(0)
        return True


def getHold(hold):
    if None not in hold and len(hold) == 20:  # detects if LED being held
        res = 0
        for p in hold:
            holdcopy = hold.copy()
            holdcopy.remove(p)
            cur = max([(math.sqrt((p[0]-c[0])**2+(p[1]-c[1])**2)) for c in holdcopy])  # obtains the maximum distance between all points
            if cur > res:
                res = cur
        if res < 5:  # if the maximum distance between points is small, triggers held state. Allows the pen to be slightly moved
            hold.clear()
            return True
    return False


def changeMode(drawmode):
    Thread(target=lambda:sound(drawmode)).start()  # threaded function to allow the points to be updated whilst sound plays
    if drawmode:  # changes the drawmode var
        return False
    else:
        return True
    

def sound(drawmode):
    if drawmode:  # sound played depending on current mode
        playsound("data/sound/dragging.mp3")
    else:
        playsound("data/sound/drawing.mp3")


def drag(pos, w, h):
    # obtains co-ordinates using screen res and current point
    x = (pos[0]/1000)*w 
    y = (pos[1]/1000)*h
    mouse.move(x, y, True)  # moves mouse to new people
    mouse.press("left")  # for drag mode, LMB pressed until LED turns off and is then released 


def draw(pos, w, h, previous):
    x = (pos[0]/1000)*w
    y = (pos[1]/1000)*h
    mouse.move(x, y, True)  # moves mouse to new people

    if previous is not None:
        mouse.drag(previous[0], previous[1], x, y)  # drags the mouse between previous position from last frame and current position
    return (x,y)




def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--width", help='cap width', type=int, default=960)
    parser.add_argument("--height", help='cap height', type=int, default=540)

    parser.add_argument('--use_static_image_mode', action='store_true')
    parser.add_argument("--min_detection_confidence",
                        help='min_detection_confidence',
                        type=float,
                        default=0.7)
    parser.add_argument("--min_tracking_confidence",
                        help='min_tracking_confidence',
                        type=int,
                        default=0.5)

    args = parser.parse_args()

    return args


def main():
    # Argument parsing #################################################################
    args = get_args()

    cap_device = args.device
    cap_width = args.width
    cap_height = args.height

    use_static_image_mode = args.use_static_image_mode
    min_detection_confidence = args.min_detection_confidence
    min_tracking_confidence = args.min_tracking_confidence

    use_brect = True

    # Camera preparation ###############################################################
    cap = cv.VideoCapture(cap_device)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, cap_width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, cap_height)

    # Model load #############################################################
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=use_static_image_mode,
        max_num_hands=1,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    keypoint_classifier = KeyPointClassifier()

    point_history_classifier = PointHistoryClassifier()

    # Read labels ###########################################################
    with open('data/src/model/keypoint_classifier/keypoint_classifier_label.csv',
              encoding='utf-8-sig') as f:
        keypoint_classifier_labels = csv.reader(f)
        keypoint_classifier_labels = [
            row[0] for row in keypoint_classifier_labels
        ]
    with open(
            'data/src/model/point_history_classifier/point_history_classifier_label.csv',
            encoding='utf-8-sig') as f:
        point_history_classifier_labels = csv.reader(f)
        point_history_classifier_labels = [
            row[0] for row in point_history_classifier_labels
        ]

    # FPS Measurement ########################################################
    cvFpsCalc = CvFpsCalc(buffer_len=10)

    # Coordinate history #################################################################
    history_length = 16
    point_history = deque(maxlen=history_length)

    # Finger gesture history ################################################
    finger_gesture_history = deque(maxlen=history_length)

    #  ########################################################################
    mode = 0

    while True:
        fps = cvFpsCalc.get()

        # Process Key (ESC: end) #################################################
        key = cv.waitKey(1)

        if key == ord('q'):
            break

        number, mode = select_mode(key, mode)

        # Camera capture #####################################################
        ret, image = cap.read()
        if not ret:
            break
        # image = cv.flip(image, 1)  # Mirror display
        debug_image = copy.deepcopy(image)

        # Detection implementation #############################################################
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True

        #  ####################################################################
        if results.multi_hand_landmarks is not None:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                  results.multi_handedness):
                # Bounding box calculation
                brect = calc_bounding_rect(debug_image, hand_landmarks)
                # Landmark calculation
                landmark_list = calc_landmark_list(debug_image, hand_landmarks)

                # Conversion to relative coordinates / normalized coordinates
                pre_processed_landmark_list = pre_process_landmark(
                    landmark_list)
                pre_processed_point_history_list = pre_process_point_history(
                    debug_image, point_history)
                # Write to the dataset file
                logging_csv(number, mode, pre_processed_landmark_list,
                            pre_processed_point_history_list)

                # Hand sign classification
                hand_sign_id = keypoint_classifier(pre_processed_landmark_list)
                if hand_sign_id == 2:  # Point gesture
                    point_history.append(landmark_list[8])
                else:
                    point_history.append([0, 0])

                # Finger gesture classification
                finger_gesture_id = 0
                point_history_len = len(pre_processed_point_history_list)
                if point_history_len == (history_length * 2):
                    finger_gesture_id = point_history_classifier(
                        pre_processed_point_history_list)

                # Calculates the gesture IDs in the latest detection
                finger_gesture_history.append(finger_gesture_id)
                most_common_fg_id = Counter(
                    finger_gesture_history).most_common()

                # Drawing part
                debug_image = draw_bounding_rect(use_brect, debug_image, brect)
                debug_image = draw_landmarks(debug_image, landmark_list)
                debug_image = draw_info_text(
                    debug_image,
                    brect,
                    handedness,
                    keypoint_classifier_labels[hand_sign_id],
                    point_history_classifier_labels[most_common_fg_id[0][0]],  
                )
                hand_gesture = keypoint_classifier(pre_processed_landmark_list)
                point_gesture_id = point_history_classifier(pre_processed_point_history_list)
                print(hand_gesture)
                if hand_gesture == 1:
                    perform_action("fistClosed")
                elif hand_gesture == 2:
                    perform_action("pointerUp")
                elif hand_gesture == 4:
                    perform_action("smolC")
                elif hand_gesture == 5:
                    perform_action("bigC")
                elif hand_gesture == 3:
                    pass
                elif hand_gesture == 0:
                    perform_action("open")
                elif hand_gesture ==6:
                    perform_action('right')
                elif hand_gesture == 7:
                    perform_action('left')
                elif hand_gesture ==8:
                    perform_action('peace')


        else:
            point_history.append([0, 0])

        debug_image = draw_point_history(debug_image, point_history)
        debug_image = draw_info(debug_image, fps, mode, number)

        # Screen reflection #############################################################
        cv.imshow('Frame2', debug_image)

    cap.release()
 
    cv2.destroyWindow('Frame2')
    close_Tkinter()



def openNewTabInOperaGX():
    try:
        # Specify the path to the Opera GX executable
        opera_gx_path = r"C:\Users\Justin Santos\AppData\Local\Programs\Opera GX\launcher.exe"  # Adjust the path as needed

        # Use the webbrowser module to open a new tab in Opera GX
        webbrowser.register('opera', None, webbrowser.BackgroundBrowser(opera_gx_path))
        webbrowser.get('opera').open('google.com', new=2)

        print('Opened a new tab in Opera GX')
    except Exception as e:
        print(f'Error opening a new tab in Opera GX: {str(e)}')

    
def perform_action(gesture):
    if gesture == "pointerUp":
        keyboard.press_and_release("volume up")
    elif gesture == "fistClosed":
        keyboard.press_and_release("volume down")
    elif gesture == "smolC":
        # Simulate Ctrl + '+' for zoom in
        pyautogui.keyDown("ctrl")
        pyautogui.scroll(100)
        pyautogui.keyUp("ctrl")
    elif gesture == "bigC":
        # Simulate Ctrl + '-' for zoom out
        pyautogui.keyDown("ctrl")
        pyautogui.scroll(-100)
        pyautogui.keyUp("ctrl")
    elif gesture == "open":
        pass
    elif gesture == "ok":
        pyautogui.keyDown('q')

    elif gesture == "right":
        pass
        keyboard.press_and_release('right')
        time.sleep(1)
    elif gesture == 'left':
        pass
        keyboard.press_and_release('left')
        time.sleep(1)
    elif gesture == 'peace':
        pass
        # openNewTabInOperaGX()
        # time.sleep(1)
     


def select_mode(key, mode):
    number = -1
    if 48 <= key <= 57:  # 0 ~ 9
        number = key - 48
    if key == 110:  # n
        mode = 0
    if key == 107:  # k
        mode = 1
    if key == 104:  # h
        mode = 2
    return number, mode


def calc_bounding_rect(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_array = np.empty((0, 2), int)

    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point = [np.array((landmark_x, landmark_y))]

        landmark_array = np.append(landmark_array, landmark_point, axis=0)

    x, y, w, h = cv.boundingRect(landmark_array)

    return [x, y, x + w, y + h]


def calc_landmark_list(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_point = []

    # Keypoint
    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        # landmark_z = landmark.z

        landmark_point.append([landmark_x, landmark_y])

    return landmark_point


def pre_process_landmark(landmark_list):
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, landmark_point in enumerate(temp_landmark_list):
        if index == 0:
            base_x, base_y = landmark_point[0], landmark_point[1]

        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

    # Convert to a one-dimensional list
    temp_landmark_list = list(
        itertools.chain.from_iterable(temp_landmark_list))

    # Normalization
    max_value = max(list(map(abs, temp_landmark_list)))

    def normalize_(n):
        return n / max_value

    temp_landmark_list = list(map(normalize_, temp_landmark_list))

    return temp_landmark_list


def pre_process_point_history(image, point_history):
    image_width, image_height = image.shape[1], image.shape[0]

    temp_point_history = copy.deepcopy(point_history)

    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, point in enumerate(temp_point_history):
        if index == 0:
            base_x, base_y = point[0], point[1]

        temp_point_history[index][0] = (temp_point_history[index][0] -
                                        base_x) / image_width
        temp_point_history[index][1] = (temp_point_history[index][1] -
                                        base_y) / image_height

    # Convert to a one-dimensional list
    temp_point_history = list(
        itertools.chain.from_iterable(temp_point_history))

    return temp_point_history


def logging_csv(number, mode, landmark_list, point_history_list):
    if mode == 0:
        pass
    if mode == 1 and (0 <= number <= 9):
        csv_path = 'data\src\model\keypoint_classifier\keypoint.csv'
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *landmark_list])
    if mode == 2 and (0 <= number <= 9):
        csv_path = 'data\src\model\point_history_classifier\point_history.csv'
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *point_history_list])
    return


def draw_landmarks(image, landmark_point):
    if len(landmark_point) > 0:
        # Thumb
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                (255, 255, 255), 2)

        # Index finger
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                (255, 255, 255), 2)

        # Middle finger
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                (255, 255, 255), 2)

        # Ring finger
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                (255, 255, 255), 2)

        # Little finger
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                (255, 255, 255), 2)

        # Palm
        cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                (255, 255, 255), 2)

    # Key Points
    for index, landmark in enumerate(landmark_point):
        if index == 0:  # 手首1
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 1:  # 手首2
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 2:  # 親指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 3:  # 親指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 4:  # 親指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 5:  # 人差指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 6:  # 人差指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 7:  # 人差指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 8:  # 人差指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 9:  # 中指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 10:  # 中指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 11:  # 中指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 12:  # 中指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 13:  # 薬指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 14:  # 薬指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 15:  # 薬指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 16:  # 薬指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 17:  # 小指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 18:  # 小指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 19:  # 小指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 20:  # 小指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)

    return image


def draw_bounding_rect(use_brect, image, brect):
    if use_brect:
        # Outer rectangle
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]),
                     (0, 0, 0), 1)

    return image


def draw_info_text(image, brect, handedness, hand_sign_text,
                   finger_gesture_text):
    cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22),
                 (0, 0, 0), -1)

    info_text = handedness.classification[0].label[0:]
    if hand_sign_text != "":
        info_text = info_text + ':' + hand_sign_text
    cv.putText(image, info_text, (brect[0] + 5, brect[1] - 4),
               cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)

    if finger_gesture_text != "":
        cv.putText(image, "Finger Gesture:" + finger_gesture_text, (10, 60),
                   cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
        cv.putText(image, "Finger Gesture:" + finger_gesture_text, (10, 60),
                   cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2,
                   cv.LINE_AA)

    return image


def draw_point_history(image, point_history):
    for index, point in enumerate(point_history):
        if point[0] != 0 and point[1] != 0:
            cv.circle(image, (point[0], point[1]), 1 + int(index / 2),
                      (152, 251, 152), 2)

    return image


def draw_info(image, fps, mode, number):
    cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX,
               1.0, (0, 0, 0), 4, cv.LINE_AA)
    cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX,
               1.0, (255, 255, 255), 2, cv.LINE_AA)

    mode_string = ['Logging Key Point', 'Logging Point History']
    if 1 <= mode <= 2:
        cv.putText(image, "MODE:" + mode_string[mode - 1], (10, 90),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                   cv.LINE_AA)
        if 0 <= number <= 9:
            cv.putText(image, "NUM:" + str(number), (10, 110),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                       cv.LINE_AA)
    return image




