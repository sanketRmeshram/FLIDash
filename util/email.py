# * This is an implementation of FLiDASH.
# * Copyright (C) 2019  Abhijit Mondal
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.



import smtplib
from email.mime.text import MIMEText

def sendErrorMail(sub, msg, pss):

    frm = "abhimondal@iitkgpmail.iitkgp.ac.in"
    to = "abhijitmanpur@gmail.com,abhimondal@iitkgp.ac.in"
    body = msg


    s = smtplib.SMTP("iitkgpmail.iitkgp.ac.in")
    s.login("abhimondal", pss)
    me="abhimondal@iitkgp.ac.in"

    msg = MIMEText(msg)
    msg['From'] = me
    msg['To'] = to
    msg['Subject'] = sub
    s.sendmail(me, to.split(","), msg.as_string())
    s.quit()
