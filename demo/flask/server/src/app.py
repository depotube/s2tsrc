# Flask imports
from flask import Flask, jsonify, render_template, flash, request, redirect, url_for
from flask import send_from_directory, current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict

# firebase imports
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app, storage
import io
import os

# misc 
from io import StringIO
import time

from bob import sample_transcribe

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="john-depotube-personal-be14008820a6.json"

# UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'wav'}

# 2. Create an app, being sure to pass __name__
app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# create the folder where files get uploaded
os.makedirs(os.path.join(app.instance_path, 'tmp'), exist_ok=True)

# Initialize Firestore DB
cred = credentials.Certificate('firebasekey.json')
default_app = initialize_app(cred)
db = firestore.client()
# get access to firebase collection (ultimately this will come from database/login)
firmCollection_ref = db.collection('Hollins & Levy')
# get access to firebase storage
bucket = storage.bucket('john-depotube-personal.appspot.com')

# Define what to do when a user hits the index route
@app.route("/")
def home():
    print("Server received request for 'Home' page...")
    data = {
        u'firmName': u'Hollins & Levy'
    }
    return render_template("index.html", d=data)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        dt = dict(request.form)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            pathname = os.path.join(app.instance_path, 'tmp', filename)
            file.save(pathname)
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            audioBlob = bucket.blob(filename) # create Blob object with name of file in firebase
            audioBlob.upload_from_filename(pathname) # do the actual upload
            
            # set the sound file URI from Google Storage
            object_uri = 'gs://' + 'john-depotube-personal.appspot.com' + '/' + filename
            
            # create the new file ("*.txt") name
            newfile_name = os.path.splitext(filename)[0] + ".txt"

            print("Calling bob...")
            transcriptionBlob = sample_transcribe(newfile_name, object_uri, bucket)

            # create dictionary for firebase collection
            blob_expiry = int(time.time() + (60 * 60 * 24 * 7)) # set for 7 days
            data = {
                u'clientName': dt['cname'],
                u'date': dt['ddate'], # datetime.datetime.now(),
                u'audioURL': audioBlob.generate_signed_url(expiration=blob_expiry),
                u'transcriptionURL': transcriptionBlob.generate_signed_url(expiration=blob_expiry),
            }

            # The name of the document equals the "'clientName'-'deposition date'"
            collName = dt['cname'] + '-' + dt['ddate']
            corrected_collName = collName.replace('/', '-')
            print("Collection name is: " + corrected_collName)
            firmCollection_ref.document(corrected_collName).set(data)

            return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard(): 
    # get all the documents for this law firm 
    docs = db.collection(u'Hollins & Levy').stream()
    return render_template("dashboard.html", d=docs, fn='Hollins & Levy')

@app.route("/about")
def about():
    print("Server received request for 'About' page...")
    return "Your name and current location"
 
@app.route("/contact")
def contact():
    print("Server received request for 'Contact' page...")
    return "email me at jcg@toast.net"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))