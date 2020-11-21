from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import Group

class TeknologOIDCAB(OIDCAuthenticationBackend):
    def get_username(self, claims):
        return claims.get('preferred_username')

    def create_user(self, claims):
        user = super(TeknologOIDCAB, self).create_user(claims)

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        groups = self.get_or_create_groups(claims.get('groups'))
        user.groups.set(groups)
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        groups = self.get_or_create_groups(claims.get('groups'))
        user.groups.set(groups)
        user.save()

        return user

    def get_or_create_groups(self, group_names):
        groups = []
        for group_name in group_names:
            obj, _ = Group.objects.get_or_create(name=group_name)
            groups.append(obj)

        return groups
