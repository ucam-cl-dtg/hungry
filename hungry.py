#! /usr/bin/env python2.7

import argparse
import datetime
from email.mime.text import MIMEText
from jinja2 import Template
import getpass
import gnupg
from subprocess import Popen, PIPE

email_to = "dtg-lab@cl.cam.ac.uk"

email_body = """
Hello,
{% if organiser_names %} This week, {{ organiser_names }} are
organising DTG pizza.

{% endif %}
This week, as in previous weeks, we shall be having a lunch *meeting*
courtesy of Prof. Hopper. This week we shall be eating {{ food_type }}
cooked by {{ supplier_name }}.

Please sign up on the {{ poll_type }} [0], indicating your choice of meat, or
vegetarian food. {% if menu_link %} Please enter your choice from the menu [1],
including the entire line, as we need this for accounts. {% endif %}

The deadline for signups is {{ deadline }}
{% if menu_warnings %}
{{ menu_warnings }}
{% endif %}
We shall dine in {{ location }} at {{ date }} {{ time }}.

See you on Friday


{{ name }}

[0] {{ poll_link }}
{% if menu_link %}
[1] {{ menu_link }}
{% endif %}
"""

def next_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta( (4-today.weekday()) % 7 )
    return friday

def sign_string(string):
    gpg = gnupg.GPG()
    gpg_passphrase = getpass.getpass("GPG passphrase: ")
    return  gpg.sign(string, passphrase=gpg_passphrase)

def send_mail(body, to=email_to, cc=""):
    signed_body = sign_string(body)
    msg = MIMEText(str(signed_body))
    msg["To"] = to
    msg["Cc"] = cc
    msg["Subject"] = "DTG pizza Friday *meeting* (%s)" % datetime.date.isoformat(
        next_friday())
    p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
    p.communicate(msg.as_string())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("food_type", default="pizza")
    parser.add_argument("supplier_name", default="Dominos", help="""The name of the
                        (approved or otherwise) supplier.""")
    parser.add_argument("poll_link", help="Link to the signup poll.")
    parser.add_argument("--menu_link", help="Link to the menu.")
    parser.add_argument("--organiser_names", help="""Textual name of those
                        organising the pizza *meeting*.""")
    parser.add_argument("--poll_type", default="Doodle", help="""The name of the
                        provider of the signup poll.""")
    parser.add_argument("--menu_warnings", help="""Any warnings that should
                        accompany the menu, such as the occurence of beef
                        in vegetarian meals.""")
    parser.add_argument("--location", default="SN08", help="""Where we shall
                        be dining.""")
    parser.add_argument("--date", default=datetime.date.isoformat(next_friday()),
                        help="""ISO8601 formatted date of the *meeting*""")
    parser.add_argument("--time", default="12:30", help="""Time that we shall
                        dine.""")
    parser.add_argument("--deadline", default="%s 09:00" %
                        datetime.date.isoformat(next_friday()))
    parser.add_argument("--guests", help="""Email address of any guests to
                        invite.""")
    parser.add_argument("--mail", "-m", action="store_true", help="Send email.")
    args = parser.parse_args()
    args.name = getpass.getuser()
    template = Template(email_body)
    body = template.render(vars(args))
    if args.mail:
        send_mail(body, cc=args.guests)
    else:
        print body

if __name__ == "__main__":
    main()
