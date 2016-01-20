from django.contrib import admin

# Register your models here.

from .models import Block
from .models import DrawingStatus
from .models import Department
from .models import Drawing
from .models import DrawingAttachment
from .models import Revision
from .models import Comment
from .models import Reply

admin.site.register(Block)
admin.site.register(DrawingStatus)
admin.site.register(Department)
admin.site.register(DrawingAttachment)
admin.site.register(Drawing)
admin.site.register(Revision)
admin.site.register(Comment)
admin.site.register(Reply)

