from django.urls import path, re_path
from . import views

urlpatterns = [
    # PUBLIC
    path('', views.home, name='home'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('store-review/', views.add_store_review, name='add_store_review'),
    
    #BLOG
    path('dashboard/blogs/', views.admin_blogs, name='admin_blogs'),
    path('dashboard/blogs/add/', views.admin_blog_form, name='admin_blog_add'),
    path('dashboard/blogs/edit/<int:id>/', views.admin_blog_form, name='admin_blog_edit'),
    path('dashboard/blogs/save/', views.admin_blog_save, name='admin_blog_save'),
    path('dashboard/blogs/delete/<int:id>/', views.admin_blog_delete, name='admin_blog_delete'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<int:id>/', views.blog_detail, name='blog_detail'),
    path('comment/like/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    
    path('about/', views.about, name='about'),

    # AUTH
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-password/', views.reset_password_new, name='reset_password_new'),
    
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # SHIPPING
    path('shipping/', views.shipping_page, name='shipping'),
    path('api/calculate-shipping/', views.api_calculate_shipping, name='api_calculate_shipping'),

    # ADMIN
    path('dashboard/', views.dashboard, name='dashboard'),

    # BLOGS (QUẢN LÝ BÀI VIẾT CHO ADMIN)
    path('dashboard/blogs/', views.admin_blogs, name='admin_blogs'),
    path('dashboard/blogs/add/', views.admin_blog_form, name='admin_blog_add'),
    path('dashboard/blogs/edit/<int:id>/', views.admin_blog_form, name='admin_blog_edit'),
    path('dashboard/blogs/save/', views.admin_blog_save, name='admin_blog_save'),
    path('dashboard/blogs/delete/<int:id>/', views.admin_blog_delete, name='admin_blog_delete'),
    
    # PRODUCTS (GIỮ NGUYÊN)
    path('dashboard/products/', views.products_list, name='products'),
    path('dashboard/products/add/', views.product_form, name='product_form'),
    path('dashboard/products/edit/<int:id>/', views.product_form, name='product_form'),
    path('dashboard/products/save/', views.product_save, name='product_save'),
    path('dashboard/products/delete/<int:id>/', views.product_delete, name='product_delete'),
    
    # ✅ CATEGORY (ĐÃ FIX)
    path('dashboard/categories/', views.categories_list, name='categories'),
    path('dashboard/categories/add/', views.category_form, name='category_add'),
    path('dashboard/categories/save/', views.category_save, name='category_save'),
    path('dashboard/categories/delete/<int:id>/', views.category_delete, name='category_delete'),

    # ORDERS
    path('dashboard/orders/', views.orders_list, name='orders'),
    path('dashboard/orders/update/', views.order_update_status, name='order_update_status'),

    # USERS
    path('dashboard/users/', views.users_list, name='users'),
    path('dashboard/users/delete/<int:id>/', views.user_delete, name='user_delete'),

    # ✅ WAREHOUSE (ĐÃ FIX)
    path('dashboard/warehouses/', views.warehouse_list, name='warehouses'),
    path('dashboard/warehouses/add/', views.warehouse_form, name='warehouse_add'),
    path('dashboard/warehouses/edit/<int:id>/', views.warehouse_form, name='warehouse_edit'),
    path('dashboard/warehouses/save/', views.warehouse_save, name='warehouse_save'),
    path('dashboard/warehouses/delete/<int:id>/', views.warehouse_delete, name='warehouse_delete'), # Thêm dòng này

    # INVENTORY
    path('dashboard/inventory/', views.inventory_manage, name='inventory_manage'),
    path('dashboard/inventory/print/<int:transaction_id>/', views.print_inventory_receipt, name='print_inventory_receipt'),
    path('inventory/export/<int:transaction_id>/', views.export_inventory_excel, name='export_inventory_excel'), 
    # MAP
    path('dashboard/map/', views.admin_map_view, name='admin_map'),
    path('api/orders-locations/', views.api_orders_locations, name='api_orders_locations'),

    path('admin-panel/about/', views.admin_about_manage, name='admin_about_manage'),

    path('clean-stock-now/', views.clean_stock_data, name='clean_stock_now'),

    re_path(r'^.*$', views.custom_catch_all_404),
]