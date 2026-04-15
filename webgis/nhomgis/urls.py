from django.urls import path,re_path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- 1. KHÁCH HÀNG (PUBLIC) ---
    path('', views.home, name='home'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'), 
    path('store-review/', views.add_store_review, name='add_store_review'), # MỚI: Đánh giá cửa hàng
    
    # --- BLOG ---
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<int:id>/', views.blog_detail, name='blog_detail'),
    path('blog/create/', views.blog_create, name='blog_create'), # MỚI: Tạo bài viết Blog

    # Tài khoản
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'), # <-- Dòng MỚI THÊM
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # Giỏ hàng & Thanh toán
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),

    # Tính phí vận chuyển (GIS)
    path('shipping/', views.shipping_page, name='shipping_page'),
    path('api/calculate-shipping/', views.api_calculate_shipping, name='api_calculate_shipping'),

    # --- 2. QUẢN TRỊ VIÊN (ADMIN) ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.products_list, name='products'),
    path('product/add/', views.product_form, name='product_add'),
    path('product/edit/<int:id>/', views.product_form, name='product_edit'),
    path('product/save/', views.product_save, name='product_save'),
    path('product/delete/<int:id>/', views.product_delete, name='product_delete'),
    
    path('categories/', views.categories_list, name='categories'),
    path('category/add/', views.category_form, name='category_add'),
    path('category/save/', views.category_save, name='category_save'),
    path('category/delete/<int:id>/', views.category_delete, name='category_delete'),
    
    # ... (các url admin khác) ...
    path('warehouses/', views.warehouse_list, name='warehouses'),
    path('warehouse/edit/<int:id>/', views.warehouse_form, name='warehouse_edit'), # Dòng thêm mới
    path('warehouse/save/', views.warehouse_save, name='warehouse_save'),          # Dòng thêm mới
    path('orders/', views.orders_list, name='orders'),
    path('orders/status/', views.order_update_status, name='order_status'),
    path('users/', views.users_list, name='users'),
    path('users/delete/<int:id>/', views.user_delete, name='user_delete'),
    
    # Bản đồ Admin
    path('dashboard/map/', views.admin_map_view, name='admin_map'),
    path('api/orders-locations/', views.api_orders_locations, name='api_orders_locations'),


    
    # MỚI: Quản lý Xuất/Nhập hàng
    path('inventory/', views.inventory_manage, name='inventory_manage'),
    
    path('orders/', views.orders_list, name='orders'),
    # ...

    path('inventory/', views.inventory_manage, name='inventory_manage'),
    # MỚI: Đường dẫn in phiếu xuất/nhập
    path('inventory/print/<int:transaction_id>/', views.print_inventory_receipt, name='print_inventory_receipt'),
      # Dòng thêm mới

    path('gioi-thieu/', views.about, name='about'),

    path('verify-email/', views.verify_email, name='verify_email'),

    # Quên mật khẩu (Dùng hệ thống sẵn có của Django gửi link vào Mailtrap)
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    # Thêm vào urlpatterns trong urls.py
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-password-new/', views.reset_password_new, name='reset_password_new'),



    re_path(r'^.*$', views.custom_catch_all_404),
]