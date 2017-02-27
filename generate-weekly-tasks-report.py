#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MYSQL_USER ='root'
MYSQL_PASSWORD = '<secret>'
MYSQL_HOST = '<jirahost>'
MYSQL_DB = 'jiradb'

MSG_FROM_DEFAULT = "<Jira <jira@domain.ru>>"
MSG_TO_DEFAULT = "<foo@bar>"
SMTP_SERVER_DEFAULT = '<smtphost>'


def main():
    # "Doing" tasks
    query = ("SELECT SUMMARY,display_name,"
             "issuenum from jiraissue as i JOIN cwd_user as u ON LOWER(i.assignee) = LOWER(u.lower_user_name) "
             "where PROJECT=10008 and issuestatus IN (10043) AND ASSIGNEE "
             "IS NOT NULL")
    doing_table = table_to_html(queryDB(query))
    # "Done" tasks
    query = ("select SUMMARY,display_name,issuenum from jiraissue as i JOIN cwd_user as u "
             "ON LOWER(i.assignee) = LOWER(u.lower_user_name)"
             "where PROJECT=10008 and issuestatus IN (10040) AND ASSIGNEE IS NOT NULL AND "
             "RESOLUTIONDATE >= DATE_ADD(NOW(), INTERVAL(-WEEKDAY(NOW())) DAY) "
             "AND issuetype=10100 ORDER BY ASSIGNEE")
    done_table = table_to_html(queryDB(query))
    # "ToDo" tasks
    query = ("select SUMMARY,display_name,issuenum from jiraissue as i JOIN cwd_user as u "
             "ON LOWER(i.assignee) = LOWER(u.lower_user_name)"
             "where PROJECT=10008 and issuestatus IN (10044) AND ASSIGNEE IS NOT NULL")
    todo_table = table_to_html(queryDB(query))
    # "Cancelled" tasks
    query = ("select SUMMARY,display_name,issuenum from jiraissue as i JOIN cwd_user as u "
             "ON LOWER(i.assignee) = LOWER(u.lower_user_name)where PROJECT=10008 and issuestatus IN (10039)"
             " AND ASSIGNEE IS NOT NULL AND RESOLUTIONDATE >= DATE_ADD(NOW(), INTERVAL(-WEEKDAY(NOW())) DAY) "
             "AND issuetype=10100")
    cancelled_table = table_to_html(queryDB(query))

    today = datetime.date.today()
    next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
    next_friday = today + datetime.timedelta(days=-(today.weekday() - 4), weeks=1)
    msg = MIMEMultipart()
    msg['Subject'] = "Weekly tasks and report - MocoMedia (" + next_monday.strftime("%d.%m.%Y") + " - " + \
                     next_friday.strftime("%d.%m.%Y") + ")"
    msg['From'] = MSG_FROM_DEFAULT
    msg['To'] = MSG_TO_DEFAULT
    msg.attach(MIMEText("<html><body>", 'html'))
    msg.attach(MIMEText("<br><b>Выполненные:</b><br>", 'html'))
    msg.attach(MIMEText(done_table, 'html'))
    msg.attach(MIMEText("<br><b>Отмененные:</b><br>", 'html'))
    msg.attach(MIMEText(cancelled_table, 'html'))
    msg.attach(MIMEText("<br><b>В ожидании:</b><br>", 'html'))
    msg.attach(MIMEText(todo_table, 'html'))
    msg.attach(MIMEText("<br><b>В работе:</b><br>", 'html'))
    msg.attach(MIMEText(doing_table, 'html'))
    msg.attach(MIMEText("</html></body>", 'html'))
    send_mail(msg, sender=MSG_FROM_DEFAULT, to=MSG_TO_DEFAULT)


def queryDB(query):
    """

    :param query: SQL query as string
    :return: list of dict
    """
    try:
        cnx = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD,
                                      host=MYSQL_HOST,
                                      database=MYSQL_DB)
        cursor = cnx.cursor()
        cursor.execute(query)
        table = []
        for (summary, assignee, issuenum) in cursor:
            table.append({'summary': summary.decode("utf-8"), 'assignee': assignee.decode("utf-8"), 'issuenum': issuenum})
        cursor.close()
    except mysql.connector.Error as err:
        print(err)
    else:
        cnx.close()
        return table


def table_to_html(table):
    """

    :param table: list of dict
    :return: HTML page as string
    """
    htmltable = "<table border=1>"
    i = 1
    for row in table:
        htmltable += "<tr>"
        htmltable += "<td>" + str(i) + "</td>"
        htmltable += "<td><a href='http://jira.dgvg.ru/browse/AD-" + str(row['issuenum']) + "'>" + str(row['summary']) \
                     + "</a></td>"
        htmltable += "<td>" + str(row['assignee']) + "</td>"
        # for key, value in row.items():
        #     htmltable += "<td>" + str(value) + "</td>"
        htmltable += "</tr>"
        i += 1
    htmltable += "</table>"
    return htmltable


def send_mail(msg, smtp_server=SMTP_SERVER_DEFAULT, sender=MSG_FROM_DEFAULT, to=MSG_TO_DEFAULT):
    """
    :param msg: MIMEText object
    :param smtp_server:
    :param sender:
    :param to:
    :return:
    """
    s = smtplib.SMTP(smtp_server)
    s.sendmail(sender, to, msg.as_string())
    s.quit()


if __name__ == "__main__":
    main()
