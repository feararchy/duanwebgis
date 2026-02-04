from django.db import models
from django.contrib.auth.models import User # Dùng bảng User có sẵn của Django

# 1. Danh Mục
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    def __str__(self): return self.name

# 2. Sản Phẩm
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Danh mục")
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    price = models.IntegerField(verbose_name="Giá bán")
    unit = models.CharField(max_length=50, verbose_name="Đơn vị tính")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    stock_quantity = models.IntegerField(default=0, verbose_name="Tồn kho")
    image_url = models.CharField(max_length=500, blank=True, verbose_name="Link ảnh")
    def __str__(self): return self.name

# 3. Kho Hàng (Phục vụ GIS)
class Warehouse(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên kho")
    address = models.CharField(max_length=200, verbose_name="Địa chỉ")
    latitude = models.FloatField(verbose_name="Vĩ độ")  # Tọa độ Y
    longitude = models.FloatField(verbose_name="Kinh độ") # Tọa độ X

    def __str__(self): return self.name

# 4. Hóa Đơn (Đơn hàng)
class Order(models.Model):
    STATUS_CHOICES = [
        ('CHỜ XÁC NHẬN', 'Chờ xác nhận'),
        ('ĐANG GIAO', 'Đang giao'),
        ('ĐÃ GIAO', 'Đã giao'),
        ('ĐÃ HỦY', 'Đã hủy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Khách hàng")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đặt")
    total_amount = models.IntegerField(default=0, verbose_name="Tổng tiền hàng")
    shipping_fee = models.IntegerField(default=0, verbose_name="Phí vận chuyển")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='CHỜ XÁC NHẬN')
    
    # Lưu thông tin GIS của khách để shipper biết đường
    shipping_address = models.CharField(max_length=255, verbose_name="Địa chỉ giao")
    customer_lat = models.FloatField(null=True, blank=True, verbose_name="Vĩ độ khách")
    customer_lon = models.FloatField(null=True, blank=True, verbose_name="Kinh độ khách")

    def __str__(self):
        return f"Đơn #{self.id} - {self.user.username}"

# 5. Chi Tiết Hóa Đơn (Lưu từng món trong đơn)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_purchase = models.IntegerField(verbose_name="Giá lúc mua") # Lưu giá phòng khi giá gốc đổi

    def total_price(self):
        return self.quantity * self.price_at_purchase