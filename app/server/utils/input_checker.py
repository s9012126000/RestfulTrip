import datetime
import re


def check_input_date(checkin, checkout):
    date_limit = True
    date_tag = True
    try:
        if checkin != '' and checkout != '':
            che_in = datetime.datetime.strptime(checkin, "%Y-%m-%d")
            che_out = datetime.datetime.strptime(checkout, "%Y-%m-%d")
            if che_out < che_in:
                date_tag = False
            elif che_in.date() < datetime.datetime.now().date():
                date_tag = False
            elif (che_out - che_in).days > 30:
                date_tag = False
                date_limit = False
        else:
            date_tag = False
    except ValueError:
        date_tag = False
    return date_tag, date_limit


def check_input_page(page, page_tol):
    page_tag = True
    try:
        page = int(page)
        if page_tol < page or page <= 0:
            page_tag = False
    except:
        page_tag = False
    return page, page_tag


def check_input_person(person):
    person_tag = True
    try:
        person = int(person)
        if person <= 0:
            person_tag = False
    except:
        person_tag = False
    return person, person_tag


def check_input_dest(dest):
    dest_tag = True
    if dest == '':
        dest_tag = False
    elif re.search(r'[\dA-Za-z%_&\-~@#$^*(){}|\[\]?><.=+;:"]+', dest):
        dest_tag = False
    return dest_tag