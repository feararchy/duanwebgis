from django.db import models
from django.contrib.auth.models import User

# 1. Danh Mục
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    
    def __str__(self): 
        return self.name

# 2. Sản Phẩm
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Danh mục")
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    price = models.IntegerField(verbose_name="Giá bán")
    unit = models.CharField(max_length=50, verbose_name="Đơn vị tính")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    stock_quantity = models.IntegerField(default=0, verbose_name="Tồn kho")
    
    # Sử dụng ImageField để up ảnh từ máy tính
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Ảnh chính")
    
    def __str__(self): 
        return self.name

# --- TÍNH NĂNG: LƯỚT NHIỀU ẢNH SẢN PHẨM ---
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_gallery/', verbose_name="Ảnh phụ")
    
    def __str__(self): 
        return f"Ảnh phụ của {self.product.name}"

# --- TÍNH NĂNG: ĐÁNH GIÁ 5 SAO CHO TỪNG SẢN PHẨM ---
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stars = models.IntegerField(default=5, verbose_name="Số sao (1-5)")
    comment = models.TextField(verbose_name="Bình luận")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') 

    def __str__(self): 
        return f"{self.user.username} đánh giá {self.product.name}"

# --- TÍNH NĂNG: ĐÁNH GIÁ CHUNG TOÀN BỘ CỬA HÀNG ---
class StoreReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stars = models.IntegerField(default=5, verbose_name="Số sao (1-5)")
    comment = models.TextField(verbose_name="Nhận xét")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user',) # Khóa đơn: Mỗi user chỉ đánh giá cửa hàng 1 lần

    def __str__(self):
        return f"{self.user.username} đánh giá cửa hàng"

# --- TÍNH NĂNG: BLOG / TIN TỨC ---
class Post(models.Model):
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    thumbnail = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name="Ảnh bìa")
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.title

# 3. Kho Hàng (Phục vụ bài toán WebGIS)
class Warehouse(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên kho hàng")
    address = models.CharField(max_length=500, verbose_name="Địa chỉ")
    
    latitude = models.FloatField(verbose_name="Vĩ độ")
    longitude = models.FloatField(verbose_name="Kinh độ")
    
    base_fee = models.IntegerField(default=15000, verbose_name="Phí cố định (VNĐ)")
    fee_per_km = models.IntegerField(default=5000, verbose_name="Phí mỗi KM (VNĐ)")

    def __str__(self): 
        return self.name

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
    
    shipping_fee = models.IntegerField(default=0, verbose_name="Phí vận chuyển")
    total_amount = models.IntegerField(default=0, verbose_name="Tổng tiền (Hàng + Ship)")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='CHỜ XÁC NHẬN')
    
    # Thông tin Giao hàng lưu tọa độ (Phục vụ bản đồ Admin)
    shipping_address = models.TextField(verbose_name="Địa chỉ giao")
    customer_lat = models.FloatField(null=True, blank=True, verbose_name="Vĩ độ khách")
    customer_lon = models.FloatField(null=True, blank=True, verbose_name="Kinh độ khách")

    def __str__(self):
        return f"Đơn #{self.id} - {self.user.username}"
    
    @property
    def product_total(self):
        return self.total_amount - self.shipping_fee

# 5. Chi Tiết Hóa Đơn
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_purchase = models.IntegerField(verbose_name="Giá lúc mua")

    def total_price(self):
        return self.quantity * self.price_at_purchase