# This is a Flask version of "startup-mailer" 
# which will send a email to recipients when a particular URL is visited.
# This is very useful for a Flask web application to send confirmation emails to user.
# It's also useful for endpoint checking and usage summary of the web application

# importing libraries 
from flask import Flask 
from flask_mail import Mail, Message 

app = Flask(__name__) 
mail = Mail(app) # instantiate the mail class 

# configuration of mail 
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'sender@gmail.com'
app.config['MAIL_PASSWORD'] = '****************'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app) 

# message object mapped to a particular URL ‘/’ 
@app.route("/") 
def index(): 
    msg = Message(subject ='Hello From Flask-Mail', 
		  sender ='sender@gmail.com', 
		  recipients = ['recipient_1@yopmail.com'] 
		    ) 
    msg.body = 'Hello Flask message sent from Flask-Mail'
    mail.send(msg) 
    return 'Sent'

if __name__ == '__main__': 
    app.run(debug = True) 
