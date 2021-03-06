from django.contrib import admin
from .models import Team, User, Paper, PaperImage, Annotation, Comment, Token, Tag, TagPaper, Watch, PaperOpen, AnnotationOpen

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    pass

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    pass

@admin.register(PaperImage)
class PaperImageAdmin(admin.ModelAdmin):
    pass

@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    pass

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    pass

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass

@admin.register(TagPaper)
class TagPaperAdmin(admin.ModelAdmin):
    pass

@admin.register(Watch)
class WatchAdmin(admin.ModelAdmin):
    pass

@admin.register(PaperOpen)
class PaperOpenAdmin(admin.ModelAdmin):
    pass

@admin.register(AnnotationOpen)
class AnnotationOpenAdmin(admin.ModelAdmin):
    pass

