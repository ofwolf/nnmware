# -*- coding: utf-8 -*-
# Base abstract classed nnmware(c)2012

from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from django.db import models
from django.db.models import permalink
from django.db.models.manager import Manager
from django.template.defaultfilters import truncatewords_html
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.utils.translation.trans_real import get_language
from nnmware.core.managers import MetaLinkManager
from nnmware.core.models import Pic

class Color(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Color'))

    class Meta:
        verbose_name = _("Color")
        verbose_name_plural = _("Colors")
        abstract = True

    def __unicode__(self):
        return self.name

class MetaContent(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    objects = MetaLinkManager()

    class Meta:
        abstract = True


class MetaDate(models.Model):
    created_date = models.DateTimeField(_("Created date"), default=datetime.now())
    updated_date = models.DateTimeField(_("Updated date"), null=True, blank=True)

    class Meta:
        abstract = True

class Unit(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name of unit'))

    class Meta:
        verbose_name = _("Unit")
        verbose_name_plural = _("Units")
        abstract = True

    def __unicode__(self):
        return "%s" % self.name

class Parameter(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name of parameter'))

    class Meta:
        verbose_name = _("Parameter")
        verbose_name_plural = _("Parameters")
        abstract = True

    def __unicode__(self):
        try:
            return "%s (%s)" % (self.name, self.unit.name)
        except :
            return "%s" % self.name


STATUS_DELETE = 0
STATUS_LOCKED = 1
STATUS_PUBLISHED = 2
STATUS_STICKY = 3
STATUS_MODERATION = 4

STATUS_CHOICES = (
    (STATUS_DELETE, _("Deleted")),
    (STATUS_LOCKED, _("Locked")),
    (STATUS_PUBLISHED, _("Published")),
    (STATUS_STICKY, _("Sticky")),
    (STATUS_MODERATION, _("Moderation")),
    )

class MetaData(MetaDate):
    """
    Abstract model that provides meta data for content.
    """
    title = models.CharField(_("Title"), max_length=256)
    slug = models.SlugField(_("URL"), max_length=256, blank=True, unique_for_date="created_date")
    description = models.TextField(_("Description"), blank=True)
    status = models.IntegerField(_("Status"), choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    user = models.ForeignKey(User, blank=True, null=True, verbose_name=_("Author"), related_name="%(app_label)s_%(class)s_user")
    login_required = models.BooleanField(verbose_name=_("Login required"), default=False, help_text=_("Enable this if users must login before access with this objects."))
    allow_comments = models.BooleanField(_("allow comments"), default=True)
    allow_pics = models.BooleanField(_("allow pics"), default=False)
    allow_docs = models.BooleanField(_("allow docs"), default=False)
    comments = models.IntegerField(blank=True, null=True)
    docs = models.IntegerField(blank=True, null=True)
    pics = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = _("MetaData")
        verbose_name_plural = _("MetaDatas")
        ordering = ("-created_date",)
        abstract = True

    objects = Manager()
    search_fields = {"title": 5}
    slug_detail = 'metadata_detail'

    def delete(self, *args, **kwargs):
        self.status = STATUS_DELETE
        self.save()

    def save(self, *args, **kwargs):
        """
        Set default for ``description`` if none
        given.
        """
        if not self.description:
            try:
                self.description = strip_tags(self.description_from_content())
            except:
                self.description = ""
        self.updated_date = datetime.now()
        if not self.slug:
            if not self.id:
                super(MetaData, self).save(*args, **kwargs)
            self.slug = self.id
        super(MetaData, self).save(*args, **kwargs)

    def description_from_content(self):
        """
        Returns the first paragraph of the first content-like field.
        """
        description = ""
        # Use the first TextField if none found.
        if not description:
            for field in self._meta.fields:
                if isinstance(field, models.TextField) and field.name != "description":
                    description = getattr(self, field.name)
                    if description:
                        break
                        # Fall back to the title if description couldn't be determined.
        if not description:
            description = self.title
            # Strip everything after the first paragraph or sentence.
        for end in ("</p>", "<br />", "\n", ". "):
            if end in description:
                description = description.split(end)[0] + end
                break
        else:
            description = truncatewords_html(description, 256)
        return description

    @permalink
    def get_absolute_url(self):
        if self.slug:
            slug = self.slug
        else:
            slug = self.pk
        return (self.slug_detail, (), {
            'year': self.created_date.year,
            'month': self.created_date.strftime('%b').lower(),
            'day': self.created_date.day,
            'slug': slug})

    def is_editable(self, request):
        """
        Restrict in-line editing to the objects's owner and superusers.
        """
        return request.user.is_superuser or request.user == self.user

    def admin_link(self):
        return "<a href='%s'>%s</a>" % (self.get_absolute_url(), _("View on site"))

    admin_link.allow_tags = True
    admin_link.short_description = ""

class MetaName(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    name_en = models.CharField(verbose_name=_("Name(English"), max_length=100, blank=True, null=True)
    enabled = models.BooleanField(verbose_name=_("Enabled in system"), default=True)
    description = models.TextField(verbose_name=_("Description"), blank=True, null=True)
    description_en = models.TextField(verbose_name=_("Description(English)"), blank=True, null=True)
    slug = models.CharField(verbose_name=_('URL-identifier'), max_length=100, blank=True, null=True)
    order_in_list = models.IntegerField(_('Order in list'), default=0)

    class Meta:
        ordering = ['name', ]
        abstract = True

    def __unicode__(self):
        return self.name

    @property
    def get_name(self):
        try:
            if get_language() == 'en':
                if self.name_en:
                    return self.name_en
            return self.name
        except :
            return self.name

    def get_description(self):
        try:
            if get_language() == 'en':
                if self.description_en:
                    return self.description_en
        except :
            pass
        return self.description

    @property
    def main_image(self):
        try:
            return self.all_images[0].pic.url
        except :
            return None

    @property
    def all_images(self):
        return Pic.objects.metalinks_for_object(self).order_by('-primary')

    def save(self, *args, **kwargs):
        if not self.slug:
            if not self.id:
                super(MetaName, self).save(*args, **kwargs)
            self.slug = self.id
        else:
            self.slug = str(self.slug).strip().replace(' ','-')
        super(MetaName, self).save(*args, **kwargs)


class Tree(MetaName):
    """
    Main nodes tree
    """
    parent = models.ForeignKey('self', verbose_name=_("Parent"), blank=True, null=True, related_name="children")
    ordering = models.IntegerField(_("Ordering"), default=0, help_text=_("Override alphabetical order in tree display"))
    rootnode = models.BooleanField(_('Root node'), default=False)
    login_required = models.BooleanField(verbose_name=_("Login required"), default=False, help_text=_("Enable this if users must login before access with this objects."))

    class Meta:
        ordering = ['ordering', ]
        verbose_name = _("Tree")
        verbose_name_plural = _("Trees")
        abstract = True

    def _recurse_for_parents(self, node):
        p_list = []
        if node.parent_id:
            p = node.parent
            p_list.append(p)
            if p != self:
                more = self._recurse_for_parents(p)
                p_list.extend(more)
        if node == self and p_list:
            p_list.reverse()
        return p_list

    def get_absolute_url(self):
        parents = self._recurse_for_parents(self)
        slug_list = [node.slug for node in parents]
        if slug_list:
            slug_list = "/".join(slug_list) + "/"
        else:
            slug_list = ""
        return reverse(self.slug_detail,
            kwargs={'parent_slugs': slug_list, 'slug': self.slug})

    def get_separator(self):
        return ' > '

    def _parents_repr(self):
        name_list = [node.name for node in self._recurse_for_parents(self)]
        return self.get_separator().join(name_list)

    _parents_repr.short_description = _("Tree parents")

    def get_url_name(self):
        # Get all the absolute URLs and names for use in the site navigation.
        name_list = []
        url_list = []
        for node in self._recurse_for_parents(self):
            name_list.append(node.name)
            url_list.append(node.get_absolute_url())
        name_list.append(self.name)
        url_list.append(self.get_absolute_url())
        return zip(name_list, url_list)

    def __unicode__(self):
        name_list = [node.name for node in self._recurse_for_parents(self)]
        name_list.append(self.name)
        return self.get_separator().join(name_list)

    def save(self, *args, **kwargs):
        if self.id:
            if self.parent and self.parent_id == self.id:
                raise ValidationError(_("You must not save a category in itself!"))
            for p in self._recurse_for_parents(self):
                if self.id == p.id:
                    raise ValidationError(_("You must not save a category in itself!"))
        super(Tree, self).save(*args, **kwargs)

    def _flatten(self, L):
        """
        Taken from a python newsgroup post
        """
        if type(L) != type([]):
            return [L]
        if not L:
            return L
        return self._flatten(L[0]) + self._flatten(L[1:])

    def _recurse_for_children(self, node, only_active=False):
        children = [node]
        for child in node.children.all():
            if child != self:
                if not only_active:
                    children_list = self._recurse_for_children(child, only_active=only_active)
                    children.append(children_list)
        return children

    def get_all_children(self, only_active=False, include_self=False):
        """
        Gets a list of all of the children categories.
        """
        children_list = self._recurse_for_children(self, only_active=only_active)
        if include_self:
            ix = 0
        else:
            ix = 1
        flat_list = self._flatten(children_list[ix:])
        return flat_list

class MetaLink(models.Model):
    # Generic Foreign Key Fields
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(_('object ID'), null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    primary = models.BooleanField(_('Is primary'), default=False)

    class Meta:
        abstract = True

    objects = MetaLinkManager()

    def get_content_object(self):
        """
        Wrapper around the GenericForeignKey due to compatibility reasons
        and due to ``list_display`` limitations.
        """
        return self.content_object

    def __unicode__(self):
        if len(self.description) > 50:
            return self.description[:50] + "..."
        return self.description[:50]

    def admin_link(self):
        return "<a href='%s'>%s</a>" % (self.get_absolute_url(), _("View on site"))

    admin_link.allow_tags = True
    admin_link.short_description = ""


DOC_FILE = 0
DOC_IMAGE = 1

DOC_TYPE = (
    (DOC_FILE, _("File")),
    (DOC_IMAGE, _("Image")),
    )


class MetaFile(MetaDate):
    user = models.ForeignKey(User, blank=True, null=True, verbose_name=_("Author"), related_name="%(class)s_user")
    description = models.CharField(verbose_name=_("Description"), max_length=256, blank=True)
    size = models.IntegerField(editable=False, null=True, blank=True)
    ordering = models.IntegerField(_("Ordering"), default=0, help_text=_("Override alphabetical order in list display"))
    locked = models.BooleanField(_('Is locked'), default=False)

    class Meta:
        abstract = True

class MetaIP(models.Model):
    ip = models.IPAddressField(verbose_name=_('IP'), null=True, blank=True)
    user_agent = models.CharField(verbose_name=_('User Agent'), null=True, blank=True, max_length=255)

    class Meta:
        abstract = True
