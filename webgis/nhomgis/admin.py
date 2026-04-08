from django.contrib import admin
from .models import Category, Product, ProductImage, Warehouse, Order, Post, StoreReview

# Hiện thêm các dòng để chọn nhiều ảnh phụ cho sản phẩm
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3 # Mặc định hiện sẵn 3 ô để chọn ảnh

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('name', 'category', 'price', 'stock_quantity')

# Đăng ký các model còn lại (Đã xóa dòng Category bị lặp)
admin.site.register(Category)
admin.site.register(Warehouse)
admin.site.register(Order)
admin.site.register(Post)
admin.site.register(StoreReview)