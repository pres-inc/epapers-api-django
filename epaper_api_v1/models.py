from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100, default="New Team")

class User(models.Model):
   id = models.CharField(primary_key=True, max_length=100)
   name = models.CharField(max_length=100, default="名無し")
   mail = models.CharField(max_length=100)
   password = models.CharField(max_length=100)
   color = models.CharField(max_length=100, default="#FFFFFF")
   team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name="user_team_id")
   is_owner = models.BooleanField(null=False, default=False)
   created_at = models.DateTimeField(auto_now_add=True)

class Paper(models.Model):
    title = models.CharField(max_length=100, default="New Paper")
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name="paper_team_id")
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="paper_user_id")
    thumbnail_url = models.CharField(max_length=300, default="") # 一旦使わない
    #auters = models.CharField(max_length=300, default="") # 一旦使わない

class PaperImage(models.Model):
    url = models.CharField(max_length=300, default="")
    paper = models.ForeignKey('Paper', on_delete=models.CASCADE, related_name="paper_id")
    page = models.IntegerField(default=0)

class Annotation(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="annotation_user_id")
    memo = models.CharField(max_length=500, default="")
    coordinate = models.CharField(max_length=100, default="")
    page = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="comment_user_id")
    comment = models.CharField(max_length=500, default="")
    is_image = models.BooleanField(null=False, default=False)
    annotation = models.ForeignKey('Annotation', on_delete=models.CASCADE, related_name="annotation_id")
    created_at = models.DateTimeField(auto_now_add=True)    
