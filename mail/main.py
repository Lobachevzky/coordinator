import mail

## It is important to fill in the following
## information about the account you want the
## emails to be sent from.

mail.gmail_user = "penncoordinatorapp"
mail.gmail_pwd = "upennmcit"
iterations = 100

## Choose a subject

subject = "HI"

## Choose the content of the email

content = "HI"
for i in range(iterations):
    content += "TEST"

def send_mail():
      
    f = open("email_addresses.txt", "r")

    for address in f:
        address = address.replace("\n","")   
        mail.mail(address, subject, content)       

    f.close()
    
def main():
    ## Call the send mail function
    for i in range(iterations):
        send_mail()
    print "Finished Mailing"

if __name__ == "__main__":
    main()
