from django.contrib import admin
from .models import ReportingPeriod
from django.utils import timezone
from datetime import datetime, timedelta

@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'deadline', 'is_closed')
    list_filter = ('is_closed',)
    search_fields = ('start_date', 'end_date')
    date_hierarchy = 'start_date'
    readonly_fields = ('deadline',)
    
    def save_model(self, request, obj, form, change):
        """Ensure deadline is set correctly before saving"""
        if not obj.deadline:
            # Calculate Friday of this period
            friday = obj.start_date + timedelta(days=4)
            obj.deadline = timezone.make_aware(
                datetime.combine(friday, datetime.min.time()) + 
                timedelta(hours=23, minutes=59, seconds=59)
            )
        super().save_model(request, obj, form, change)

from django.contrib import admin
from .models import ReportingPeriod, Report, Comment

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('employee', 'period', 'status', 'is_late', 'submitted_at')
    list_filter = ('status', 'is_late', 'period')
    search_fields = ('employee__full_name', 'employee__email', 'accomplishments', 'goals_next_week')
    raw_id_fields = ('employee', 'period')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'is_late')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee', 'period', 'status', 'is_late')
        }),
        ('Report Content', {
            'fields': ('accomplishments', 'goals_next_week', 'blockers', 
                      'support_needed', 'progress_rating', 'additional_notes')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == Report.Status.SUBMITTED:
            return [f.name for f in self.model._meta.fields if f.name not in ['status']]
        return self.readonly_fields     

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'report', 'created_at', 'has_parent')
    list_filter = ('created_at',)
    search_fields = ('author__full_name', 'author__email', 'body')
    raw_id_fields = ('report', 'author', 'parent')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    def has_parent(self, obj):
        return obj.parent is not None
    has_parent.boolean = True
    has_parent.short_description = 'Has Reply'