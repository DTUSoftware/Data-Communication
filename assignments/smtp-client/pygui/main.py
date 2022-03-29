import traceback
from PyQt5.QtWidgets import *
from PyQt5 import uic
from smtp import smtp, mail
import base64


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
            smtp.ADDRESS = self.smtpserver.text()
            smtp.PORT = int(self.portnr.text())
            smtp.USE_SSL = True
            self.conn = smtp.Connection()
            self.conn.ehlo(self.smtpserver.text())
            self.conn.starttls()
            self.conn.ehlo(self.smtpserver.text())
            self.conn.auth(base64.b64encode(self.emailadress.text().encode("UTF-8")).decode("UTF-8"),
                           base64.b64encode(self.password.text().encode("UTF-8")).decode("UTF-8"))

            self.smtpserver.setEnabled(False)
            self.portnr.setEnabled(False)
            self.emailadress.setEnabled(False)
            self.password.setEnabled(False)
            self.pushButton.setEnabled(False)

            self.to.setEnabled(True)
            self.subject.setEnabled(True)
            self.text123.setEnabled(True)
            self.fromadress.setEnabled(True)
            self.pushButton_2.setEnabled(True)
            self.pushButton_3.setEnabled(True)
        except:
            traceback.print_exc()
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
            try:
                self.conn.mail(self.fromadress.text())
                self.conn.rcpt(self.to.text())
                header = str("From: " + self.fromadress.text() + "\r\n" +
                             "To: " + self.to.text() + "\r\n" +
                             "Subject: " + self.subject.text() + "\r\n")

                mimemessage = mail.MIMEMessage()
                mimemessage.add_body(self.text123.toPlainText())

                self.conn.data(header + mimemessage.get_output())
                confirmed = QMessageBox()
                confirmed.setText("Mail sent :)")
                confirmed.exec()
            except:
                traceback.print_exc()
                errormessage = QMessageBox()
                errormessage.setText("Sending the mail failed")
                errormessage.exec()


def main():
    app = QApplication([])
    window = MailGui()
    app.exec_()


if __name__ == '__main__':
    main()
