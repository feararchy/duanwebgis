from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. KHÁCH HÀNG (PUBLIC)
    # ==========================================
    path('', views.home, name='home'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'), 
    path('store-review/', views.add_store_review, name='add_store_review'),
    
    # --- BLOG ---
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<int:id>/', views.blog_detail, name='blog_detail'),
    path('blog/create/', views.blog_create, name='blog_create'), 

    # --- TÀI KHOẢN ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-new-password/', views.reset_new_password, name='reset_new_password'),
    path('about/', views.about_view, name='about'),

    # --- GIỎ HÀNG & THANH TOÁN ---
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('address/delete/<int:id>/', views.delete_address, name='delete_address'),

    # --- GIS: TÍNH PHÍ VẬN CHUYỂN ---
    path('shipping/', views.shipping_page, name='shipping_page'),
    path('api/calculate-shipping/', views.api_calculate_shipping, name='api_calculate_shipping'),
    path('warehouses/public/', views.public_warehouses, name='public_warehouses'),

    # ==========================================
    # 2. QUẢN TRỊ VIÊN (ADMIN)
    # ==========================================
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # --- SẢN PHẨM ---
    path('products/', views.products_list, name='products'),
    path('product/form/', views.product_form, name='product_form'), # ĐÃ FIX: Khớp với HTML
    path('product/form/<int:id>/', views.product_form, name='product_form'), # ĐÃ FIX: Khớp với HTML
    path('product/save/', views.product_save, name='product_save'),
    path('product/delete/<int:id>/', views.product_delete, name='product_delete'),
    
    # --- DANH MỤC ---
    path('categories/', views.categories_list, name='categories'),
    path('category/form/', views.category_form, name='category_form'), # ĐÃ FIX: Khớp với HTML
    path('category/save/', views.category_save, name='category_save'),
    path('category/delete/<int:id>/', views.category_delete, name='category_delete'),
    
    # --- KHO HÀNG ---
    path('warehouses/', views.warehouse_list, name='warehouses'),
    path('warehouse/form/', views.warehouse_form, name='warehouse_form'), 
    path('warehouse/form/<int:id>/', views.warehouse_form, name='warehouse_form'), 
    path('warehouse/save/', views.warehouse_save, name='warehouse_save'), 
    path('warehouse/delete/<int:id>/', views.warehouse_delete, name='warehouse_delete'), 

    # --- ĐƠN HÀNG ---
    path('orders/', views.orders_list, name='orders'),
    path('orders/status/', views.order_update_status, name='order_update_status'),
    
    # --- NGƯỜI DÙNG ---
    path('users/', views.users_list, name='users'),
    path('users/delete/<int:id>/', views.user_delete, name='user_delete'),
    path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'), # THÊM DÒNG NÀY
    
    # --- BẢN ĐỒ ADMIN ---
    path('dashboard/map/', views.admin_map_view, name='admin_map'),
    path('api/orders-locations/', views.api_orders_locations, name='api_orders_locations'),
]