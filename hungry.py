#! /usr/bin/env python2.7

import argparse
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template, Environment
import getpass
import gnupg
import html2text
from subprocess import Popen, PIPE

email_to = "dtg-lab@cl.cam.ac.uk"

email_body = """
<html>
  <body>
    <script type="application/ld+json">
    {
      "@context" : "http://schema.org",
      "@type" : "FoodEstablishmentReservation",
      "reservationNumber" : "DTG pizza *meeting*",
      "reservationFor" : {
        "@type" : "FoodEstablishment",
        "name" : "{{ location }}",
        "url" : "https://www.cl.cam.ac.uk/research/dtg/openroommap/static/?h={{ location }}",
        "telephone": "+44 (0)1223 763500",
        "address" : {
          "@type" : "PostalAddress",
          "streetAddress" : "William Gates Building, 15 JJ Thompson Avenue",
          "addressLocality" : "Cambridge",
          "addressRegion" : "Cambs",
          "addressCountry" : "UK",
          "postalCode" : "CB3 0FD"
        }
      },
      "modifyReservationUrl" : "{{ poll_link }}",
      "startTime" : "{{ date }}:{{ time }}",
      "reservationStatus": "Unconfirmed",
      "underName": "Prof. Hopper",
      "action": [
        {
          "@type": "RsvpAction",
          "handler": {
            "@type": "HttpActionHandler",
            "url": "{{ poll_link }}"
          },
          "attendance": "http://schema.org/RsvpAttendance/Yes"
        },
        {
          "@type": "RsvpAction",
          "handler": {
            "@type": "HttpActionHandler",
            "url": "{{ poll_link }}"
          },
          "attendance": "http://schema.org/RsvpAttendance/No"
        }
      ]
    }
    </script>
<p>Hello,
{% if organiser_names %}<br />This week, {{ organiser_names }} are
organising DTG pizza.

{% endif %}</p>
<p>This week, as in previous weeks, we shall be having a pizza *meeting*
courtesy of Prof. Hopper. This week we shall be eating {{ food_type }}
cooked by {{ supplier_name }}.</p>

<p>Please sign up on the {{ poll_type }} [<a href="{{ poll_link }}">0</a>], indicating your choice of meat, or
vegetarian food. {% if menu_link %} Please enter your choice from the menu [<a href="{{ menu_link }}">1</a>],
including the entire line, as we need this for accounts. {% endif %}</p>

<p>The deadline for signups is {{ deadline }}
{% if menu_warnings %}
</p><p>{{ menu_warnings }}</p><p>
{% endif %}
We shall dine in {{ location }} at {{ date }} {{ time }}.</p>

<p>See you on Friday</p>


<p>{{ name }}</p>

<p>[0] <a href="{{ poll_link }}">{{ poll_link }}</a><br />
{% if menu_link %}
[1] <a href="{{ menu_link }}">{{ menu_link }}</a>
{% endif %}</p>
</body>
</html>
"""

gpg_passphrase = None

def next_friday():
    today = datetime.date.today()
    friday = today + datetime.timedelta( (4-today.weekday()) % 7 )
    return friday

def sign_string(string):
    global gpg_passphrase
    gpg = gnupg.GPG()
    if not gpg_passphrase:
        gpg_passphrase = getpass.getpass("GPG passphrase: ")
    return  str(gpg.sign(string, passphrase=gpg_passphrase))

def send_mail(body, to=email_to, cc=""):
    msg = MIMEMultipart('alternative')
    msg["To"] = to
    msg["Cc"] = cc
    msg["Subject"] = "DTG pizza Friday *meeting* (%s)" % datetime.date.isoformat(
        next_friday())
    part1 = MIMEText(sign_string(html2text.html2text(body)), 'plain')
    part2 = MIMEText(body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    p = Popen(["/usr/sbin/sendmail", "-t", "-f dtg-infra@cl.cam.ac.uk"], stdin=PIPE)
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
                        datetime.date.isoformat(next_friday()), help="""The
                        deadline for signing up for the *meeting*.""")
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
