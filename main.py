from flask import Flask, render_template, Response, stream_with_context
import cv2
import time
import random
import json
import os
import HandTrackingModule as htm

app = Flask(__name__)

cap = cv2.VideoCapture(0)


def gen_frames():
    wCam, hCam = 640, 480
    global handfingers
    folderPath = "resized"
    myList = os.listdir(folderPath)
    overlayList = []
    for imPath in myList:
        image = cv2.imread(f"{folderPath}/{imPath}")
        print(image)
        overlayList.append(image)

    print(overlayList)
    pTime = 0

    detector = htm.handDetector(detectionCon=0.75)

    tipIds = [4, 8, 12, 16, 20]

    while True:
        success, img = cap.read()
        cap.set(3, wCam)
        cap.set(4, hCam)
        img = detector.findHands(img)
        # img = cv2.resize(img,(hCam,wCam))
        lmList = detector.findPosition(
            cv2.resize(img, (hCam, wCam)), draw=False)
        # print(lmList)

        if len(lmList) != 0:
            fingers = []

            # Thumb
            if lmList[tipIds[0]][1] > lmList[tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

            # 4 Fingers
            for id in range(1, 5):

                if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)

                print(fingers)
                totalFingers = fingers.count(1)
                print(f"Total fingers: {totalFingers}")
                handfingers = totalFingers
                h, w, c = overlayList[totalFingers - 1].shape

                # Print Photos on camera
                # print(cv2.resize(
                #     overlayList[totalFingers - 1], (480, 640)).shape)
                # img[0:h, 0:w] = overlayList[totalFingers - 1]

                # cv2.rectangle(img, (20, 225), (170, 425),
                #               (0, 255, 0), cv2.FILLED)
                # cv2.putText(img, str(totalFingers), (45, 375), cv2.FONT_HERSHEY_PLAIN,
                #             10, (255, 0, 0), 25)
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        # cv2.putText(img, f'FPS: {int(fps)}', (400, 70), cv2.FONT_HERSHEY_PLAIN,
        #             3, (255, 0, 0), 3)

        ret, buffer = cv2.imencode(".jpg", img)
        img = buffer.tobytes()

        yield (b'--img\r\n'b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')
        cv2.waitKey(1)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=img')


@app.route("/listen")
def listen():

    def respond_to_client():
        while True:
            _data = json.dumps({"floor": handfingers})
            yield f"id: 1\ndata: {_data}\nevent: online\n\n"
            time.sleep(0.5)
    return Response(respond_to_client(), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(debug=True)
