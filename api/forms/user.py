from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from api.models.user import User

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "full_name", "phone", "role")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Пароль (хэш)")

    class Meta:
        model = User
        fields = (
            "email", "full_name", "phone", "role",
            "password", "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions",
        )
