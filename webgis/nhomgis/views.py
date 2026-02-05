from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Order, OrderItem, Warehouse
import requests
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages

# ==========================================
# 1. PUBLIC (KHÁCH HÀNG)
# ==========================================

def home(request):
    # Lấy sản phẩm từ Database thật, sắp xếp mới nhất lên đầu
    products = Product.objects.all().order_by('-id')
    return render(request, 'index.html', {'products': products})

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'product-detail.html', {'product': product})

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

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Mật khẩu nhập lại không khớp!')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tên tài khoản này đã có người dùng!')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email này đã được đăng ký!')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        messages.success(request, 'Đăng ký thành công! Hãy đăng nhập.')
        return redirect('login')

    return render(request, 'register.html')

# --- GIỎ HÀNG (SESSION) ---
def cart_view(request):
    cart = request.session.get('cart', {}) 
    cart_items = []
    total_price = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            total = product.price * quantity
            total_price += total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': total
            })
        except Product.DoesNotExist:
            continue

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

def cart_add(request):
    if request.method == 'POST':
        p_id = request.POST.get('product_id')
        qty = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        
        if p_id in cart:
            cart[p_id] += qty 
        else:
            cart[p_id] = qty  
            
        request.session['cart'] = cart 
        return redirect('cart')
    return redirect('home')

def cart_remove(request):
    if request.method == 'POST':
        p_id = request.POST.get('product_id')
        cart = request.session.get('cart', {})
        if p_id in cart:
            del cart[p_id]
            request.session['cart'] = cart
    return redirect('cart')

# --- THANH TOÁN & TẠO ĐƠN (Đã cập nhật logic Phí Ship) ---
@login_required(login_url='/login/')
def checkout(request):
    if request.method == 'POST':
        address = request.POST.get('address', 'Địa chỉ mặc định')
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        
        # 1. Lấy phí ship từ form gửi lên (convert sang int)
        try:
            shipping_fee = int(float(request.POST.get('shipping_fee', 0)))
        except ValueError:
            shipping_fee = 0

        # 2. Tạo đơn hàng (Lưu tạm total=0)
        new_order = Order.objects.create(
            user=request.user,
            shipping_address=address,
            customer_lat=float(lat) if lat else None,
            customer_lon=float(lon) if lon else None,
            status='CHỜ XÁC NHẬN',
            shipping_fee=shipping_fee, # Lưu phí ship
            total_amount=0 
        )
        
        # 3. Lưu chi tiết sản phẩm & Tính tổng tiền hàng
        cart = request.session.get('cart', {})
        product_total = 0 # Tổng tiền hàng
        
        for p_id, qty in cart.items():
            try:
                prod = Product.objects.get(id=p_id)
                OrderItem.objects.create(
                    order=new_order,
                    product=prod,
                    quantity=qty,
                    price_at_purchase=prod.price
                )
                product_total += prod.price * qty
            except Product.DoesNotExist:
                continue
            
        # 4. CẬP NHẬT TỔNG TIỀN (Hàng + Ship)
        new_order.total_amount = product_total + shipping_fee
        new_order.save()
        
        # Xóa giỏ và thông báo
        request.session['cart'] = {}
        messages.success(request, 'Đặt hàng thành công!')
        return redirect('home')

    return redirect('cart')


# ==========================================
# 2. ADMIN (QUẢN LÝ)
# ==========================================

@login_required
def dashboard(request):
    return render(request, 'admin/dashboard.html')

# --- SẢN PHẨM ---
def products_list(request):
    products = Product.objects.all().order_by('-id')
    return render(request, 'admin/products.html', {'products': products})

def product_form(request, id=None):
    categories = Category.objects.all()
    product = None
    if id:
        product = get_object_or_404(Product, id=id)
    return render(request, 'admin/product-form.html', {
        'categories': categories,
        'product': product
    })

def product_save(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price_raw = request.POST.get('price', '0')
        stock_raw = request.POST.get('stock_quantity', '0')
        unit = request.POST.get('unit')
        image = request.POST.get('image_url')
        cat_id = request.POST.get('category_id')
        prod_id = request.POST.get('id')

        try:
            price = int(str(price_raw).replace('.', '').replace(',', ''))
        except ValueError:
            price = 0
            
        try:
            stock = int(str(stock_raw).replace('.', '').replace(',', ''))
        except ValueError:
            stock = 0

        cat = Category.objects.get(id=cat_id)

        if prod_id: # Sửa
            prod = Product.objects.get(id=prod_id)
            prod.name = name
            prod.price = price
            prod.unit = unit
            prod.stock_quantity = stock
            prod.category = cat
            prod.image_url = image
            prod.save()
        else: # Thêm mới
            Product.objects.create(
                name=name, price=price, unit=unit, stock_quantity=stock,
                category=cat, image_url=image or 'https://via.placeholder.com/150'
            )
            
        return redirect('products')
    return redirect('products')

def product_delete(request, id):
    get_object_or_404(Product, id=id).delete()
    return redirect('products')

# --- DANH MỤC ---
def categories_list(request):
    cats = Category.objects.all()
    return render(request, 'admin/categories.html', {'categories': cats})

def category_form(request):
    return render(request, 'admin/category-form.html')

def category_save(request):
    if request.method == 'POST':
        Category.objects.create(name=request.POST.get('name'))
        return redirect('categories')
    return redirect('categories')

def category_delete(request, id):
    get_object_or_404(Category, id=id).delete()
    return redirect('categories')

# --- KHO HÀNG (GIS) ---
def warehouse_list(request):
    warehouses = Warehouse.objects.all()
    return render(request, 'admin/warehouses.html', {'warehouses': warehouses})

# --- ĐƠN HÀNG ---
def orders_list(request):
    orders = Order.objects.all().order_by('-order_date')
    return render(request, 'admin/orders.html', {'orders': orders})

def order_update_status(request):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=request.POST.get('id'))
        order.status = request.POST.get('status')
        order.save()
    return redirect('orders')

# --- USER ---
def users_list(request):
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'admin/users.html', {'users': users})

def user_delete(request, id):
    user = get_object_or_404(User, id=id)
    if not user.is_superuser:
        user.delete()
        messages.success(request, 'Đã xóa khách hàng thành công!')
    else:
        messages.error(request, 'Không thể xóa tài khoản Admin!')
    return redirect('users')

# --- BẢN ĐỒ ADMIN (MARKER CLUSTERING) ---
@login_required
def admin_map_view(request):
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'admin/map_clustering.html')

def api_orders_locations(request):
    orders = Order.objects.exclude(status__in=['ĐÃ GIAO', 'ĐÃ HỦY'])\
                          .exclude(customer_lat__isnull=True)
    
    data = []
    for order in orders:
        data.append({
            'id': order.id,
            'customer': order.user.username,
            'lat': order.customer_lat,
            'lon': order.customer_lon,
            'address': order.shipping_address,
            'total': order.total_amount,
            'status': order.status,
            'url_detail': f"/orders/"
        })
        
    return JsonResponse({'orders': data})


# --- API TÍNH PHÍ VẬN CHUYỂN (GIS) ---
def api_calculate_shipping(request):
    if request.method == 'POST':
        try:
            customer_lat = request.POST.get('lat')
            customer_lng = request.POST.get('lng')
            
            warehouse = Warehouse.objects.first()
            if not warehouse:
                return JsonResponse({'error': 'Chưa thiết lập kho hàng trong Database'}, status=400)

            osrm_url = f"http://router.project-osrm.org/route/v1/driving/{warehouse.longitude},{warehouse.latitude};{customer_lng},{customer_lat}?overview=false"
            
            response = requests.get(osrm_url)
            data = response.json()

            if data.get('code') == 'Ok':
                distance_km = data['routes'][0]['distance'] / 1000
                
                # Tính phí: Base Fee + (Số Km * Fee per Km)
                total_fee = warehouse.base_fee + (distance_km * warehouse.fee_per_km)
                
                return JsonResponse({
                    'status': 'success',
                    'distance': round(distance_km, 2),
                    'fee': int(round(total_fee, -2)), # Chuyển thành số nguyên (VNĐ)
                    'warehouse': warehouse.name
                })
            else:
                return JsonResponse({'error': 'Không tìm thấy đường đi'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def shipping_page(request):
    return render(request, 'shipping.html')