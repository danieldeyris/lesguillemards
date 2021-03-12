# -*- coding: utf-8 -*-
# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo.exceptions import UserError
from odoo import _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

""""
<MODEL_NAME> = [
    {
        'struct': <name> # Define the name of the object that must be created,
                         # and filled with 'content'
        'type': 'struct'|'direct'|'dict'
                'struct': will use the 'struct' key to build the data.
                'direct': will directly update the returned variable by calling
                          the WSDL method.
                'dict': will return a dictionary containing the data to be
                        transmitted to the WSDL method
                'list': will return a list containing the data to be
                        transmitted to the WSDL method
        'required': <boolean>, used we 'struct' key only, if True this
                    definition is mandatory
        'content': [ # Definition of the content ///
            {
                'src': <string>
                'dst': <string>
                'default': default value if 'src' isn't defined,
                'required': must have a value (not only present)
                'evaluate_default': if True the default value will be evaluate,
                                    else the default value is the value
                'max_size': ...
                },
            { ... },
            ]
        },
    { ... },
"""


def str2dct(dct, keys, val=None, sep='.'):
    """ Add or update the dict 'dct' with value given at the position
    represented by 'keys'.

    @param dct: Dictionnary to complete/update
    @param keys: String contains list of keys
    @param val: Value to put in dict.
    """
    *ks, last = keys.split(sep)
    cur = dct
    for j in ks + [last]:
        v = cur.setdefault(j, val if val and j == last else {})
        if j == last and v and val and v != val:
            cur[j] = val
        cur = cur[j]


class FromModel:
    """"""
    def __init__(self, uid, pwd):
        self.credential = {
            'uid': uid,
            'pwd': pwd,
            }

    def _check_conditions(self, value, content):
        """
        :param value: Value to check
        :param content: Dict of content constraints to check
        :return: Value respecting constraints.
        """
        max_size = content.get('max_size')
        if max_size:
            value = value and value[:max_size]
        if content.get('required'):
            if value == None:
                raise UserError(_(
                    "A value for the field '%s' is required!"
                    "(value: %s)!") % (content.get('dst'), value))
        regexp = content.get('regexp')
        if regexp:
            if not re.match(regexp, value):
                raise UserError(_(
                    "The value of the field '%s' doesn't respect the expected "
                    "conditions (conditions: %s, value: %s)!") % (
                        content.get('dst'), regexp, value))
        return value

    def _check_required(self, model, values):
        # Get all field must be present
        must_fields = [k for k,v in model.items() if v.get('required')]
        # Check if all fields are present
        cur_fields = [k for k,v in asdict(values).items() if v != None]
        print('must:', must_fields, 'have:', cur_fields)
        not_present = set(must_fields) - set(cur_fields)
        if not_present:
            raise UserError(
                _('Some field are missing: %s') % ', '.join(list(not_present)))

    def _build_value(self, content, record, options=None):
        """ """
        value = None
        source = content.get('src')
        if content:
            value = eval(source) if source else ''
        if value is None:
            source = content.get('default')
            if content.get('evaluate_default'):
                value = eval(source, globals())
            else:
                value = source
        _logger.debug("_build_value: %s: %s" % (source, value))
        value = self._check_conditions(value, content)
        return value

    def _get_content(self, item):
        """Get the content after checking if it defined."""
        contents = item.get('content')
        if not contents:
            _logger.error(
                    "Error! No 'content' to process: %s" % (item,))
            raise UserError(
                _("Error in data: see log on server for details!"))
        return contents

    def _build_values_dict(self, item, record, options=None):
        values = {}
        _logger.debug("_build_values_dict: %s\n%s" % (item, options))
        contents = self._get_content(item)
        for content in contents:
            value = self._build_value(content, record, options=options)
            if value:
                str2dct(values, content.get('dst'), value,)
        return values

    def _build_values_list(self, item, record, options=None):
        """According to the model, returns the record data in the form of a
        list.Return the data.

        :param item: Model of data.
        :type item: list.
        :param record: The Odoo's record from which the data will be retrieved.
        :type record: object
        :return: List of data.
        :rtype: list
        """
        values = []
        _logger.debug("_build_values_list: %s" % (item,))
        contents = self._get_content(item)
        for content in contents:
            values.append(
                self._build_value(content, record, options=options))
        return values

    def build_values(self, model, record, options=None):
        """
        Build a structure with is data defined in the transmitted model.
        The model must respect the <MODEL_NAME> structure.

        :param record: The Odoo's record from which the data will be retrieved.
        :param options: Dict of parameters needed to transforme the data.
        :return: A list of structure.
        """
        values = []
        options = options or {}
        for item in model:
            type_data = item.get('type')
            if not type_data:
                _logger.error(
                    "Error no 'type' defined, in item of model we cannot "
                    "continue: %s" % item)
                raise UserError(
                    _("Error in data: see log on serveur for details!"))
            method = '_build_values_%s' % (type_data,)
            try:
                action = getattr(self, method)
            except AttributeError as e:
                _logger.error("build_values: The method: %s isn't "
                    "defined!" % (method, ))
            else:
                values.append(action(item, record, options=options))
                _logger.debug("build_values: values: %s" % values)
        return values
