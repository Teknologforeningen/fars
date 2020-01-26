import requests
from getenv import env
from django.utils.translation import gettext as _

class BILLException(Exception):
    pass

class NotAllowedException(BILLException):
    pass

class BILLChecker:

    def __init__(self):
        self.api_url = env("BILL_API_URL")
        self.user = env("BILL_API_USER")
        self.password = env("BILL_API_PW")

    def check_user_can_book(self, user, type, group=0):
        if type is None:
            raise BILLException(_("BILL is not configured for this bookable"))
        group = 0 if group is None else group
        try:
            r = requests.get(self.api_url + "query?user=%s&group=%s&type=%s" % (user, group, type), auth=(self.user, self.password))
        except:
            raise BILLException("Could not connect to BILL server")
        if r.status_code != 200:
            raise BILLException("BILL returned status: %d" % r.status_code)
        # BILL API does not use proper http status codes
        try:
            response = int(r.text)
        except ValueError:
            # Unexpected non-integer response
            raise BILLException("BILL returned unexpected response: %s" % r.text)

        if response < 0:
            # Possible error responses:
            # -1 = User argument invalid
            # -2 = Group argument invalid
            # -3 = Type argument invalid
            # -4 = Database query error
            # -5 = Illegal response from database
            # -6 = User does not exist in BILL database
            # -7 = Group does not exist in LDAP database
            # -8 = Group has no BILL allocation
            # -9 = Type does not exist in BILL database
            # -10 = User does not belong to group
            raise BILLException("BILL returned error response: %d" % response)

        # 0 = Chosen combination has right to use the device and is NOT over limit
        # 1 = User has no right to use device
        # 2 = Group has no right to use device
        # 3 = Chosen combination has right to use the device but IS over limit
        # 4 = Chosen combination has right to use the device; the database has no limit specified for this device but the user IS over the default limit
        if response == 1:
            raise NotAllowedException(_("User has no right to use device"))
        elif response == 2:
            raise NotAllowedException(_("Group has no right to use device"))
        elif response == 3 or response == 4:
            raise NotAllowedException(_("User has insufficient credits to use device"))

        return True