from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
	"""
	A user profile model for tracking additional user metadata.
	"""
	user = models.OneToOneField(User, related_name='profile')

	# Used to enable a user's publicly accessible profile
	public = models.BooleanField(default=False)

	# Used to track how this user profile object was created
	source = models.CharField(max_length=10, default="admin")

	def __str__(self):
		return u'%s <%s>' % (self.user.get_full_name(), self.user.email,)

	def get_absolute_url(self):
		return reverse('user_profile', kwargs={'user_id': self.user.pk})