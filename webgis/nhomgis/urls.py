from django.urls import path
from . import views

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
    
    path('warehouses/', views.warehouse_list, name='warehouses'),
    path('orders/', views.orders_list, name='orders'),
    path('orders/status/', views.order_update_status, name='order_status'),
    path('users/', views.users_list, name='users'),
    path('users/delete/<int:id>/', views.user_delete, name='user_delete'),
    
    # Bản đồ Admin
    path('dashboard/map/', views.admin_map_view, name='admin_map'),
    path('api/orders-locations/', views.api_orders_locations, name='api_orders_locations'),
]