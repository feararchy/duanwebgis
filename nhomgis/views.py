from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product, Category, Order, OrderItem, Warehouse, ProductImage, Review, Post, StoreReview, UserAddress
import requests
import math
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
import random
from django.core.mail import send_mail

# ==========================================
# TRẠM GÁC BẢO MẬT & THUẬT TOÁN GIS
# ==========================================
def is_admin(user):
    return user.is_authenticated and user.is_staff

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ==========================================
# 1. PUBLIC (KHÁCH HÀNG & TRANG CHỦ)
# ==========================================

def home(request):
    categories = Category.objects.all()
    products_list = Product.objects.all().order_by('-id')

    # Chuẩn bị danh sách ảnh cho Carousel
    for p in products_list:
        all_imgs = [p.image.url] if p.image else []
        for sub_img in p.images.all(): all_imgs.append(sub_img.image.url)
        if not all_imgs: all_imgs.append("https://via.placeholder.com/300")
        p.image_list = all_imgs 

    # Bộ lọc và tìm kiếm
    search_query, cat_id = request.GET.get('q', ''), request.GET.get('category', '')
    if search_query: products_list = products_list.filter(name__icontains=search_query)
    if cat_id and cat_id != 'all': products_list = products_list.filter(category_id=cat_id)

    # Phân trang
    page_obj = Paginator(products_list, 8).get_page(request.GET.get('page'))
    
    # Đánh giá cửa hàng
    store_reviews = StoreReview.objects.all().order_by('-created_at')[:5]
    has_store_reviewed = StoreReview.objects.filter(user=request.user).exists() if request.user.is_authenticated else False

    return render(request, 'index.html', {
        'page_obj': page_obj, 'categories': categories,
        'search_query': search_query, 'cat_id': cat_id,
        'store_reviews': store_reviews, 'has_store_reviewed': has_store_reviewed
    })

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.all().order_by('-created_at')
    has_reviewed = Review.objects.filter(user=request.user, product=product).exists() if request.user.is_authenticated else False
    return render(request, 'product-detail.html', {'product': product, 'reviews': reviews, 'has_reviewed': has_reviewed})

@login_required(login_url='/login/')
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        if not Review.objects.filter(user=request.user, product=product).exists():
            Review.objects.create(user=request.user, product=product, stars=int(request.POST.get('stars', 5)), comment=request.POST.get('comment', ''))
            messages.success(request, 'Đánh giá đã được ghi nhận!')
        else: messages.error(request, 'Bạn đã đánh giá sản phẩm này rồi.')
    return redirect('product_detail', id=product_id)

@login_required(login_url='/login/')
def add_store_review(request):
    if request.method == 'POST':
        if not StoreReview.objects.filter(user=request.user).exists():
            StoreReview.objects.create(user=request.user, stars=int(request.POST.get('stars', 5)), comment=request.POST.get('comment', ''))
            messages.success(request, "Cảm ơn bạn đã đánh giá cửa hàng!")
    return redirect('home')

def blog_list(request): 
    return render(request, 'blog.html', {'page_obj': Paginator(Post.objects.all().order_by('-created_at'), 6).get_page(request.GET.get('page'))})

def blog_detail(request, id): 
    return render(request, 'blog_detail.html', {'post': get_object_or_404(Post, id=id)})

@login_required(login_url='/login/')
def blog_create(request):
    if not request.user.is_staff: return redirect('blog_list')
    if request.method == 'POST':
        Post.objects.create(title=request.POST.get('title'), content=request.POST.get('content'), thumbnail=request.FILES.get('thumbnail'), author=request.user)
        messages.success(request, "Đã đăng bài thành công!")
        return redirect('blog_list')
    return render(request, 'blog_form.html')

def public_warehouses(request):
    return render(request, 'warehouses_public.html', {'warehouses': Warehouse.objects.all()})

# ==========================================
# 2. TÀI KHOẢN, GIỎ HÀNG & THANH TOÁN
# ==========================================

def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('dashboard') if user.is_staff else redirect('home')
        return render(request, 'login.html', {'error_message': 'Sai tài khoản hoặc mật khẩu!'})
    return render(request, 'login.html')

def logout_view(request): 
    logout(request); return redirect('/login/')

# ----- ĐĂNG KÝ VÀ XÁC THỰC EMAIL OTP -----
def register(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')

        # Kiểm tra xem User hoặc Email đã tồn tại chưa
        if User.objects.filter(username=u).exists():
            messages.error(request, 'Tên đăng nhập này đã có người sử dụng!')
            return redirect('register')
        if User.objects.filter(email=e).exists():
            messages.error(request, 'Email này đã được đăng ký!')
            return redirect('register')

        # Tạo mã OTP ngẫu nhiên 6 chữ số
        otp = str(random.randint(100000, 999999))

        # Lưu tạm thông tin vào Session, CHƯA tạo tài khoản vội
        request.session['temp_user'] = {
            'username': u, 'email': e, 'password': p, 'otp': otp
        }

        # Gửi email qua Mailtrap
        subject = 'Mã xác nhận đăng ký tài khoản KingMateShop'
        message = f'Chào {u},\n\nMã xác nhận (OTP) của bạn là: {otp}\n\nVui lòng nhập mã này trên trang web để hoàn tất đăng ký.\n\nTrân trọng,\nĐội ngũ KingMate.'
        
        try:
            send_mail(subject, message, 'noreply@kingmateshop.com', [e])
            messages.info(request, 'Chúng tôi đã gửi mã xác nhận đến Email của bạn. Vui lòng kiểm tra hộp thư!')
            return redirect('verify_email')
        except Exception as err:
            messages.error(request, 'Lỗi hệ thống khi gửi email: ' + str(err))
            return redirect('register')
            
    return render(request, 'register.html')

def verify_email(request):
    # Nếu chưa điền form đăng ký mà tự ý vào trang này thì đuổi về
    if 'temp_user' not in request.session:
        return redirect('register')

    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        temp_user = request.session['temp_user']

        # Nếu mã nhập vào TRÙNG với mã đã lưu trong session
        if user_otp == temp_user['otp']:
            # Chính thức tạo tài khoản lưu vào Database
            User.objects.create_user(
                username=temp_user['username'],
                email=temp_user['email'],
                password=temp_user['password']
            )
            # Xóa session rác
            del request.session['temp_user']
            messages.success(request, 'Đăng ký thành công! Mời bạn đăng nhập.')
            return redirect('login')
        else:
            messages.error(request, 'Mã OTP không chính xác, vui lòng thử lại!')

    return render(request, 'verify_email.html')
# ==========================================
# QUÊN MẬT KHẨU (GỬI OTP QUA MAILTRAP)
# ==========================================
def forgot_password(request):
    if request.method == 'POST':
        e = request.POST.get('email')
        user = User.objects.filter(email=e).first()
        
        if user:
            # Tạo mã OTP 6 số ngẫu nhiên
            otp = str(random.randint(100000, 999999))
            request.session['reset_data'] = {'email': e, 'otp': otp}
            
            subject = 'Mã khôi phục mật khẩu KingMateShop'
            message = f'Chào bạn,\n\nMã OTP để khôi phục mật khẩu của bạn là: {otp}\n\nVui lòng nhập mã này lên website để đặt lại mật khẩu mới. Tuyệt đối không chia sẻ mã này cho người khác!\n\nTrân trọng,\nĐội ngũ KingMate.'
            try:
                send_mail(subject, message, 'noreply@kingmateshop.com', [e])
                messages.info(request, 'Mã khôi phục đã được gửi! Vui lòng kiểm tra email của bạn.')
                return redirect('verify_reset_otp')
            except Exception as err:
                messages.error(request, 'Lỗi gửi mail: ' + str(err))
        else:
            messages.error(request, 'Email này chưa được đăng ký trong hệ thống!')
            
    return render(request, 'forgot_password.html')

def verify_reset_otp(request):
    # Nếu chưa nhập email mà tự ý vào thì đuổi về
    if 'reset_data' not in request.session:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        if user_otp == request.session['reset_data']['otp']:
            # Đánh dấu đã xác thực thành công để cho phép đổi mật khẩu
            request.session['can_reset_password'] = True
            messages.success(request, 'Xác thực thành công. Mời bạn tạo mật khẩu mới!')
            return redirect('reset_new_password')
        else:
            messages.error(request, 'Mã OTP không chính xác!')
            
    return render(request, 'verify_reset_otp.html')

def reset_new_password(request):
    # Trạm gác: Bắt buộc phải qua bước nhập OTP mới được vào đây
    if not request.session.get('can_reset_password'):
        return redirect('forgot_password')
        
    if request.method == 'POST':
        p1 = request.POST.get('new_password')
        p2 = request.POST.get('confirm_password')
        
        if p1 == p2:
            email = request.session['reset_data']['email']
            user = User.objects.get(email=email)
            user.set_password(p1) # Mã hóa mật khẩu mới
            user.save()
            
            # Dọn dẹp sạch sẽ session
            del request.session['reset_data']
            del request.session['can_reset_password']
            
            messages.success(request, 'Tuyệt vời! Bạn đã đổi mật khẩu thành công. Vui lòng đăng nhập lại.')
            return redirect('login')
        else:
            messages.error(request, 'Mật khẩu xác nhận không khớp!')
            
    return render(request, 'reset_new_password.html')
# ----------------------------------------

def cart_view(request):
    cart, items, total = request.session.get('cart', {}), [], 0
    for p_id, qty in cart.items():
        try:
            p = Product.objects.get(id=p_id)
            items.append({'product': p, 'quantity': qty, 'total': p.price * qty})
            total += p.price * qty
        except: continue
    
    saved_addresses = UserAddress.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, 'cart.html', {'cart_items': items, 'total_price': total, 'saved_addresses': saved_addresses})

def cart_add(request):
    if request.method == 'POST':
        p_id, qty = request.POST.get('product_id'), int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        cart[p_id] = cart.get(p_id, 0) + qty
        request.session['cart'] = cart
    return redirect('cart')

def cart_remove(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart.pop(request.POST.get('product_id'), None)
        request.session['cart'] = cart
    return redirect('cart')

@login_required(login_url='/login/')
def checkout(request):
    if request.method == 'POST':
        address, lat, lon = request.POST.get('address'), request.POST.get('lat'), request.POST.get('lon')
        save_address, address_name = request.POST.get('save_address'), request.POST.get('address_name', 'Địa chỉ phụ')
        try: shipping_fee = int(float(request.POST.get('shipping_fee', 0)))
        except ValueError: shipping_fee = 0

        # Lưu sổ địa chỉ nếu khách yêu cầu
        if save_address == 'on' and lat and lon:
            if not UserAddress.objects.filter(user=request.user).exists():
                UserAddress.objects.create(user=request.user, name="Mặc định", address=address, latitude=float(lat), longitude=float(lon), is_default=True)
            else:
                UserAddress.objects.create(user=request.user, name=address_name, address=address, latitude=float(lat), longitude=float(lon))

        new_order = Order.objects.create(
            user=request.user, shipping_address=address,
            customer_lat=float(lat) if lat else None, customer_lon=float(lon) if lon else None,
            status='CHỜ XÁC NHẬN', shipping_fee=shipping_fee, total_amount=0 
        )
        
        cart, product_total = request.session.get('cart', {}), 0 
        for p_id, qty in cart.items():
            try:
                prod = Product.objects.get(id=p_id)
                OrderItem.objects.create(order=new_order, product=prod, quantity=qty, price_at_purchase=prod.price)
                product_total += prod.price * qty
            except Product.DoesNotExist: continue
            
        new_order.total_amount = product_total + shipping_fee
        new_order.save()
        request.session['cart'] = {}
        messages.success(request, 'Đặt hàng thành công!')
        return redirect('home')
    return redirect('cart')

@login_required(login_url='/login/')
def delete_address(request, id):
    get_object_or_404(UserAddress, id=id, user=request.user).delete()
    return redirect('cart')

# ==========================================
# 3. GIS API: TÌM KHO GẦN NHẤT & TÍNH PHÍ
# ==========================================

def api_calculate_shipping(request):
    if request.method == 'POST':
        try:
            customer_lat, customer_lng = float(request.POST.get('lat')), float(request.POST.get('lng'))
            warehouses = Warehouse.objects.all()
            
            if not warehouses:
                return JsonResponse({'error': 'Hệ thống chưa thiết lập kho hàng.'}, status=400)

            # Lọc kho gần nhất bằng Haversine
            nearest_w = None
            min_dist = float('inf')
            for w in warehouses:
                dist = calculate_distance(customer_lat, customer_lng, w.latitude, w.longitude)
                if dist < min_dist:
                    min_dist = dist
                    nearest_w = w

            # Gọi OSRM tính đường đi thực tế
            osrm_url = f"http://router.project-osrm.org/route/v1/driving/{nearest_w.longitude},{nearest_w.latitude};{customer_lng},{customer_lat}?overview=false"
            data = requests.get(osrm_url).json()

            if data.get('code') == 'Ok':
                route_dist_km = data['routes'][0]['distance'] / 1000
                total_fee = nearest_w.base_fee + (route_dist_km * nearest_w.fee_per_km)
                return JsonResponse({
                    'status': 'success', 
                    'distance': round(route_dist_km, 2), 
                    'fee': int(round(total_fee, -2)), 
                    'warehouse': nearest_w.name
                })
            else: return JsonResponse({'error': 'Không tìm thấy đường đi thực tế.'}, status=400)
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)

def shipping_page(request): 
    return render(request, 'shipping.html')

# ==========================================
# 4. ADMIN (QUẢN TRỊ VIÊN) - ĐÃ BẢO MẬT
# ==========================================

@user_passes_test(is_admin, login_url='/login/')
def dashboard(request): 
    return render(request, 'admin/dashboard.html')

# ----- SẢN PHẨM & DANH MỤC -----
@user_passes_test(is_admin, login_url='/login/')
def products_list(request): 
    return render(request, 'admin/products.html', {'products': Product.objects.all().order_by('-id')})

@user_passes_test(is_admin, login_url='/login/')
def product_form(request, id=None):
    return render(request, 'admin/product-form.html', {'categories': Category.objects.all(), 'product': get_object_or_404(Product, id=id) if id else None})

@user_passes_test(is_admin, login_url='/login/')
def product_save(request):
    if request.method == 'POST':
        name, price_raw, stock, unit = request.POST.get('name'), request.POST.get('price', '0').replace('.', ''), request.POST.get('stock_quantity', '0'), request.POST.get('unit')
        cat = Category.objects.get(id=request.POST.get('category_id'))
        desc, prod_id = request.POST.get('description', ''), request.POST.get('id')
        main_img, gallery = request.FILES.get('image'), request.FILES.getlist('gallery_images')

        try: price, stock = int(price_raw), int(stock)
        except ValueError: price = stock = 0

        if prod_id:
            p = Product.objects.get(id=prod_id)
            p.name, p.price, p.unit, p.stock_quantity, p.category, p.description = name, price, unit, stock, cat, desc
            if main_img: p.image = main_img
            p.save()
        else: p = Product.objects.create(name=name, price=price, unit=unit, stock_quantity=stock, category=cat, image=main_img, description=desc)
        for img in gallery: ProductImage.objects.create(product=p, image=img)
    return redirect('products')

@user_passes_test(is_admin, login_url='/login/')
def product_delete(request, id): get_object_or_404(Product, id=id).delete(); return redirect('products')

@user_passes_test(is_admin, login_url='/login/')
def categories_list(request): return render(request, 'admin/categories.html', {'categories': Category.objects.all()})

@user_passes_test(is_admin, login_url='/login/')
def category_form(request): return render(request, 'admin/category-form.html')

@user_passes_test(is_admin, login_url='/login/')
def category_save(request):
    if request.method == 'POST': Category.objects.create(name=request.POST.get('name'))
    return redirect('categories')

@user_passes_test(is_admin, login_url='/login/')
def category_delete(request, id): get_object_or_404(Category, id=id).delete(); return redirect('categories')

# ----- QUẢN LÝ KHO HÀNG (WAREHOUSE CRUD) -----
@user_passes_test(is_admin, login_url='/login/')
def warehouse_list(request):
    return render(request, 'admin/warehouses.html', {'warehouses': Warehouse.objects.all().order_by('id')})

@user_passes_test(is_admin, login_url='/login/')
def warehouse_form(request, id=None):
    return render(request, 'admin/warehouse-form.html', {'warehouse': get_object_or_404(Warehouse, id=id) if id else None})

@user_passes_test(is_admin, login_url='/login/')
def warehouse_save(request):
    if request.method == 'POST':
        w_id = request.POST.get('id')
        name, addr = request.POST.get('name'), request.POST.get('address')
        lat, lon = request.POST.get('latitude'), request.POST.get('longitude')
        base, per_km = request.POST.get('base_fee', 15000), request.POST.get('fee_per_km', 5000)
        
        if w_id:
            w = get_object_or_404(Warehouse, id=w_id)
            w.name, w.address, w.latitude, w.longitude, w.base_fee, w.fee_per_km = name, addr, lat, lon, base, per_km
            w.save()
            messages.success(request, f"Đã cập nhật kho: {name}")
        else:
            Warehouse.objects.create(name=name, address=addr, latitude=lat, longitude=lon, base_fee=base, fee_per_km=per_km)
            messages.success(request, f"Đã thêm kho mới: {name}")
    return redirect('warehouses')

@user_passes_test(is_admin, login_url='/login/')
def warehouse_delete(request, id):
    w = get_object_or_404(Warehouse, id=id)
    w.delete(); messages.warning(request, f"Đã xóa kho hàng!")
    return redirect('warehouses')

# ----- ĐƠN HÀNG & USER -----
@user_passes_test(is_admin, login_url='/login/')
def orders_list(request): return render(request, 'admin/orders.html', {'orders': Order.objects.all().order_by('-order_date')})

@user_passes_test(is_admin, login_url='/login/')
def order_update_status(request):
    if request.method == 'POST':
        o = get_object_or_404(Order, id=request.POST.get('id'))
        o.status = request.POST.get('status'); o.save()
    return redirect('orders')

@user_passes_test(is_admin, login_url='/login/')
def users_list(request): return render(request, 'admin/users.html', {'users': User.objects.filter(is_superuser=False)})

@user_passes_test(is_admin, login_url='/login/')
def user_delete(request, id): get_object_or_404(User, id=id).delete(); return redirect('users')

@user_passes_test(is_admin, login_url='/login/')
def admin_map_view(request): return render(request, 'admin/map_clustering.html')

# ----- API BẢN ĐỒ ADMIN (ĐÃ NÂNG CẤP ĐỂ LẤY CẢ ĐƠN HÀNG & KHO HÀNG) -----
@user_passes_test(is_admin, login_url='/login/')
def api_orders_locations(request):
    # 1. Lấy dữ liệu Đơn hàng
    orders = Order.objects.exclude(status__in=['ĐÃ GIAO', 'ĐÃ HỦY']).exclude(customer_lat__isnull=True)
    orders_data = [{
        'id': o.id, 'customer': o.user.username, 
        'lat': o.customer_lat, 'lon': o.customer_lon, 
        'status': o.status, 'address': o.shipping_address
    } for o in orders]
    
    # 2. Lấy dữ liệu Kho hàng
    warehouses = Warehouse.objects.all()
    warehouses_data = [{
        'id': w.id, 'name': w.name, 
        'lat': w.latitude, 'lon': w.longitude, 
        'address': w.address
    } for w in warehouses]
    
    return JsonResponse({'orders': orders_data, 'warehouses': warehouses_data})

# ==========================================
# 5. XỬ LÝ LỖI (404, 403)
# ==========================================
def error_404(request, exception): return render(request, '404.html', status=404)
def error_403(request, exception): return render(request, '403.html', status=403)

def about_view(request):
    return render(request, 'about.html')