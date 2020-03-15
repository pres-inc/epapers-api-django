from django.contrib import admin
from .models import Team, User, Paper, PaperImage, Annotation, Comment

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

