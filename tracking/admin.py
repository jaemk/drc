from django.contrib import admin

# Register your models here.

from .models import User
from .models import Block
from .models import Phase
from .models import DrawingStatus
from .models import Department
from .models import Drawing
from .models import DrawingAttachment
from .models import Revision
from .models import RevisionAttachment
from .models import Comment
from .models import CommentAttachment
from .models import Reply
from .models import ReplyAttachment
from .models import Project

admin.site.register(Block)
admin.site.register(Phase)
admin.site.register(DrawingStatus)
admin.site.register(Department)
admin.site.register(DrawingAttachment)
admin.site.register(Drawing)
admin.site.register(Revision)
admin.site.register(RevisionAttachment)
admin.site.register(Comment)
admin.site.register(CommentAttachment)
admin.site.register(Reply)
admin.site.register(ReplyAttachment)
admin.site.register(Project)

