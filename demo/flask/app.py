# Flask imports
from flask import Flask, jsonify, render_template, flash, request, redirect, url_for
from flask import send_from_directory, current_app
from werkzeug.utils import secure_filename

# firebase imports
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app, storage
import io
import os

# misc 
from io import StringIO
import time

from google.cloud import speech_v1p1beta1

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
# get access to firebase collection
sampleCollection_ref = db.collection('sampleCollection')
# get access to firebase storage
bucket = storage.bucket('john-depotube-personal.appspot.com')

# 3. Define what to do when a user hits the index route
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

                u'firmName': u'Hollins & Levy',
                u'clientName': u'Shea Jensen',
                u'date': '09-17-19', # datetime.datetime.now(),
                u'audioURL': audioBlob.generate_signed_url(expiration=blob_expiry),
                u'transcriptionURL': transcriptionBlob.generate_signed_url(expiration=blob_expiry),
            }

            sampleCollection_ref.document(u'Shea Jensen-9-17-19').set(data)

            return redirect(url_for('dashboard'))


#@app.route('/uploads/<filename>')
#def uploaded_file(filename):
#    return send_from_directory(app.config['UPLOAD_FOLDER'],
#                               filename)

# @app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
#def download(filename):
#    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
#    return send_from_directory(directory=uploads, filename=filename)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():  
    doc_ref = sampleCollection_ref.document(u'Shea Jensen-9-17-19').get()
    return render_template("dashboard.html", d=doc_ref.to_dict())


#---------------------------------------------------------
# 4. Define what to do when a user hits the /about route
@app.route("/about")
def about():
    print("Server received request for 'About' page...")
    return "Your name and current location"

#5. 
@app.route("/contact")
def contact():
    print("Server received request for 'Contact' page...")
    return "email me at jcg@toast.net"

if __name__ == "__main__":
    app.run(debug=True)