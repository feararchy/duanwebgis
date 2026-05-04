from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField  # 1. Import thư viện ở đầu file
import random
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator

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
    
    
    # 2. Thay đổi TextField thành RichTextField
    description = RichTextField(blank=True, null=True, verbose_name="Mô tả") 
    
    stock_quantity = models.IntegerField(default=0, verbose_name="Tồn kho")
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
# Thêm Comment model vào models.py
class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Nâng cấp: Bình luận cha (để làm Reply) và Lượt thích (Like)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return f"Bình luận của {self.user.username} trên bài: {self.post.title}"
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
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kho xuất hàng")
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
# Thêm vào cuối file models.py

# --- 6. QUẢN LÝ TỒN KHO & LỊCH SỬ XUẤT NHẬP ---
class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stocks', verbose_name="Kho hàng")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks', verbose_name="Sản phẩm")
    quantity = models.IntegerField(default=0, verbose_name="Số lượng tồn tại kho")

    class Meta:
        unique_together = ('warehouse', 'product') # Ràng buộc 1 kho chỉ có 1 dòng tồn kho cho 1 sản phẩm

    def __str__(self):
        return f"{self.warehouse.name} - {self.product.name}: {self.quantity}"

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IMPORT', 'Nhập hàng'),
        ('EXPORT', 'Xuất hàng'),
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Kho hàng")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Sản phẩm")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="Loại giao dịch")
    quantity = models.PositiveIntegerField(verbose_name="Số lượng")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Ngày thực hiện")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Người thực hiện")
    # CHỈ THÊM DÒNG NÀY (Giữ nguyên các trường trên của bạn)
    batch_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Mã lô/phiếu")

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"
    
# thongtin
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Số điện thoại")
    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ cụ thể")
    
    # THÊM 2 TRƯỜNG NÀY
    latitude = models.FloatField(null=True, blank=True, verbose_name="Vĩ độ")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Kinh độ")

    def __str__(self):
        return f"Hồ sơ của {self.user.username}"

#EmailVerification
class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Mã hết hạn sau 5 phút
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"OTP của {self.user.username}: {self.code}"
    

    
# --- 7. QUẢN LÝ TRANG GIỚI THIỆU ---
class AboutPage(models.Model):
    title = models.CharField(max_length=255, default="Giới thiệu về KINGMATE", verbose_name="Tiêu đề chính")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class AboutSection(models.Model):
    SECTION_TYPES = [
        ('TEXT', 'Văn bản thường'),
        ('FEATURE', 'Tính năng (Có Icon)'),
        ('CONTACT', 'Khối Liên hệ'),
    ]
    # THÊM MỚI TỪ ĐÂY
    ALIGN_CHOICES = [
        ('text-start', 'Căn trái'),
        ('text-center', 'Căn giữa'),
        ('text-end', 'Căn phải'),
        ('text-justify', 'Căn đều'),
    ]
    
    page = models.ForeignKey(AboutPage, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=10, choices=SECTION_TYPES, default='TEXT')
    text_align = models.CharField(max_length=20, choices=ALIGN_CHOICES, default='text-start') # TRƯỜNG MỚI
    # ĐẾN ĐÂY
    
    heading = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tiêu đề khối")
    content = models.TextField(blank=True, null=True, verbose_name="Nội dung chi tiết")
    icon_class = models.CharField(max_length=50, blank=True, null=True, help_text="VD: bi-truck, bi-shield-check")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.page.title} - {self.heading}"
    
    # thongtin
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # --- SỬA LẠI TRƯỜNG PHONE NHƯ SAU ---
    phone_regex = RegexValidator(
        regex=r'^\d{10}$', 
        message="Số điện thoại không hợp lệ. Vui lòng nhập đúng 10 chữ số."
    )
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=10, # Đổi từ 15 thành 10
        blank=True, 
        null=True, 
        verbose_name="Số điện thoại"
    )
    # -------------------------------------

    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ cụ thể")
    
    # THÊM 2 TRƯỜNG NÀY
    latitude = models.FloatField(null=True, blank=True, verbose_name="Vĩ độ")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Kinh độ")

    def __str__(self):
        return f"Hồ sơ của {self.user.username}"