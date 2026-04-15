# nhomgis/forms.py
from django import forms
from .models import Warehouse # Thay 'Warehouse' bằng tên class model thật của bạn
from django.contrib.auth.models import User
from .models import CustomerProfile


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        # Liệt kê các trường cần sửa: tên, địa chỉ, lat, lon, phí cơ bản, phí/km
        fields = ['name', 'address', 'latitude', 'longitude', 'base_fee', 'fee_per_km'] 
        
        # Thêm class CSS (ví dụ: Bootstrap) để giao diện đẹp như trang KingMate của bạn
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên kho'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Địa chỉ kho'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'base_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'fee_per_km': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email']
        labels = {
            'last_name': 'Họ và tên đệm',
            'first_name': 'Tên',
            'email': 'Địa chỉ Email'
        }
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# Cập nhật class ProfileUpdateForm trong form.py
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'address', 'latitude', 'longitude']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: 0987654321'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'id': 'address-input', 
                # XÓA readonly: 'readonly' ĐỂ NGƯỜI DÙNG CÓ THỂ SỬA TÊN
                'placeholder': 'Chọn trên bản đồ hoặc tự nhập tên địa chỉ gợi nhớ...'
            }),
            'latitude': forms.HiddenInput(attrs={'id': 'lat-input'}),
            'longitude': forms.HiddenInput(attrs={'id': 'lon-input'}),
        }