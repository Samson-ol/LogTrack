from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
	class Meta:
		verbose_name = 'Custom User'
		verbose_name_plural = 'Custom Users'
	USER_TYPE_CHOICES = (
		('student', 'Student'),
		('supervisor', 'Supervisor'),
	)
	email = models.EmailField(unique=True)
	user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
	title = models.CharField(max_length=20, blank=True, null=True, help_text='Title for supervisors (e.g., Dr, Prof, Mr, Mrs)')
	matric_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
	supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'user_type': 'supervisor'}, related_name='students')

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	def __str__(self):
		return self.email

# Submission model for student daily logs
class Submission(models.Model):
	student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submissions')
	matric_number = models.CharField(max_length=20)
	overview = models.CharField(max_length=255, blank=True, null=True, help_text='Short summary of what you did today')
	text = models.TextField()
	file = models.FileField(upload_to='submissions/', blank=True, null=True)
	date = models.DateTimeField(auto_now_add=True)
	approved = models.BooleanField(default=False)
	reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
	remark = models.TextField(blank=True, null=True, help_text='Supervisor remark or comment for this submission')

	def __str__(self):
		return f"{self.matric_number} - {self.date.strftime('%Y-%m-%d %H:%M') if self.date else ''}"