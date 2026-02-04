from django.contrib import admin
from .models import Category, Product, Warehouse, Order, OrderItem

# Đăng ký các bảng để quản lý trong trang Admin
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Warehouse)
admin.site.register(Order)
admin.site.register(OrderItem)