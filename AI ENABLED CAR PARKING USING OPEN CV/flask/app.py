
import cv2
import cvzone
import numpy as np
import pickle
import psycopg2
from flask import Flask, render_template, request, session
import urllib.parse as up

app = Flask(__name__)
app.secret_key = 'a'

up.uses_netloc.append("postgres")
url = up.urlparse("postgres://wiesofsm:FiD8RZsW_XYDFO_D0ui9XdBJdioUfo_c@kiouni.db.elephantsql.com/wiesofsm")

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

print("connected")


@app.route('/')
def project():
    return render_template('index.html')


@app.route('/index.html')
def home():
    return render_template('index.html')


@app.route('/model')
def model():
    return render_template('model.html')


@app.route('/login.html')
def login():
    return render_template('login.html')


@app.route('/aboutus.html')
def aboutus():
    return render_template('aboutus.html')


@app.route('/signup.html')
def signup():
    return render_template('signup.html')


@app.route("/signup", methods=['POST', 'GET'])
def signup1():
    msg = ''
    if request.method == 'POST':
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        insert_sql = "INSERT INTO REGISTER VALUES (%s, %s, %s)"
        cur = conn.cursor()
        cur.execute(insert_sql, (name, email, password))
        conn.commit()
        msg = "You have successfully registered!"
    return render_template('login.html', msg=msg)


@app.route("/login", methods=['POST', 'GET'])
def login1():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        sql = "SELECT * FROM REGISTER WHERE EMAIL = %s AND PASSWORD = %s"
        cur = conn.cursor()
        cur.execute(sql, (email, password))
        account = cur.fetchone()
        if account:
            session['Loggedin'] = True
            session['id'] = account[1]
            session['email'] = account[2]
            return render_template('model.html')
        else:
            msg = "Incorrect Email/password"
            return render_template('login.html', msg=msg)
    else:
        return render_template('login.html')


@app.route('/modelq')
def liv_pred():
    # Video feed
    cap = cv2.VideoCapture('carParkingInput.mp4')
    with open('parkingSlotPosition', 'rb') as f:
        posList = pickle.load(f)
    width, height = 107, 48

    def checkParkingSpace(imgPro):
        spaceCounter = 0
        for pos in posList:
            x, y = pos
            imgCrop = imgPro[y:y + height, x:x + width]
            count = cv2.countNonZero(imgCrop)
            if count < 900:
                color = (0, 255, 0)
                thickness = 5
                spaceCounter += 1
            else:
                color = (0, 0, 255)
                thickness = 2
            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
        cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20,
                           colorR=(0, 200, 0))

    while True:
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        success, img = cap.read()
        if not success:
            break
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
        imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
                                             25, 16)
        imgMedian = cv2.medianBlur(imgThreshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)
        checkParkingSpace(imgDilate)
        cv2.imshow("Image", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    app.run(debug=True)
