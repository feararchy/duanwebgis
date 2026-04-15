from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product, Category, Order, OrderItem, Warehouse, ProductImage, Review, Post, StoreReview, Stock, InventoryTransaction
import requests
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q  # Thư viện hỗ trợ tìm kiếm nâng cao
from django.core.exceptions import PermissionDenied
from .models import CustomerProfile
from .form import UserUpdateForm, ProfileUpdateForm
import random
from django.core.mail import send_mail
from .models import EmailVerification

# ==========================================
# 1. PUBLIC (KHÁCH HÀNG)
# ==========================================
def home(request):
    categories = Category.objects.all()
    products_list = Product.objects.all().order_by('-id')

    for p in products_list:
        all_imgs = []
        if p.image: all_imgs.append(p.image.url) 
        for sub_img in p.images.all(): all_imgs.append(sub_img.image.url)
        if not all_imgs: all_imgs.append("https://via.placeholder.com/300")
        p.image_list = all_imgs 

    search_query, cat_id = request.GET.get('q', ''), request.GET.get('category', '')
    if search_query: products_list = products_list.filter(name__icontains=search_query)
    if cat_id and cat_id != 'all': products_list = products_list.filter(category_id=cat_id)

    page_obj = Paginator(products_list, 8).get_page(request.GET.get('page'))

    store_reviews = StoreReview.objects.all().order_by('-created_at')[:5]
    has_store_reviewed = StoreReview.objects.filter(user=request.user).exists() if request.user.is_authenticated else False

    return render(request, 'index.html', {
        'page_obj': page_obj, 'categories': categories, 'search_query': search_query, 'cat_id': cat_id,
        'store_reviews': store_reviews, 'has_store_reviewed': has_store_reviewed
    })

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    has_reviewed = Review.objects.filter(user=request.user, product=product).exists() if request.user.is_authenticated else False
    return render(request, 'product-detail.html', {'product': product, 'reviews': product.reviews.all().order_by('-created_at'), 'has_reviewed': has_reviewed})

@login_required(login_url='/login/')
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        if not Review.objects.filter(user=request.user, product=product).exists():
            Review.objects.create(user=request.user, product=product, stars=int(request.POST.get('stars', 5)), comment=request.POST.get('comment', ''))
            messages.success(request, 'Đánh giá đã được ghi nhận!')
    return redirect('product_detail', id=product_id)

@login_required(login_url='/login/')
def add_store_review(request):
    if request.method == 'POST' and not StoreReview.objects.filter(user=request.user).exists():
        StoreReview.objects.create(user=request.user, stars=int(request.POST.get('stars', 5)), comment=request.POST.get('comment', ''))
        messages.success(request, "Cảm ơn bạn đã đánh giá cửa hàng!")
    return redirect('home')

def blog_list(request): return render(request, 'blog.html', {'page_obj': Paginator(Post.objects.all().order_by('-created_at'), 6).get_page(request.GET.get('page'))})
def blog_detail(request, id): return render(request, 'blog_detail.html', {'post': get_object_or_404(Post, id=id)})

@login_required(login_url='/login/')
def blog_create(request):
    if not request.user.is_staff: return redirect('blog_list')
    if request.method == 'POST':
        Post.objects.create(title=request.POST.get('title'), content=request.POST.get('content'), thumbnail=request.FILES.get('thumbnail'), author=request.user)
        messages.success(request, "Đã đăng bài thành công!")
        return redirect('blog_list')
    return render(request, 'blog_form.html')

# ==========================================
# 2. TÀI KHOẢN & GIỎ HÀNG
# ==========================================
def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('dashboard') if user.is_staff else redirect('home')
        return render(request, 'login.html', {'error_message': 'Sai tài khoản!'})
    return render(request, 'login.html')

def logout_view(request): logout(request); return redirect('/login/')

def register(request):
    if request.method == 'POST':
        u, e, p = request.POST.get('username'), request.POST.get('email'), request.POST.get('password')
        if User.objects.filter(username=u).exists() or User.objects.filter(email=e).exists():
            messages.error(request, "Tài khoản hoặc Email đã tồn tại!")
            return render(request, 'register.html')
        user = User.objects.create_user(username=u, email=e, password=p)
        user.is_active = False; user.save()
        otp_code = str(random.randint(100000, 999999))
        EmailVerification.objects.create(user=user, code=otp_code)
        send_mail('[KINGMATE] Mã xác nhận', f'Mã xác nhận của bạn là: {otp_code}.', 'noreply@kingmate.com', [e])
        request.session['pending_user_id'] = user.id
        return redirect('verify_email')
    return render(request, 'register.html')

def verify_email(request):
    user_id = request.session.get('pending_user_id')
    if not user_id: return redirect('register')
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        verify_obj = EmailVerification.objects.filter(user=user, code=request.POST.get('otp')).last()
        if verify_obj and not verify_obj.is_expired():
            user.is_active = True; user.save(); verify_obj.delete()
            messages.success(request, "Kích hoạt thành công!")
            return redirect('login')
        messages.error(request, "Mã sai hoặc hết hạn!")
    return render(request, 'verify_email.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            otp = str(random.randint(100000, 999999))
            EmailVerification.objects.create(user=user, code=otp)
            send_mail('[KINGMATE] Khôi phục mật khẩu', f'Mã của bạn: {otp}', 'noreply@kingmate.com', [email])
            request.session['reset_email'] = email
            return redirect('verify_reset_otp')
        messages.error(request, "Email không tồn tại!")
    return render(request, 'forgot_password.html')

def verify_reset_otp(request):
    email = request.session.get('reset_email')
    if request.method == 'POST':
        user = User.objects.filter(email=email).first()
        otp_obj = EmailVerification.objects.filter(user=user, code=request.POST.get('otp')).last()
        if otp_obj and not otp_obj.is_expired():
            request.session['otp_verified'] = True
            return redirect('reset_password_new')
        messages.error(request, "Mã sai hoặc hết hạn!")
    return render(request, 'verify_reset_otp.html')

def reset_password_new(request):
    if not request.session.get('otp_verified'): return redirect('forgot_password')
    if request.method == 'POST':
        if request.POST.get('password') != request.POST.get('confirm_password'):
            messages.error(request, "Mật khẩu không khớp!"); return render(request, 'reset_password_new.html')
        user = User.objects.filter(email=request.session.get('reset_email')).first()
        if user:
            user.set_password(request.POST.get('password')); user.save()
            del request.session['reset_email']; del request.session['otp_verified']
            messages.success(request, "Đổi mật khẩu thành công!")
            return redirect('login')
    return render(request, 'reset_password_new.html')

def cart_view(request):
    cart, items, total = request.session.get('cart', {}), [], 0
    for p_id, qty in cart.items():
        try:
            p = Product.objects.get(id=p_id)
            items.append({'product': p, 'quantity': qty, 'total': p.price * qty})
            total += p.price * qty
        except: continue
    return render(request, 'cart.html', {'cart_items': items, 'total_price': total})

def cart_add(request):
    if request.method == 'POST':
        p_id, qty = request.POST.get('product_id'), int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        cart[p_id] = cart.get(p_id, 0) + qty; request.session['cart'] = cart
    return redirect('cart')

def cart_remove(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart.pop(request.POST.get('product_id'), None); request.session['cart'] = cart
    return redirect('cart')

@login_required(login_url='/login/')
def checkout(request):
    if request.method == 'POST':
        lat_raw, lon_raw = request.POST.get('lat'), request.POST.get('lon')
        try: customer_lat, customer_lon = float(lat_raw) if lat_raw else None, float(lon_raw) if lon_raw else None
        except: customer_lat = customer_lon = None

        order = Order.objects.create(
            user=request.user, shipping_address=request.POST.get('address'), 
            shipping_fee=int(float(request.POST.get('shipping_fee', 0))),
            customer_lat=customer_lat, customer_lon=customer_lon 
        )
        
        cart, total = request.session.get('cart', {}), 0
        for p_id, qty in cart.items():
            p = Product.objects.get(id=p_id)
            OrderItem.objects.create(order=order, product=p, quantity=qty, price_at_purchase=p.price)
            total += p.price * qty
            
        order.total_amount = total + order.shipping_fee; order.save()
        request.session['cart'] = {}
        messages.success(request, '🎉 Đặt hàng thành công!')
        return redirect('home')
    return redirect('cart')

def about(request): return render(request, 'about.html')

@login_required(login_url='/login/')
def profile_view(request): return render(request, 'profile_display.html', {'profile': CustomerProfile.objects.get_or_create(user=request.user)[0]})

@login_required(login_url='/login/')
def profile_edit_view(request):
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        u_form, p_form = UserUpdateForm(request.POST, instance=request.user), ProfileUpdateForm(request.POST, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save(); p_form.save(); messages.success(request, 'Đã cập nhật thông tin!')
            return redirect('profile')
    else: u_form, p_form = UserUpdateForm(instance=request.user), ProfileUpdateForm(instance=profile)
    return render(request, 'profile_edit.html', {'u_form': u_form, 'p_form': p_form})

def api_calculate_shipping(request):
    if request.method == 'POST':
        w = get_object_or_404(Warehouse, id=request.POST.get('warehouse_id')) if request.POST.get('warehouse_id') else Warehouse.objects.first()
        if not w: return JsonResponse({'error': 'Chưa có kho'}, status=400)
        res = requests.get(f"http://router.project-osrm.org/route/v1/driving/{w.longitude},{w.latitude};{request.POST.get('lng')},{request.POST.get('lat')}?overview=false").json()
        if res.get('code') == 'Ok':
            dist = res['routes'][0]['distance'] / 1000
            fee = 0 if dist <= 3.0 else (w.base_fee if dist <= 5.0 else w.base_fee + ((dist - 5.0) * w.fee_per_km))
            return JsonResponse({'status': 'success', 'distance': round(dist, 2), 'fee': int(round(fee, -2)), 'warehouse_name': w.name})
    return JsonResponse({'error': 'Error'}, status=400)

def shipping_page(request): return render(request, 'shipping.html', {'warehouses': Warehouse.objects.all()})

# ==========================================
# 4. ADMIN (QUẢN LÝ)
# ==========================================
def is_admin(user):
    if not user.is_authenticated: return False
    if user.is_staff: return True
    raise PermissionDenied

@user_passes_test(is_admin, login_url='/login/')
def dashboard(request): return render(request, 'admin/dashboard.html')

@user_passes_test(is_admin, login_url='/login/')
def products_list(request): 
    query = request.GET.get('q', '')
    products = Product.objects.all().order_by('-id')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(category__name__icontains=query))
    
    paginator = Paginator(products, 10)
    return render(request, 'admin/products.html', {'products': paginator.get_page(request.GET.get('page')), 'search_query': query})

@user_passes_test(is_admin, login_url='/login/')
def product_form(request, id=None): return render(request, 'admin/product-form.html', {'categories': Category.objects.all(), 'product': get_object_or_404(Product, id=id) if id else None})

@user_passes_test(is_admin, login_url='/login/')
def product_save(request):
    if request.method == 'POST':
        name, price_raw, stock, unit = request.POST.get('name'), request.POST.get('price', '0').replace('.', ''), request.POST.get('stock_quantity', '0'), request.POST.get('unit')
        cat, desc, prod_id = Category.objects.get(id=request.POST.get('category_id')), request.POST.get('description', ''), request.POST.get('id')
        main_img, gallery = request.FILES.get('image'), request.FILES.getlist('gallery_images')
        try: price, stock = int(price_raw), int(stock)
        except: price = stock = 0

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

@user_passes_test(is_admin, login_url='/login/')
def warehouse_list(request): return render(request, 'admin/warehouses.html', {'warehouses': Warehouse.objects.all()})

@user_passes_test(is_admin, login_url='/login/')
def orders_list(request): 
    query = request.GET.get('q', '')
    orders = Order.objects.all().order_by('-order_date')
    if query:
        orders = orders.filter(Q(id__icontains=query) | Q(user__username__icontains=query) | Q(status__icontains=query))
    
    paginator = Paginator(orders, 10)
    return render(request, 'admin/orders.html', {'orders': paginator.get_page(request.GET.get('page')), 'search_query': query})

@user_passes_test(is_admin, login_url='/login/')
def order_update_status(request):
    if request.method == 'POST':
        o = get_object_or_404(Order, id=request.POST.get('id')); o.status = request.POST.get('status'); o.save()
        messages.success(request, f'Đã cập nhật trạng thái đơn hàng #{o.id}')
    return redirect('orders')

@user_passes_test(is_admin, login_url='/login/')
def users_list(request): 
    query = request.GET.get('q', '')
    users = User.objects.filter(is_superuser=False).order_by('-id')
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    
    paginator = Paginator(users, 10)
    return render(request, 'admin/users.html', {'users': paginator.get_page(request.GET.get('page')), 'search_query': query})

@user_passes_test(is_admin, login_url='/login/')
def user_delete(request, id): get_object_or_404(User, id=id).delete(); return redirect('users')

@user_passes_test(is_admin, login_url='/login/')
def admin_map_view(request): return render(request, 'admin/map_clustering.html')

@user_passes_test(is_admin, login_url='/login/')
def api_orders_locations(request):
    orders = Order.objects.exclude(status__in=['ĐÃ GIAO', 'ĐÃ HỦY']).exclude(customer_lat__isnull=True)
    orders_data = [{'id': o.id, 'customer': o.user.get_full_name() or o.user.username, 'lat': o.customer_lat, 'lon': o.customer_lon, 'status': o.status, 'total': o.total_amount, 'address': o.shipping_address} for o in orders]
    
    warehouses = Warehouse.objects.all()
    warehouses_data = [{'id': w.id, 'name': w.name, 'lat': w.latitude, 'lon': w.longitude, 'address': w.address} for w in warehouses]
    
    return JsonResponse({'orders': orders_data, 'warehouses': warehouses_data})

@user_passes_test(is_admin, login_url='/login/')
def inventory_manage(request):
    warehouses, products = Warehouse.objects.all(), Product.objects.all()
    transactions = Paginator(InventoryTransaction.objects.all().order_by('-date'), 10).get_page(request.GET.get('page'))

    if request.method == 'POST':
        warehouse = get_object_or_404(Warehouse, id=request.POST.get('warehouse'))
        transaction_type, note = request.POST.get('transaction_type'), request.POST.get('note', '')

        try:
            if 'excel_file' in request.FILES and request.FILES['excel_file']:
                import pandas as pd
                df = pd.read_excel(request.FILES['excel_file'])
                with transaction.atomic():
                    for index, row in df.iterrows():
                        p_id, quantity = int(row['ID Sản Phẩm']), int(row['Số Lượng'])
                        if quantity <= 0: raise ValueError(f"Dòng {index+2}: Số lượng <= 0")
                        product = get_object_or_404(Product, id=p_id)
                        stock_record, _ = Stock.objects.get_or_create(warehouse=warehouse, product=product)

                        if transaction_type == 'IMPORT': stock_record.quantity += quantity; product.stock_quantity += quantity 
                        elif transaction_type == 'EXPORT':
                            if stock_record.quantity >= quantity: stock_record.quantity -= quantity; product.stock_quantity -= quantity
                            else: raise ValueError(f"Kho {warehouse.name} thiếu hàng!")
                        stock_record.save(); product.save()
                        InventoryTransaction.objects.create(warehouse=warehouse, product=product, transaction_type=transaction_type, quantity=quantity, note="Excel: "+note, user=request.user)
                messages.success(request, 'Nhập Excel thành công!')
            else:
                p_ids, qtys = request.POST.getlist('product'), request.POST.getlist('quantity')
                with transaction.atomic():
                    for p_id, qty_str in zip(p_ids, qtys):
                        quantity = int(qty_str)
                        if quantity <= 0: raise ValueError("Số lượng <= 0")
                        product = get_object_or_404(Product, id=p_id)
                        stock_record, _ = Stock.objects.get_or_create(warehouse=warehouse, product=product)

                        if transaction_type == 'IMPORT': stock_record.quantity += quantity; product.stock_quantity += quantity 
                        elif transaction_type == 'EXPORT':
                            if stock_record.quantity >= quantity: stock_record.quantity -= quantity; product.stock_quantity -= quantity
                            else: raise ValueError(f"Thiếu hàng!")
                        stock_record.save(); product.save()
                        InventoryTransaction.objects.create(warehouse=warehouse, product=product, transaction_type=transaction_type, quantity=quantity, note=note, user=request.user)
                messages.success(request, 'Giao dịch thành công!')
        except Exception as e: messages.error(request, str(e))
        return redirect('inventory_manage')

    return render(request, 'admin/inventory_form.html', {'warehouses': warehouses, 'products': products, 'transactions': transactions})

@user_passes_test(is_admin, login_url='/login/')
def print_inventory_receipt(request, transaction_id): return render(request, 'admin/inventory_receipt.html', {'transaction': get_object_or_404(InventoryTransaction, id=transaction_id)})

@user_passes_test(is_admin, login_url='/login/')
def warehouse_form(request, id=None): return render(request, 'admin/warehouse_form.html', {'warehouse': get_object_or_404(Warehouse, id=id) if id else None})

@user_passes_test(is_admin, login_url='/login/')
def warehouse_save(request):
    if request.method == 'POST':
        try:
            w_id, name, address = request.POST.get('id'), request.POST.get('name'), request.POST.get('address')
            lat, lon, base_fee, fee_per_km = float(request.POST.get('latitude', 0)), float(request.POST.get('longitude', 0)), int(request.POST.get('base_fee', 0)), int(request.POST.get('fee_per_km', 0))
            if w_id:
                w = Warehouse.objects.get(id=w_id)
                w.name, w.address, w.latitude, w.longitude, w.base_fee, w.fee_per_km = name, address, lat, lon, base_fee, fee_per_km; w.save()
                messages.success(request, 'Cập nhật kho thành công!')
            else:
                Warehouse.objects.create(name=name, address=address, latitude=lat, longitude=lon, base_fee=base_fee, fee_per_km=fee_per_km)
                messages.success(request, 'Thêm kho mới thành công!')
        except ValueError: messages.error(request, 'Lỗi định dạng số!')
    return redirect('warehouses')

def custom_catch_all_404(request, *args, **kwargs): return render(request, '404.html', status=404)