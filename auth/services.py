from typing import Optional

from auth.models import User


class AuthService:
    def login(self, token: str) -> Optional[User]:
        return User.objects.filter(token=token, is_active=True).select_related("role").first()

    def update_profile(self, user_id: int, data: dict) -> bool:
        updated = User.objects.filter(id=user_id).update(**data)
        return updated > 0

    def change_token(self, user_id: int, old_token: str, new_token: str) -> bool:
        user = User.objects.filter(id=user_id, token=old_token).first()
        if not user:
            return False
        user.token = new_token
        user.save(update_fields=["token"])
        return True
