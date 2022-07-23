import datetime


def get_date_limitation(day):
    checkin = datetime.datetime.now().date().isoformat()
    checkin_limit = (
        (datetime.datetime.now() + datetime.timedelta(days=day)).date().isoformat()
    )
    checkout = (datetime.datetime.now() + datetime.timedelta(days=1)).date().isoformat()
    checkout_limit = (
        (datetime.datetime.now() + datetime.timedelta(days=day + 1)).date().isoformat()
    )
    return checkin, checkin_limit, checkout, checkout_limit
