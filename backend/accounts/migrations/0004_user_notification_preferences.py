from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_password_reset_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_notifications_enabled',
            field=models.BooleanField(default=True, help_text='Whether to receive email notifications'),
        ),
        migrations.AddField(
            model_name='user',
            name='notify_on_comment_added',
            field=models.BooleanField(default=True, help_text='Notify when a comment is added to your report'),
        ),
        migrations.AddField(
            model_name='user',
            name='notify_on_deadline_approaching',
            field=models.BooleanField(default=True, help_text='Receive deadline approaching notifications'),
        ),
        migrations.AddField(
            model_name='user',
            name='notify_on_report_reviewed',
            field=models.BooleanField(default=True, help_text='Notify when your report is reviewed'),
        ),
        migrations.AddField(
            model_name='user',
            name='notify_on_report_submitted',
            field=models.BooleanField(default=True, help_text='Notify when employee submits a report'),
        ),
        migrations.AddField(
            model_name='user',
            name='notify_on_weekly_reminder',
            field=models.BooleanField(default=True, help_text='Receive weekly reminders to submit reports'),
        ),
    ]
