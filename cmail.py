import smtplib #(simple mail transfer protocol) # smtplib is a Python library that lets your programs send emails by following the special rules and addresses used by email servers.(types of n\w protocols)[protocol-a set of rules{types-n\w communication,n\w management,n\w security}
from email.message import EmailMessage #-class(this class is used because to get mail in a mail formate)
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL("smtp.gmail.com",465) #portnumber and server is an object [587 or 465 we only use these port numbers for email]-->to snd mail securely
    server.login("kousarnaazm@gmail.com","abud lnmw mkrf runt")
    msg=EmailMessage()
    msg["FROM"]="kousarnaazm@gmail.com"
    msg["TO"]=to
    msg["SUBJECT"]=subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()

