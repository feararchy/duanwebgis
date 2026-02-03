from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

# ==========================================
# PHẦN 1: PUBLIC (KHÁCH HÀNG)
# ==========================================

def home(request):
    # Dữ liệu giả lập sản phẩm
    mock_products = [
        {'id': 1, 'name': 'Xi măng Hà Tiên', 'category': {'name': 'Xi măng'}, 'price': 85000, 'unit': 'Bao', 'image_url': 'https://vlxdhiepha.com/wp-content/uploads/2024/02/gia-xi-mang-ha-tien-1.jpg'},
        {'id': 2, 'name': 'Cát xây tô (Cát đen)', 'category': {'name': 'Cát đá'}, 'price': 180000, 'unit': 'm3', 'image_url': 'https://vatlieuxaydung360.com/wp-content/uploads/2021/11/cat-xay-to.jpg'},
        {'id': 3, 'name': 'Gạch ống Tuynel', 'category': {'name': 'Gạch xây'}, 'price': 1200, 'unit': 'Viên', 'image_url': 'https://vatlieuxaydung24h.vn/upload/sanpham/gach-ong-tuynel-binh-duong-thanh-tam-8x8x18.jpg'},
        {'id': 4, 'name': 'Thép Pomina phi 10', 'category': {'name': 'Sắt thép'}, 'price': 78000, 'unit': 'Cây', 'image_url': 'https://satthepmanhphat.com/wp-content/uploads/2021/04/thep-pomina-2.jpg'},
    ]
    return render(request, 'index.html', {'products': mock_products})

def product_detail(request, id):
    # Giả lập 1 sản phẩm chi tiết
    product = {
        'id': id,
        'name': 'Xi măng Hà Tiên (Demo)',
        'price': 85000,
        'description': 'Xi măng đa dụng chất lượng cao, phù hợp cho mọi công trình...',
        'unit': 'Bao',
        'stock_quantity': 100,
        'image_url': 'https://vlxdhiepha.com/wp-content/uploads/2024/02/gia-xi-mang-ha-tien-1.jpg',
        'category': {'name': 'Xi măng'}
    }
    return render(request, 'product-detail.html', {'product': product})

# --- Login / Logout ---
def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            if user.is_staff: return redirect('dashboard')
            else: return redirect('home')
        else:
            return render(request, 'login.html', {'error_message': 'Sai tài khoản hoặc mật khẩu!'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('/login/?logout')

# --- Giỏ hàng ---
def cart_view(request):
    mock_items = [
        {'id': 1, 'product': {'name': 'Gạch men', 'price': 150000, 'image_url': ''}, 'quantity': 2},
        {'id': 2, 'product': {'name': 'Xi măng', 'price': 85000, 'image_url': ''}, 'quantity': 5}
    ]
    # Tính tổng tiền
    total = sum(item['product']['price'] * item['quantity'] for item in mock_items)
    return render(request, 'cart.html', {'cart_items': mock_items, 'total_price': total})

def cart_add(request):
    if request.method == 'POST':
        # Logic thêm vào giỏ hàng (Session) sẽ viết ở đây
        print(f"Thêm SP {request.POST.get('product_id')} - SL: {request.POST.get('quantity')}")
        return redirect('cart')
    return redirect('home')

def cart_remove(request):
    if request.method == 'POST':
        print(f"Xóa Item ID: {request.POST.get('item_id')}")
        return redirect('cart')
    return redirect('cart')

def checkout(request):
    print("Xử lý thanh toán...")
    return redirect('home')


# ==========================================
# PHẦN 2: ADMIN (QUẢN TRỊ)
# ==========================================

def dashboard(request):
    return render(request, 'admin/dashboard.html')

# --- Quản lý Sản phẩm ---
def products_list(request):
    mock_products = [
        {'id': 101, 'name': 'Gạch men cao cấp', 'price': 150000, 'stock_quantity': 500, 'image_url': 'https://via.placeholder.com/50'},
        {'id': 102, 'name': 'Xi măng Hà Tiên', 'price': 85000, 'stock_quantity': 200, 'image_url': ''},
    ]
    return render(request, 'admin/products.html', {'products': mock_products})

def product_form(request):
    # Mock danh mục để hiện trong dropdown
    mock_categories = [{'id': 1, 'name': 'Gạch'}, {'id': 2, 'name': 'Xi măng'}]
    return render(request, 'admin/product-form.html', {'product': None, 'categories': mock_categories})

def product_save(request):
    if request.method == 'POST':
        print(f"Lưu sản phẩm: {request.POST.get('name')}")
        return redirect('products')
    return redirect('products')

def product_delete(request, id):
    print(f"Xóa sản phẩm ID: {id}")
    return redirect('products')

# --- Quản lý Danh mục ---
def categories_list(request):
    mock_cats = [{'id': 1, 'name': 'Gạch ốp lát'}, {'id': 2, 'name': 'Vật liệu thô'}]
    return render(request, 'admin/categories.html', {'categories': mock_cats})

def category_form(request):
    return render(request, 'admin/category-form.html', {'category': None})

def category_save(request):
    if request.method == 'POST':
        print(f"Lưu danh mục: {request.POST.get('name')}")
        return redirect('categories')
    return redirect('categories')

def category_delete(request, id):
    print(f"Xóa danh mục ID: {id}")
    return redirect('categories')

# --- Quản lý User ---
def users_list(request):
    mock_users = [
        {'id': 1, 'username': 'admin', 'full_name': 'Quản trị viên', 'role': 'ROLE_ADMIN'},
        {'id': 2, 'username': 'user1', 'full_name': 'Nguyễn Văn A', 'role': 'ROLE_USER'},
    ]
    return render(request, 'admin/users.html', {'users': mock_users})

def user_delete(request, id):
    print(f"Xóa User ID: {id}")
    return redirect('users')

# --- Quản lý Hóa đơn ---
def orders_list(request):
    # Dữ liệu giả lập hóa đơn
    mock_orders = [
        {
            'id': 1001, 
            'user': {'fullName': 'Nguyễn Văn A'}, 
            'orderDate': '2023-10-25', 
            'totalAmount': 500000, 
            'status': 'CHỜ XÁC NHẬN'
        },
        {
            'id': 1002, 
            'user': {'fullName': 'Trần Thị B'}, 
            'orderDate': '2023-10-26', 
            'totalAmount': 1200000, 
            'status': 'ĐANG GIAO'
        }
    ]
    return render(request, 'admin/orders.html', {'orders': mock_orders})

def order_update_status(request):
    if request.method == 'POST':
        print(f"Cập nhật đơn {request.POST.get('id')} thành {request.POST.get('status')}")
        return redirect('orders')
    return redirect('orders')