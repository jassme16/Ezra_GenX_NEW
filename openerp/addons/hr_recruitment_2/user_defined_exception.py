# -*- coding: utf-8 -*-
##############################################################################
#
#    GenX, Data Genesis
#    User Defined Exceptions
#
##############################################################################
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError


class Warning(Exception):
    pass


class RedirectWarning(Exception):
    """ Warning with a possibility to redirect the user instead of simply
    diplaying the warning message.

    Should receive as parameters:
      :param int action_id: id of the action where to perform the redirection
      :param string button_text: text to put on the button that will trigger
          the redirection.
    """


class DateValidation(except_orm):
    def __init__(self, msg):
        super(DateValidation, self).__init__('Date notification', msg)


