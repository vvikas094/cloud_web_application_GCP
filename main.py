from __future__ import with_statement
from google.appengine.api import images
import PIL
from PIL import Image
import mimetypes
from StringIO import StringIO
import cStringIO
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from PIL import ImageEnhance
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import app_identity
from google.appengine.api import memcache
from random import randint
import re
import random, string
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import urllib
import os
import lib.cloudstorage as gcs
import time
import webapp2


class ImageData(ndb.Model):
    imageKey = ndb.BlobKeyProperty()
    gColor = ndb.FloatProperty()
    gBrightness = ndb.FloatProperty()
    gContrast = ndb.FloatProperty()
    gSharpness = ndb.FloatProperty()
    gRotate = ndb.IntegerProperty()
    gImFLSelected = ndb.BooleanProperty()

Default_Note_name='default_note'

def note_key(note_name=Default_Note_name):
    return ndb.Key('Notes', note_name)



class Text(ndb.Model):
    author=ndb.StringProperty()
    content=ndb.TextProperty()
    date=ndb.DateTimeProperty(auto_now_add=True)
    rating_input=ndb.StringProperty()

def validateEmail(email):

    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return 1
    return 0

def sendEmail(email,passcode):

    bodystr = passcode
    sender_address = "admin@" + app_identity.get_application_id() + ".appspotmail.com"
    mail.send_mail(sender=sender_address,to=email,subject="Secure Login Code!",body=bodystr)
    
def validatePasscode(UserID,pass_code):
    if pass_code in (Account1.query(Account1.id == UserID).fetch(1)[0].passcode):
        return 1
    return 0
        
class Account1(ndb.Model):
    name=ndb.StringProperty()
    key = ndb.StringProperty()
    id = ndb.StringProperty()
    passcode = ndb.StringProperty()
    
def randomwordgenerator(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

def generateHashCode(email):
    import hashlib
    return hashlib.md5(email.encode()).hexdigest()

# Entry point of the application
class MainPage(webapp2.RequestHandler):
    global UserID, randomgenerator, countMemCache, authorName
    def get(self):

        self.response.write("""
            <!doctype html>
            <html><head>
          <title>Image Enhancer</title>
            <meta name="viewport" content="width=device-width">
            <link rel="stylesheet" type="text/css" href="/stylesheets/style.css">
            <script src="https://code.jquery.com/jquery-2.2.1.min.js" integrity="sha256-gvQgAFzTH6trSrAWoH1iPo9Xc96QxSZ3feW6kem+O00=" crossorigin="anonymous">
    </script>
    <script src="/scripts/action.js"></script>
</head><body>""")
        note_name=self.request.get('note_name', Default_Note_name)
        countMemCache = memcache.get('countMemCache')
        if countMemCache == None:
            memcache.set('countMemCache', 0)
        else:
            memcache.set('countMemCache', countMemCache + 1)
            self.response.out.write("Page Visits <strong>" + str(countMemCache) + "</strong><br>")
            self.response.out.write("""<form>
                                      Choose your User name:<br>
                                      <input type="text" name="author" placeholder="Enter Your Name" required><br><br>
                                      <input type="text" name="UserName" placeholder="Enter your Email ID" required>
                                      <br><br>
                                      <input type="submit" value="Submit">
                                    </form> 
                                    <p>"Click the "Submit" button"</p>
                                    """)
        if 'author' in self.request.GET.keys():
            global authorName
            authorName = self.request.GET['author']
        if 'Passcode' in self.request.GET.keys():
            Passcode = self.request.GET['Passcode']
            global UserID, randomgenerator
            # self.response.out.write(validatePasscode(UserID,Passcode));
            if ((validatePasscode(UserID,Passcode[2:])==1) & (randomgenerator==Passcode[:2])):
                self.redirect("/ImageEnhancer")
            else:
              self.response.out.write("<h3>Enter a valid Passcode and try again</h3>");
        if 'UserName' in self.request.GET.keys():
            UserID = self.request.GET['UserName']
            if (validateEmail(UserID)==0):
                self.response.out.write("<h3>Enter a valid email ID</h3>");
            if (validateEmail(UserID)==1):
                rand_integer = 1*randint(0,25)
                randomgenerator = randomwordgenerator(2)
                sendEmail(UserID,randomgenerator+generateHashCode(UserID)[rand_integer:rand_integer+4])
                User = Account1(id=UserID, passcode=generateHashCode(UserID), key = UserID)
                
                if not (Account1.query(Account1.id == UserID).fetch(1)):
                    User_Key = User.put();
                    self.response.out.write("<h3>We have emailed your secured code for future logins to your email ID</h3>")
                self.response.out.write("""<form>Enter your Passcode:<br><input type="text" name="Passcode" placeholder="Enter your Passcode">
                <br><br><input type="submit" value="Submit">""")
              
class ImageEnhancer(webapp2.RequestHandler):
    def get(self):
        self.response.write("""
      <html><head>
      <title>Image Enhancer</title>
            <meta name="viewport" content="width=device-width">
            <link rel="stylesheet" type="text/css" href="/stylesheets/style.css">
            <script src="https://code.jquery.com/jquery-2.2.1.min.js" integrity="sha256-gvQgAFzTH6trSrAWoH1iPo9Xc96QxSZ3feW6kem+O00=" crossorigin="anonymous">
            </script>
            <script src="/scripts/action.js"></script></head>
            <form id="form" action="/imagehandler" method="POST" enctype="multipart/form-data" target="otp">
        """)
        note_name=self.request.get('note_name',Default_Note_name)
        self.response.write('<center><h1>Image Enhancement</h1></center>')
        self.response.write("""
        <input type="radio" name="choice-image" id="choice-image-url" value="image-url" checked="checked">
        <label for="choice-image-url">Image-URL</label>

        <input type="radio" name="choice-image" id="choice-image-file" value="image-file">
        <label for="choice-image-file">Image-File</label>
        <br>

        <label id="image-url">Image URL:
            <input type="url" id="imageURL" name="imageURL" placeholder="Enter an image URL here">
        </label>

        <label id="image-file">Image File:
            <input type="file" id="imageFile" name="imageFile" accept="image/*" placeholder="Choose an image file">
        </label>
        <br>

        <label>Rotate:
            <input type="range" name="rotate" min="0" max="360" value="0" step="1" onchange="showValue(this.name, this.value)" />
            <span id="rotate">0</span>
        </label>
        <br>

        <label>Color:
            <input type="range" name="color" min="-2" max="2" value="1" step="0.1" onchange="showValue(this.name, this.value)" />
            <span id="color">1</span>
        </label>
        <br>

        <label>Contrast:
            <input type="range" name="contrast" min="0" max="3" value="1" step="0.1" onchange="showValue(this.name, this.value)" />
            <span id="contrast">1</span>
        </label>
        <br>

        <label>Sharpness:
            <input type="range" name="sharpness" min="-2" max="2" value="1" step="0.1" onchange="showValue(this.name, this.value)" />
            <span id="sharpness">1</span>
        </label>
        <br>


        <label>Brightness:
            <input type="range" name="brightness" min="0" max="4" value="1" step="0.1" onchange="showValue(this.name, this.value)" />
            <span id="brightness">1</span>
        </label>
        <br>

        <h5><label><input type="checkbox" name="lucky" value="I'm Feeling Lucky"/> If you have any problem setting the values, Select this and we will get you a "I'm Feeling Lucky" image <label></h5>

        <input type="submit" name="submit" value="submit" />
        <br>
        <div id="runningindicator">
            Processing, please wait...
            <div id="runningindicator-img"></div>
        </div>
    </form>
    <iframe id="otpFrame" name="otp" frameborder="0"></iframe>""")
        self.response.write(""" <center><h2>Feedback</h2>
            <form action="/notes" method="POST">
            <span class="rating">
            <input type="checkbox" class="rating-input"
              id="rating-input-1-5" name="rating_input" value="5">
               <label for="rating-input-1-5" class="rating-star"></label>
                <input type="checkbox" class="rating-input"
                id="rating-input-1-4" name="rating_input" value="4">
              <label for="rating-input-1-4" class="rating-star"></label>
               <input type="checkbox" class="rating-input"
               id="rating-input-1-3" name="rating_input" value="3">
               <label for="rating-input-1-3" class="rating-star"></label>
              <input type="checkbox" class="rating-input"
                 id="rating-input-1-2" name="rating_input" value="2">
                <label for="rating-input-1-2" class="rating-star"></label>
                <input type="checkbox" class="rating-input"
                id="rating-input-1-1" name="rating_input" value="1">
                <label for="rating-input-1-1" class="rating-star"></label>
                </span><br><br>
               <textarea name="content" cols="40" rows="5" placeholder="Please provide your feedback"></textarea><br>
               <input type="submit" name="submit"  value="submit"/></center>
              """)
        texts_query=Text.query(ancestor=note_key(note_name)).order(-Text.date)
        texts=texts_query.fetch(15)
        for text in texts:
            if text.content:
                self.response.write('<strong><br><hr><div>(%s):</strong>'%text.author)
            if text.rating_input:
                if text.rating_input=="1":
                    self.response.write("""<span class="rating">
                      <input type="checkbox" class="rating-input"
                     id="rating-input-1-5" name="rating_input" value="5">
                     <label for="rating-input-1-5" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                      id="rating-input-1-4" name="rating_input" value="4">
                     <label for="rating-input-1-4" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                       id="rating-input-1-3" name="rating_input" value="3">
                    <label for="rating-input-1-3" class="rating-star"></label>
                    <input type="checkbox" class="rating-input"
                     id="rating-input-1-2" name="rating_input" value="2">
                    <label for="rating-input-1-2" class="rating-star"></label>
                    <input type="checkbox" class="rating-input"
                     id="rating-input-1-1" name="rating_input" value="1" checked>
                       <label for="rating-input-1-1" class="rating-star" ></label>
                     </span><br><br>""")
                elif text.rating_input=="2":
                    self.response.write("""<span class="rating">
                      <input type="checkbox" class="rating-input"
                       id="rating-input-1-5" name="rating_input" value="5">
                     <label for="rating-input-1-5" class="rating-star"></label>
                     <input type="checkbox" class="rating-input"
                      id="rating-input-1-4" name="rating_input" value="4">
                     <label for="rating-input-1-4" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                       id="rating-input-1-3" name="rating_input" value="3">
                     <label for="rating-input-1-3" class="rating-star"></label>
                     <input type="checkbox" class="rating-input"
                     id="rating-input-1-2" name="rating_input" value="2" checked>
                      <label for="rating-input-1-2" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                     id="rating-input-1-1" name="rating_input" value="1" checked>
                       <label for="rating-input-1-1" class="rating-star" ></label>
                     </span><br><br>""")
                elif text.rating_input=="3":
                    self.response.write("""<span class="rating">
                     <input type="checkbox" class="rating-input"
                     id="rating-input-1-5" name="rating_input" value="5">
                     <label for="rating-input-1-5" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                      id="rating-input-1-4" name="rating_input" value="4">
                     <label for="rating-input-1-4" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                       id="rating-input-1-3" name="rating_input" value="3" checked>
                      <label for="rating-input-1-3" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                     id="rating-input-1-2" name="rating_input" value="2" checked>
                          <label for="rating-input-1-2" class="rating-star"></label>
                     <input type="checkbox" class="rating-input"
                     id="rating-input-1-1" name="rating_input" value="1" checked>
                       <label for="rating-input-1-1" class="rating-star" ></label>
                     </span><br><br>""")
                elif text.rating_input=="4":
                    self.response.write("""<span class="rating">
                      <input type="checkbox" class="rating-input"
                     id="rating-input-1-5" name="rating_input" value="5">
                     <label for="rating-input-1-5" class="rating-star"></label>
                     <input type="checkbox" class="rating-input"
                      id="rating-input-1-4" name="rating_input" value="4"checked>
                     <label for="rating-input-1-4" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                       id="rating-input-1-3" name="rating_input" value="3"checked>
                      <label for="rating-input-1-3" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                     id="rating-input-1-2" name="rating_input" value="2" checked>
                       <label for="rating-input-1-2" class="rating-star"></label>
                       <input type="checkbox" class="rating-input"
                     id="rating-input-1-1" name="rating_input" value="1" checked>
                       <label for="rating-input-1-1" class="rating-star" ></label>
                     </span><br><br>""")
                elif text.rating_input=="5":
                    self.response.write("""<span class="rating">
                      <input type="checkbox" class="rating-input"
                     id="rating-input-1-5" name="rating_input" value="5" checked>
                     <label for="rating-input-1-5" class="rating-star"></label>
                     <input type="checkbox" class="rating-input"
                      id="rating-input-1-4" name="rating_input" value="4"checked>
                     <label for="rating-input-1-4" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                       id="rating-input-1-3" name="rating_input" value="3"checked>
                     <label for="rating-input-1-3" class="rating-star"></label>
                     <input type="checkbox" class="rating-input"
                     id="rating-input-1-2" name="rating_input" value="2" checked>
                     <label for="rating-input-1-2" class="rating-star"></label>
                      <input type="checkbox" class="rating-input"
                     id="rating-input-1-1" name="rating_input" value="1" checked>
                       <label for="rating-input-1-1" class="rating-star" ></label>
                     </span><br><br>""")
                if text.content:
                    self.response.write('%s</div>' %text.content)
            self.response.write("""</body></html>""")


class CreateUploadImageHandler(webapp2.RequestHandler):
    def get(self):
#         self.response.headers.add_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
#         self.response.headers.add_header("Expires","0")
        self.response.headers[b'Content-Type'] = b'text/plain'
        self.response.out.write(blobstore.create_upload_url('/upload_photo'))

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        try:
            upload = self.get_uploads()[0]
            iR = ImageData(imageKey=upload.key(),
                           gColor = float(self.request.get('color')),
                           gBrightness = float(self.request.get('brightness')),
                           gContrast = float(self.request.get('contrast')),
                           gSharpness = float(self.request.get('sharpness')),
                           gRotate = int(self.request.get('rotate')),
                           gImFLSelected = bool(self.request.get('lucky')))
            iR.key = ndb.Key(ImageData, '123')
            iR.put()
            self.redirect('/view_photo/%s' % upload.key())
        except:
            self.error(500)

class ImageDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
            if not blobstore.get(photo_key):
                self.error(404)
            else:
                try:
                  blob_info = blobstore.BlobInfo.get(photo_key)
                  im = Image.open(blob_info.open())
                  iR = ndb.Key(ImageData, '123').get()
                  mimeType = im.format
                  try:
                    if iR.gImFLSelected:
                      img = images.Image(blob_key = iR.imageKey)
                      img.im_feeling_lucky()
                      data = img.execute_transforms(output_encoding=images.JPEG)
                    else:
                      enh = ImageEnhance.Color(im) # 0 - 2 to be considered
                      out = enh.enhance(iR.gColor)
                      enh = ImageEnhance.Brightness(out) # 0 - black image, 1 - original image; Can give more than 1.0
                      out = enh.enhance(iR.gBrightness)
                      enh = ImageEnhance.Contrast(out) # 0 - solid grey image, 1 - original image
                      out = enh.enhance(iR.gContrast)
                      enh = ImageEnhance.Sharpness(out) # 0 - blurred image, 1 - original image, 2 - sharpened image
                      out = enh.enhance(iR.gSharpness) 
                      out = out.rotate(iR.gRotate, resample=Image.BICUBIC, expand=True)
                      buf = cStringIO.StringIO()
                      out.save(buf, mimeType)
                      data = buf.getvalue()
                    bucket_name = 'dem-ode'
                    bucket = '/' + bucket_name
                    filename = bucket + '/' + urllib.quote(u"{0}".format(time.time()).encode('utf8'))
                    with gcs.open(filename, 'w') as f:
                      f.write(data)
                    blobstore_filename = "/gs"+filename
                    #this is needed if you want to continue using blob_keys.
                    ieurl = images.get_serving_url(blobstore.BlobKey(blobstore.create_gs_key(str(blobstore_filename))))
                    self.response.out.write('<img width="100%" height="100%" src="' + ieurl +'"/>')
                    self.response.out.write('<a style="float:right;position:absolute;top:8px;right:8px;width:48px;height:48px" href="' + ieurl + '" download>'+'<img style="width: 48px;height: 48px;" src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Download-Icon.png/480px-Download-Icon.png"></a>')
                  except:
                        self.response.headers[b'Content-Type'] = b'text/plain'
                        self.response.out.write('Image size is too large. Can\'t handle')
                except:
                    self.response.headers[b'Content-Type'] = b'text/plain'
                    self.response.out.write('Image size is too large. Can\'t handle')

class ImageHandler(webapp2.RequestHandler):
    def post(self):
      try:
        gurl = self.request.get('imageURL')
        # print("urlColor: " +self.request.get('color'))
        gcolor = float(self.request.get('color'))
        gbrightness = float(self.request.get('brightness'))
        gcontrast = float(self.request.get('contrast'))
        gsharpness = float(self.request.get('sharpness'))
        grotate = int(self.request.get('rotate'))
        gImFLSelected = bool(self.request.get('lucky'))
        c = urlfetch.fetch(gurl, deadline=10).content
        im = Image.open(StringIO(c))
        mimeType = im.format
        try:
          if gImFLSelected:
            img = images.Image(c)
            img.im_feeling_lucky()
            data = img.execute_transforms(output_encoding=images.JPEG)
          else: 
            enh = ImageEnhance.Color(im) # 0 - 2 to be considered
            out = enh.enhance(gcolor)
            enh = ImageEnhance.Brightness(out) # 0 - black image, 1 - original image; Can give more than 1.0
            out = enh.enhance(gbrightness)
            enh = ImageEnhance.Contrast(out) # 0 - solid grey image, 1 - original image
            out = enh.enhance(gcontrast)
            enh = ImageEnhance.Sharpness(out) # 0 - blurred image, 1 - original image, 2 - sharpened image
            out = enh.enhance(gsharpness) 
            out = out.rotate(grotate, resample=Image.BICUBIC, expand=True)
            buf = cStringIO.StringIO()
            out.save(buf, mimeType)
            data = buf.getvalue()
            
          bucket_name = 'dem-ode'
          bucket = '/' + bucket_name
            
          filename = bucket + '/' + urllib.quote(u"{0}".format(time.time()).encode('utf8'))
          with gcs.open(filename, 'w') as f:
            f.write(data)
          blobstore_filename = "/gs"+filename
          # this is needed if you want to continue using blob_keys.
          ieurl = images.get_serving_url(blobstore.BlobKey(blobstore.create_gs_key(str(blobstore_filename))))
#        
          self.response.out.write('<img width="100%" height="100%" src="' + ieurl +'"/>')
          self.response.out.write('<a style="float:right;position:absolute;top:8px;right:8px;width:48px;height:48px" href="' + ieurl + '" download>'+'<img style="width: 48px;height: 48px;" src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Download-Icon.png/480px-Download-Icon.png"></a>')
        except:
          self.response.headers[b'Content-Type'] = b'text/plain'
          self.response.out.write('Image size is too large. Can\'t handle')
      except:
        self.response.headers[b'Content-Type'] = b'text/plain'
        self.response.out.write('Image size is too large. Can\'t handle')



class Notes(webapp2.RequestHandler):
    def post(self):
        note_name=self.request.get('note_name',Default_Note_name)
        text=Text(parent=note_key(note_name))
        text.rating_input=self.request.get('rating_input')
        global authorName
        text.author=authorName
        text.content=self.request.get('content')
        text.put()

        query_params={'note_name':note_name}
        self.redirect('/ImageEnhancer')
        

app = webapp2.WSGIApplication([
    ('/', MainPage), 
    ('/ImageEnhancer', ImageEnhancer),
    ('/imagehandler', ImageHandler),
    ('/createUploadHandler', CreateUploadImageHandler),
    ('/upload_photo', UploadHandler),
    ('/view_photo/([^/]+)?', ImageDownloadHandler),
    ('/notes',Notes),

    
], debug=True)