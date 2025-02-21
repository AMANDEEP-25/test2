from flask import Flask, request, render_template, redirect, flash, url_for
from PIL import Image
import os
import tweepy
import secrets
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Folders for uploads and resized images
UPLOAD_FOLDER = 'uploads'
RESIZED_FOLDER = os.path.join('static', 'resized')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESIZED_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Predefined image sizes
SIZES = {
    "300x250": (300, 250),
    "728x90": (728, 90),
    "160x600": (160, 600),
    "300x600": (300, 600)
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part in the request')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Secure the filename to avoid malicious input
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            resized_filenames = []
            try:
                img = Image.open(filepath)
                for key, size in SIZES.items():
                    try:
                        # Use a copy of the image for each resize
                        img_copy = img.copy()
                        img_resized = img_copy.resize(size)
                        resized_filename = f"{os.path.splitext(filename)[0]}_{key}.png"
                        resized_path = os.path.join(RESIZED_FOLDER, resized_filename)
                        img_resized.save(resized_path)
                        resized_filenames.append(resized_filename)
                    except Exception as e:
                        flash(f"Error processing image for size {key}: {e}")
                        return redirect(request.url)
            except Exception as e:
                flash(f"Error opening the uploaded image: {e}")
                return redirect(request.url)

            # Publish images to X (Twitter) using the X API
            try:
                publish_images_to_x(resized_filenames)
                flash("Images have been uploaded and published to your X account!")
            except Exception as e:
                flash(f"Error publishing images: {e}")

            return render_template('index.html', images=resized_filenames)
    return render_template('index.html')

def publish_images_to_x(image_filenames):
    # Load API credentials from environment variables (or fallback to provided placeholders)
    consumer_key = os.environ.get('CONSUMER_KEY', "SS1E4T6yxfpCSYqEzOcorT5pc")
    consumer_secret = os.environ.get('CONSUMER_SECRET', "wzgWdg6q0IcNCK5Jh4kDj6RmsejbKzMvL5nkjPeedUzCWZhqXo")
    access_token = os.environ.get('ACCESS_TOKEN', "1799713241829965824-txgz3MQSnqjTYWiGNOvAlwPrMutjPK")
    access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET', "FuQXFRqDB4hEfUQs7wYHrfDVUG8FIjlKhUCMglgbfvvWd")

    # Set up Tweepy API authentication
    auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
    api = tweepy.API(auth)

    media_ids = []
    for filename in image_filenames:
        path = os.path.join(RESIZED_FOLDER, filename)
        media = api.media_upload(path)
        media_ids.append(media.media_id)

    status_text = f"Resized images from my app - {datetime.datetime.now().isoformat()}"
    try:
        api.update_status(status=status_text, media_ids=media_ids)
    except tweepy.TweepError as e:
        print("Error publishing images:", e)
        raise e

if __name__ == '__main__':
    app.run(debug=True)
