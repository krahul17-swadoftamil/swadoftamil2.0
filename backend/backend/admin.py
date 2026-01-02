# backend/backend/admin.py

from django.contrib import admin
from django.contrib.admin import AdminSite

class SwadAdminSite(AdminSite):
    # Keep a local class for branding/Media only. Do NOT replace
    # the global `admin.site` instance here as that would detach
    # already-registered ModelAdmin instances and hide them from
    # the index view.
    site_header = "Swad of Tamil Admin"
    site_title = "Swad Admin"
    index_title = "Kitchen & ERP Control"

    class Media:
        css = {
            "all": (
                "admin/swadtamil_admin.css",
                "admin/swadtamil_admin_extra.css",
            )
        }
        js = (
            "admin/swadtamil_admin.js",
        )


# Apply branding to the existing admin.site instead of replacing it
admin.site.site_header = SwadAdminSite.site_header
admin.site.site_title = SwadAdminSite.site_title
admin.site.index_title = SwadAdminSite.index_title
admin.site.__class__.Media = SwadAdminSite.Media
