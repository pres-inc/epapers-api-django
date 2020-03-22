from rest_framework import serializers
from ..models import Paper, Team, User, PaperImage, Annotation, Comment

class UserSerializerForPaper(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'mail', 'color', 'team_id')

class PaperImageSerializerForPaperInfo(serializers.ModelSerializer):
    class Meta:
        model = PaperImage
        fields = ('url', 'page')

class AnnotationSerializerForPaperInfo(serializers.ModelSerializer):
    comment_count = serializers.SerializerMethodField()
    x0 = serializers.SerializerMethodField()
    y0 = serializers.SerializerMethodField()
    x1 = serializers.SerializerMethodField()
    y1 = serializers.SerializerMethodField()
    user = UserSerializerForPaper(read_only=True)
    class Meta:
        model = Annotation
        fields = ('pk', 'memo', 'comment_count', 'x0', 'y0', 'x1', 'y1', 'user', 'page')

    def get_comment_count(self, obj):
        return Comment.objects.filter(annotation=obj.pk).count()
    
    def get_x0(self, obj):
        return int(obj.coordinate.split(",")[0])
    
    def get_y0(self, obj):
        return int(obj.coordinate.split(",")[1])
    
    def get_x1(self, obj):
        return int(obj.coordinate.split(",")[2])
    
    def get_y1(self, obj):
        return int(obj.coordinate.split(",")[3])
    




class PaperInfoSerializer(serializers.ModelSerializer):
    team_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    pk = serializers.SerializerMethodField()
    pages = serializers.SerializerMethodField()
    annotations = serializers.SerializerMethodField()
    annotationed_users = serializers.SerializerMethodField()
    user = UserSerializerForPaper(read_only=True)
    class Meta:
        model = Paper
        fields = ('pk', 'title', 'team_id', 'user_id', 'created_at', 'user', 'pages', 'annotations', 'annotationed_users')
        read_only_fields = ('created_at', 'pk', )

    def create(self, validated_date):

        validated_date['team'] = validated_date.get('team_id', None)
        validated_date['user'] = validated_date.get('user_id', None)

        if validated_date['team'] is None or validated_date['user'] is None:
            raise serializers.ValidationError("team or user not found.") 

        del validated_date['team_id']
        del validated_date['user_id']

        return Paper.objects.create(**validated_date)
    
    def get_pk(self, obj):
        return int(obj.pk)
    
    def get_pages(self, obj):
        serializer = PaperImageSerializerForPaperInfo(PaperImage.objects.filter(paper_id=obj.pk).order_by("page"), many=True)
        return serializer.data
    
    def get_annotations(self, obj):
        serializer = AnnotationSerializerForPaperInfo(Annotation.objects.filter(paper=obj.pk), many=True)
        return serializer.data

    def get_annotationed_users(self, obj):
        user_id_list = Annotation.objects.filter(paper=obj.pk).values_list('user', flat=True)
        serializer = UserSerializerForPaper(User.objects.filter(id__in=user_id_list), many=True)
        for i,data in enumerate(serializer.data):
            annotaton_count = Annotation.objects.filter(user_id=data["id"], paper_id=obj.pk).count()
            serializer.data[i].update(annotation_count=annotaton_count)
        return serializer.data