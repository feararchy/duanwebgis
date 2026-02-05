from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Product, Category, Order, OrderItem, Warehouse
import requests
from django.http import JsonResponse



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

@login_required(login_url='/login/')
def checkout(request):
    if request.method == 'POST':
        address = request.POST.get('address', 'Địa chỉ mặc định')
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        
        # 1. Tạo đơn hàng
        new_order = Order.objects.create(
            user=request.user,
            shipping_address=address,
            customer_lat=float(lat) if lat else None,
            customer_lon=float(lon) if lon else None,
            status='CHỜ XÁC NHẬN'
        )
        
        # 2. Lưu chi tiết
        cart = request.session.get('cart', {})
        total = 0
        for p_id, qty in cart.items():
            prod = Product.objects.get(id=p_id)
            OrderItem.objects.create(
                order=new_order,
                product=prod,
                quantity=qty,
                price_at_purchase=prod.price
            )
            total += prod.price * qty
            
        new_order.total_amount = total
        new_order.save()
        
        # Xóa giỏ
        request.session['cart'] = {}
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

# Hàm Form xử lý cả Thêm Mới và Sửa (Dựa vào ID)
def product_form(request, id=None):
    categories = Category.objects.all()
    product = None
    
    # Nếu có ID -> Tìm sản phẩm để sửa
    if id:
        product = get_object_or_404(Product, id=id)
        
    return render(request, 'admin/product-form.html', {
        'categories': categories,
        'product': product  # Truyền sang HTML để điền sẵn vào ô input
    })

# Hàm Lưu (Xử lý logic làm sạch giá tiền + Update/Create)
def product_save(request):
    if request.method == 'POST':
        # Lấy dữ liệu thô
        name = request.POST.get('name')
        price_raw = request.POST.get('price', '0')
        stock_raw = request.POST.get('stock_quantity', '0')
        unit = request.POST.get('unit')
        image = request.POST.get('image_url')
        cat_id = request.POST.get('category_id')
        prod_id = request.POST.get('id') # Lấy ID từ input hidden

        # --- XỬ LÝ LÀM SẠCH DỮ LIỆU ---
        # Xóa dấu chấm và phẩy để tránh lỗi "94.000"
        try:
            price = int(str(price_raw).replace('.', '').replace(',', ''))
        except ValueError:
            price = 0
            
        try:
            stock = int(str(stock_raw).replace('.', '').replace(',', ''))
        except ValueError:
            stock = 0

        cat = Category.objects.get(id=cat_id)

        # --- LOGIC LƯU ---
        if prod_id:
            # TRƯỜNG HỢP SỬA (UPDATE)
            prod = Product.objects.get(id=prod_id)
            prod.name = name
            prod.price = price
            prod.unit = unit
            prod.stock_quantity = stock
            prod.category = cat
            prod.image_url = image
            prod.save()
        else:
            # TRƯỜNG HỢP THÊM MỚI (CREATE)
            Product.objects.create(
                name=name,
                price=price,
                unit=unit,
                stock_quantity=stock,
                category=cat,
                image_url=image or 'https://via.placeholder.com/150'
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
    return render(request, 'admin/users.html', {'users': []})

def user_delete(request, id):
    return redirect('users')



def api_calculate_shipping(request):
    if request.method == 'POST':
        try:
            # Nhận tọa độ khách hàng chọn từ bản đồ
            customer_lat = request.POST.get('lat')
            customer_lng = request.POST.get('lng')
            
            # Lấy kho hàng đầu tiên làm điểm xuất phát (hoặc chọn theo ID)
            warehouse = Warehouse.objects.first()
            if not warehouse:
                return JsonResponse({'error': 'Chưa thiết lập kho hàng trong Database'}, status=400)

            # Gọi OSRM API để lấy khoảng cách đường bộ thực tế
            # Định dạng OSRM: {lng},{lat};{lng},{lat}
            osrm_url = f"http://router.project-osrm.org/route/v1/driving/{warehouse.longitude},{warehouse.latitude};{customer_lng},{customer_lat}?overview=false"
            
            response = requests.get(osrm_url)
            data = response.json()

            if data.get('code') == 'Ok':
                # Khoảng cách trả về là mét, đổi sang km
                distance_km = data['routes'][0]['distance'] / 1000
                
                # Tính phí: Phí cứng + (Số km * Đơn giá)
                total_fee = warehouse.base_fee + (distance_km * warehouse.fee_per_km)
                
                return JsonResponse({
                    'status': 'success',
                    'distance': round(distance_km, 2),
                    'fee': round(total_fee, -2), # Làm tròn đến hàng trăm
                    'warehouse': warehouse.name
                })
            else:
                return JsonResponse({'error': 'Không tìm thấy đường bộ phù hợp'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
def shipping_page(request):
    return render(request, 'shipping.html')