from django.urls import path
from . import views

urlpatterns = [
    # --- PHẦN 1: KHÁCH HÀNG (PUBLIC) ---
    path('', views.home, name='home'),                              # Trang chủ
    path('product/<int:id>/', views.product_detail, name='product_detail'), # Chi tiết sản phẩm
    
    # Tài khoản
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Giỏ hàng & Thanh toán
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),


    # --- PHẦN 2: QUẢN TRỊ VIÊN (ADMIN) ---
    path('dashboard/', views.dashboard, name='dashboard'),          # Bảng điều khiển

    # Quản lý Sản phẩm
    path('products/', views.products_list, name='products'),
    path('product/add/', views.product_form, name='product_add'),       # Thêm mới
    path('product/edit/<int:id>/', views.product_form, name='product_edit'), # <-- MỚI THÊM: Sửa sản phẩm
    path('product/save/', views.product_save, name='product_save'),     # Lưu (Xử lý cả thêm và sửa)
    path('product/delete/<int:id>/', views.product_delete, name='product_delete'),

    # Quản lý Danh mục
    path('categories/', views.categories_list, name='categories'),
    path('category/add/', views.category_form, name='category_add'),
    path('category/save/', views.category_save, name='category_save'),
    path('category/delete/<int:id>/', views.category_delete, name='category_delete'),

    # Quản lý Kho hàng (GIS) - MỚI THÊM CHO ĐỒNG BỘ
    path('warehouses/', views.warehouse_list, name='warehouses'),

    # Quản lý Người dùng
    path('users/', views.users_list, name='users'),
    path('users/delete/<int:id>/', views.user_delete, name='user_delete'),

    # Quản lý Hóa đơn (Orders)
    path('orders/', views.orders_list, name='orders'),
    path('orders/status/', views.order_update_status, name='order_status'), 
]