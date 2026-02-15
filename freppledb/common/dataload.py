#
# Copyright (C) 2017 by frePPLe bv
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from datetime import timedelta, datetime
from decimal import Decimal
from logging import INFO, ERROR, WARNING, DEBUG
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.worksheet.worksheet import Worksheet
import unicodedata

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.validators import EMPTY_VALUES
from django.db import DEFAULT_DB_ALIAS
from django.db.models import ForeignKey
from django.db.models.fields import (
    IntegerField,
    AutoField,
    DurationField,
    BooleanField,
    DecimalField,
)
from django.db.models.fields import (
    DateField,
    DateTimeField,
    TimeField,
    CharField,
    NOT_PROVIDED,
)
from django.db.models.fields.related import RelatedField
from django.forms.models import modelform_factory
from django.utils import translation
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.encoding import force_str
from django.utils.formats import get_format
from django.utils.text import get_text_list

from .models import Comment
from .localization import parseLocalizedDateTime


def sanitizeNumber(value):
    """
    Copied from https://github.com/django/django/blob/848fe70f3ee6dc151831251076dc0a4a9db5a0ec/django/utils/formats.py#L237
    Just some changes to make it work when l10n is False.
    """
    if isinstance(value, str):
        parts = []
        decimal_separator = get_format("DECIMAL_SEPARATOR", get_language(), True)
        if decimal_separator in value:
            value, decimals = value.split(decimal_separator, 1)
            parts.append(decimals)
        if settings.USE_THOUSAND_SEPARATOR:
            thousand_sep = get_format("THOUSAND_SEPARATOR", get_language(), True)
            if (
                thousand_sep == "."
                and value.count(".") == 1
                and len(value.split(".")[-1]) != 3
            ):
                # Special case where we suspect a dot meant decimal separator (see #22171)
                pass
            else:
                for replacement in {
                    thousand_sep,
                    unicodedata.normalize("NFKD", thousand_sep),
                }:
                    value = value.replace(replacement, "")
        parts.append(value)
        value = ".".join(reversed(parts))
    return value


def parseExcelWorksheet(
    model,
    data,
    user=None,
    database=DEFAULT_DB_ALIAS,
    ping=False,
    excel_duration_in_days=False,
    skip_audit_log=False,
):
    class MappedRow:
        """
        A row of data is made to behave as a dictionary.
        For instance the following data:
           headers: ['field1', 'field2', 'field3']
           data: [val1, val2, val3]
        behaves like:
          {'field1': val1, 'field2': val2, 'field3': val3}
        but it's faster because we don't actually build the dictionary.
        """

        def __init__(self, headers=None):
            if headers is None:
                headers = []
            self.headers = {}
            self.data = []
            colnum = 0
            self.numHeaders = 0
            for col in headers:
                if col:
                    self.headers[col.name] = (colnum, col)
                    self.numHeaders += 1
                colnum += 1

        def setData(self, data):
            self.data = data

        def empty(self):
            for i in self.data:
                if i.value:
                    return False
            return True

        def __getitem__(self, key):
            tmp = self.headers.get(key)
            if tmp:
                idx = tmp[0]
                field = tmp[1]
            else:
                idx = None
                field = None
            data = (
                self.data[idx].value
                if idx is not None and idx < len(self.data)
                else None
            )
            if isinstance(field, (IntegerField, AutoField)):
                if isinstance(data, (Decimal, float, int)):
                    data = int(data)
            elif isinstance(field, DecimalField):
                if isinstance(data, (Decimal, float)):
                    data = round(data, field.decimal_places)
            elif isinstance(field, DurationField):
                if isinstance(data, timedelta):
                    return data
                if isinstance(data, (float, int)):
                    # data is in days, convert it to seconds
                    if excel_duration_in_days:
                        return round(data * 86400, 3)
                    else:
                        return "%.6f" % data
                elif data is not None:
                    data = str(data)
                    day_split = data.split("d", 1)
                    days = 0
                    if len(day_split) > 1:
                        try:
                            days = int(day_split[0])
                        except Exception:
                            pass
                        if days:
                            if day_split[1].strip():
                                return "%s %s" % (days, day_split[1].strip())
                            else:
                                return "%s 00:00:00" % days
                        else:
                            return day_split[1].strip()
                    else:
                        return data
                else:
                    return None
            elif isinstance(field, (DateField, DateTimeField)):
                if isinstance(data, datetime):
                    # Rounding to second
                    if data.microsecond < 500000:
                        data = data.replace(microsecond=0)
                    else:
                        data = data.replace(microsecond=0) + timedelta(seconds=1)
                elif data:
                    data = str(data).strip()
                    try:
                        data = parseLocalizedDateTime(data)
                    except Exception:
                        pass
                else:
                    data = None
            elif isinstance(field, TimeField) and isinstance(data, datetime):
                data = "%s:%s:%s" % (data.hour, data.minute, data.second)
            elif (
                isinstance(field, RelatedField)
                and not isinstance(data, str)
                and isinstance(field.target_field, CharField)
                and data is not None
            ):
                data = str(data)
            elif isinstance(data, str):
                data = data.strip()
            return data

        def get(self, key, default=NOT_PROVIDED):
            try:
                return self.__getitem__(key)
            except KeyError as e:
                if default != NOT_PROVIDED:
                    return default
                raise e

        def __len__(self):
            return self.numHeaders

        def __contains__(self, key):
            return key in self.headers

        def has_key(self, key):
            return key in self.headers

        def keys(self):
            return self.headers.keys()

        def values(self):
            return [i.value for i in self.data]

        def items(self):
            return {col: self.__getitem__(col) for col in self.headers.keys()}

        __setitem__ = None
        __delitem__ = None

    if hasattr(model, "parseData"):
        # Some models have their own special uploading logic
        return model.parseData(
            data,
            MappedRow,
            user,
            database,
            ping,
            excel_duration_in_days,
            skip_audit_log,
        )
    else:
        return _parseData(
            model,
            data,
            MappedRow,
            user,
            database,
            ping,
            excel_duration_in_days,
            skip_audit_log,
        )


def parseCSVdata(
    model,
    data,
    user=None,
    database=DEFAULT_DB_ALIAS,
    ping=False,
    excel_duration_in_days=False,
    skip_audit_log=False,
):
    """
    This method:
      - reads CSV data from an input iterator
      - creates or updates the database records
      - yields a list of data validation errors

    The data must follow the following format:
      - the first row contains a header, listing all field names
      - a first character # marks a comment line
      - empty rows are skipped
    """

    class MappedRow:
        """
        A row of data is made to behave as a dictionary.
        For instance the following data:
           headers: ['field1', 'field2', 'field3']
           data: [val1, val2, val3]
        behaves like:
          {'field1': val1, 'field2': val2, 'field3': val3}
        but it's faster because we don't actually build the dictionary.
        """

        def __init__(self, headers=None):
            if headers is None:
                headers = []
            self.headers = {}
            self.data = []
            colnum = 0
            self.numHeaders = 0
            for col in headers:
                if col:
                    self.headers[col.name] = (colnum, col)
                    self.numHeaders += 1
                colnum += 1

        def setData(self, data):
            self.data = data

        def empty(self):
            for i in self.data:
                if i:
                    return False
            return True

        def __getitem__(self, key):
            try:
                idx = self.headers.get(key)
                if idx is None or idx[0] >= len(self.data):
                    return None
                val = self.data[idx[0]]
                if isinstance(idx[1], BooleanField) and val == "0":
                    # Argh... bool('0') returns True.
                    return False
                elif isinstance(idx[1], (DateField, DateTimeField)):
                    try:
                        return parseLocalizedDateTime(val) if val != "" else None
                    except Exception:
                        return val if val != "" else None
                elif isinstance(idx[1], DecimalField):
                    # Automatically round to 8 digits rather than giving an error message
                    return round(float(sanitizeNumber(val)), 8) if val != "" else None

                elif isinstance(idx[1], DurationField):
                    val = self.data[idx[0]]
                    if isinstance(val, timedelta):
                        return val
                    if isinstance(val, (float, int)):
                        # data is in days, convert it to seconds
                        if excel_duration_in_days:
                            return round(val * 86400, 3)
                        else:
                            return "%.6f" % val
                    elif val is not None:
                        val = str(val)
                        day_split = val.split("d", 1)
                        days = 0
                        if len(day_split) > 1:
                            try:
                                days = int(day_split[0])
                            except Exception:
                                pass
                            if days:
                                if day_split[1].strip():
                                    return "%s %s" % (days, day_split[1].strip())
                                else:
                                    return "%s 00:00:00" % days
                            else:
                                return day_split[1].strip()
                        else:
                            return val
                else:
                    return val if val != "" else None
            except KeyError as e:
                raise e

        def get(self, key, default=NOT_PROVIDED):
            try:
                return self.__getitem__(key)
            except KeyError as e:
                if default != NOT_PROVIDED:
                    return default
                raise e

        def __len__(self):
            return self.numHeaders

        def __contains__(self, key):
            return key in self.headers

        def has_key(self, key):
            return key in self.headers

        def keys(self):
            return self.headers.keys()

        def values(self):
            return self.data

        def items(self):
            return {col: self.data[idx[0]] for col, idx in self.headers.items()}

        __setitem__ = None
        __delitem__ = None

    if hasattr(model, "parseData"):
        # Some models have their own special uploading logic
        return model.parseData(
            data,
            MappedRow,
            user,
            database,
            ping,
            excel_duration_in_days,
            skip_audit_log,
        )
    else:
        return _parseData(
            model,
            data,
            MappedRow,
            user,
            database,
            ping,
            excel_duration_in_days,
            skip_audit_log,
        )


def _parseData(
    model,
    data,
    rowmapper,
    user,
    database,
    ping,
    excel_duration_in_days=False,
    skip_audit_log=False,
):
    selfReferencing = []

    def formfieldCallback(f):
        # global selfReferencing
        if isinstance(f, RelatedField):
            tmp = BulkForeignKeyFormField(field=f, using=database)
            if f.remote_field.model == model:
                selfReferencing.append(tmp)
            return tmp
        else:
            return f.formfield(localize=True)

    # Initialize
    headers = []
    rownumber = 0
    changed = 0
    added = 0
    content_type_id = ContentType.objects.get_for_model(
        model, for_concrete_model=False
    ).pk

    # Call the beforeUpload method if it is defined
    if hasattr(model, "beforeUpload"):
        model.beforeUpload(database)

    errors = 0
    warnings = 0
    has_pk_field = False
    processed_header = False
    rowWrapper = rowmapper()

    # Detect excel autofilter data tables
    if isinstance(data, Worksheet) and data.auto_filter.ref:
        try:
            bounds = CellRange(data.auto_filter.ref).bounds
        except Exception:
            bounds = None
    else:
        bounds = None

    for row in data:
        rownumber += 1
        if bounds:
            # Only process data in the excel auto-filter range
            if rownumber < bounds[1]:
                continue
            else:
                rowWrapper.setData(row)
        else:
            rowWrapper.setData(row)

        # Case 1: Skip empty rows
        if rowWrapper.empty():
            continue

        # Case 2: The first line is read as a header line
        elif not processed_header:
            processed_header = True

            # Collect required fields
            required_fields = set()
            for i in model._meta.fields:
                if (
                    not i.blank
                    and i.default == NOT_PROVIDED
                    and not isinstance(i, AutoField)
                ):
                    required_fields.add(i.name)

            # Validate all columns
            for col in rowWrapper.values():
                col = str(col).strip().strip("#").lower() if col else ""
                if col == "":
                    headers.append(None)
                    continue
                ok = False
                for i in model._meta.fields:
                    # Try with translated field names
                    if (
                        col == i.name.lower()
                        or (
                            isinstance(i, ForeignKey)
                            and col == "%s_id" % i.name.lower()
                        )
                        or col == i.verbose_name.lower()
                        or col == ("%s - %s" % (model.__name__, i.verbose_name)).lower()
                    ):
                        if i.editable is True:
                            headers.append(i)
                        else:
                            headers.append(None)
                        required_fields.discard(i.name)
                        ok = True
                        break
                    if translation.get_language() != "en":
                        # Try with English field names
                        with translation.override("en"):
                            if (
                                col == i.name.lower()
                                or (
                                    isinstance(i, ForeignKey)
                                    and col == "%s_id" % i.name.lower()
                                )
                                or col == i.verbose_name.lower()
                                or col
                                == (
                                    "%s - %s" % (model.__name__, i.verbose_name)
                                ).lower()
                            ):
                                if i.editable is True:
                                    headers.append(i)
                                else:
                                    headers.append(None)
                                required_fields.discard(i.name)
                                ok = True
                                break
                if not ok:
                    headers.append(None)
                    warnings += 1
                    yield (
                        WARNING,
                        None,
                        None,
                        None,
                        force_str(
                            _("Skipping unknown field %(column)s" % {"column": col})
                        ),
                    )
                if (
                    col == model._meta.pk.name.lower()
                    or col == model._meta.pk.verbose_name.lower()
                ):
                    has_pk_field = True
            if required_fields:
                # We are missing some required fields
                errors += 1
                yield (
                    ERROR,
                    None,
                    None,
                    None,
                    force_str(
                        _(
                            "Some keys were missing: %(keys)s"
                            % {"keys": ", ".join(required_fields)}
                        )
                    ),
                )
            # Abort when there are errors
            if errors:
                if isinstance(data, Worksheet) and len(data.parent.sheetnames) > 1:
                    # Skip this sheet an continue with the next one
                    return
                else:
                    raise NameError("Can't proceed")

            # Create a form class that will be used to validate the data
            fields = [i.name for i in headers if i]
            if hasattr(model, "getModelForm"):
                UploadForm = model.getModelForm(tuple(fields), database=database)
            else:
                UploadForm = modelform_factory(
                    model, fields=tuple(fields), formfield_callback=formfieldCallback
                )
            rowWrapper = rowmapper(headers)

            # Get natural keys for the class
            natural_key = None
            if hasattr(model.objects, "get_by_natural_key"):
                if model._meta.unique_together:
                    natural_key = model._meta.unique_together[0]
                elif hasattr(model, "natural_key") and isinstance(
                    model.natural_key, tuple
                ):
                    natural_key = model.natural_key

        # Case 3: Process a data row
        else:
            try:
                # Step 1: Send a ping-alive message to make the upload interruptable
                if ping:
                    if rownumber % 50 == 0:
                        yield (DEBUG, rownumber, None, None, None)

                # Step 2: Fill the form with data, either updating an existing
                # instance or creating a new one.
                if has_pk_field:
                    # A primary key is part of the input fields
                    try:
                        # Try to find an existing record with the same primary key
                        it = (
                            model.objects.using(database)
                            .only(*fields)
                            .get(pk=rowWrapper[model._meta.pk.name])
                        )
                        form = UploadForm(rowWrapper, instance=it)
                    except model.DoesNotExist:
                        form = UploadForm(rowWrapper)
                        it = None
                elif natural_key:
                    # A natural key exists for this model
                    try:
                        # Build the natural key
                        key = []
                        for x in natural_key:
                            key.append(rowWrapper.get(x, None))
                        # Try to find an existing record using the natural key
                        it = model.objects.get_by_natural_key(*key)
                        form = UploadForm(rowWrapper, instance=it)
                    except model.DoesNotExist:
                        form = UploadForm(rowWrapper)
                        it = None
                    except model.MultipleObjectsReturned:
                        yield (
                            ERROR,
                            rownumber,
                            None,
                            None,
                            force_str(_("Key fields not unique")),
                        )
                        continue
                else:
                    # No primary key required for this model
                    form = UploadForm(rowWrapper)
                    it = None

                # Step 3: Validate the form and model, and save to the database
                if form.has_changed():
                    if form.is_valid():
                        # Save the form
                        obj = form.save(commit=False)
                        if it:
                            changed += 1
                            obj.save(using=database, force_update=True)
                        else:
                            added += 1
                            obj.save(using=database, force_insert=True)
                            # Add the new object in the cache of available keys
                            for x in selfReferencing:
                                if x.cache is not None and obj.pk not in x.cache:
                                    x.cache[obj.pk] = obj
                        if not skip_audit_log and user:
                            if it:
                                Comment(
                                    user_id=user.id,
                                    content_type_id=content_type_id,
                                    object_pk=obj.pk,
                                    object_repr=force_str(obj),
                                    type="change",
                                    comment="Changed %s."
                                    % get_text_list(form.changed_data, "and"),
                                ).save(using=database)
                            else:
                                Comment(
                                    user_id=user.id,
                                    content_type_id=content_type_id,
                                    object_pk=obj.pk,
                                    object_repr=force_str(obj),
                                    type="add",
                                    comment="Added",
                                ).save(using=database)
                    else:
                        # Validation fails
                        for error in form.non_field_errors():
                            errors += 1
                            yield (ERROR, rownumber, None, None, error)
                        for field in form:
                            for error in field.errors:
                                errors += 1
                                yield (
                                    ERROR,
                                    rownumber,
                                    field.name,
                                    rowWrapper[field.name],
                                    error,
                                )

            except Exception as e:
                errors += 1
                yield (ERROR, None, None, None, "Exception during upload: %s" % e)

    yield (
        INFO,
        None,
        None,
        None,
        _(
            "%(rows)d data rows, changed %(changed)d and added %(added)d records, %(errors)d errors, %(warnings)d warnings"
        )
        % {
            "rows": rownumber - 1,
            "changed": changed,
            "added": added,
            "errors": errors,
            "warnings": warnings,
        },
    )


class BulkForeignKeyFormField(forms.fields.Field):
    def __init__(
        self,
        using=DEFAULT_DB_ALIAS,
        field=None,
        required=None,
        label=None,
        help_text="",
        *args,
        **kwargs,
    ):
        forms.fields.Field.__init__(
            self,
            *args,
            required=required if required is not None else not field.null,
            label=label,
            help_text=help_text,
            **kwargs,
        )

        # Build a cache with the list of values - as long as it reasonable fits in memory
        self.model = field.remote_field.model
        field.remote_field.parent_link = (
            True  # A trick to disable the model validation on foreign keys!
        )
        if field.remote_field.model._default_manager.all().using(using).count() > 30000:
            self.queryset = field.remote_field.model._default_manager.all().using(using)
            self.cache = None
        else:
            self.queryset = None
            self.cache = {
                obj.pk: obj
                for obj in field.remote_field.model._default_manager.all().using(using)
            }

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if self.cache is not None:
            try:
                return self.cache[value]
            except KeyError:
                raise forms.ValidationError(
                    _(
                        "Select a valid choice. That choice is not one of the available choices."
                    )
                )
        else:
            try:
                return self.queryset.get(pk=value)
            except self.model.DoesNotExist:
                raise forms.ValidationError(
                    _(
                        "Select a valid choice. That choice is not one of the available choices."
                    )
                )

    def has_changed(self, initial, data):
        return initial != data
