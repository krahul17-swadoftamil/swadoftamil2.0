import os
from django.conf import settings
from django.http import FileResponse, Http404


def download_report(request, filename):
    """Admin-protected download view for report files.

    `filename` should be a basename (no directories). Only files under
    the reports directory are allowed.
    """
    # reports directory under BASE_DIR/analytics/reports
    reports_dir = os.path.join(settings.BASE_DIR, 'analytics', 'reports')
    # prevent traversal
    if os.path.sep in filename or filename.startswith('..'):
        raise Http404("Invalid filename")

    file_path = os.path.join(reports_dir, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("File not found")

    try:
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    except Exception:
        raise Http404("Unable to open file")
