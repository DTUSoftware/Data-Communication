from PyQt5.QtWidgets import *
from PyQt5 import uic
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


class MailGui(QMainWindow):
    def __init__(self):
        super(MailGui, self).__init__()
        uic.loadUi("mailgui.ui", self)
        self.show()

        self.pushButton.clicked.connect(self.login)
        self.pushButton_2.clicked.connect(self.attatch)
        self.pushButton_3.clicked.connect(self.send)

    def login(self):
        try:
            self.server = smtplib.SMTP(self.smtpserver.text(), self.portnr.text())
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.emailadress.text(), self.password.text())

            self.smtpserver.setEnabled(False)
            self.portnr.setEnabled(False)
            self.emailadress.setEnabled(False)
            self.password.setEnabled(False)
            self.pushButton.setEnabled(False)

            self.to.setEnabled(True)
            self.subject.setEnabled(True)
            self.text.setEnabled(True)
            self.pushButton_2.setEnabled(True)
            self.pushButton_3.setEnabled(True)
        except:
            errormessage = QMessageBox()
            errormessage.setText("Login Failed!")
            errormessage.exec()

    def attatch(self):
        pass

    def send(self):
        confirmsend = QMessageBox()
        confirmsend.setText("Do you want to send this mail?")
        confirmsend.addButton(QPushButton("Yes"), QMessageBox.YesRole)
        confirmsend.addButton(QPushButton("No"), QMessageBox.NoRole)

        if confirmsend.exec_() == 0:

            self.msg['From'] = "HEJHEJHEJ"
            self.msg['To'] = self.to.text()
            self.msg['Subject'] = self.subject.text()
            self.msg.attach(MIMEText(self.textEdit.toPlainText(), 'plain'))
            text = self.msg.as_string()
            self.server.sendmail(self.emailadress.text(), self.to.text(), text)
            confirmed = QMessageBox()
            confirmed.setText("Mail sent :)")
            confirmed.exec()
#            except:
#                errormessage = QMessageBox()
#                errormessage.setText("Sending the mail failed")
#                errormessage.exec()


def main():
    app = QApplication([])
    window = MailGui()
    app.exec_()


if __name__ == '__main__':
    main()
