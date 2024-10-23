from django.urls import reverse

def reverse_with_next(url_name, next_url):
    url = reverse(url_name)
    url+= f"?next={next_url}"
    return url

"""Checks if user is logged in"""
class LogInTester:
    def _is_logged_in(self):
         return '_auth_user_id' in self.client.session.keys()
