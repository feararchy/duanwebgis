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

    # CHUẨN BỊ DANH SÁCH ẢNH CHO CAROUSEL TẠI TRANG CHỦ
    for p in products_list:
        all_imgs = []
        if p.image:
            all_imgs.append(p.image.url) # Ảnh chính
        
        # Lấy thêm các ảnh phụ từ gallery
        for sub_img in p.images.all():
            all_imgs.append(sub_img.image.url)
            
        # Nếu hoàn toàn không có ảnh nào thì dùng ảnh tạm
        if not all_imgs:
            all_imgs.append("https://via.placeholder.com/300")
            
        p.image_list = all_imgs # Đưa vào mảng để lặp trong HTML

    # Xử lý tìm kiếm và bộ lọc
    search_query = request.GET.get('q', '')
    cat_id = request.GET.get('category', '')
    if search_query: 
        products_list = products_list.filter(name__icontains=search_query)
    if cat_id and cat_id != 'all': 
        products_list = products_list.filter(category_id=cat_id)

    # Phân trang
    paginator = Paginator(products_list, 8) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Đánh giá cửa hàng
    store_reviews = StoreReview.objects.all().order_by('-created_at')[:5]
    has_store_reviewed = False
    if request.user.is_authenticated:
        has_store_reviewed = StoreReview.objects.filter(user=request.user).exists()

    return render(request, 'index.html', {
        'page_obj': page_obj, 'categories': categories,
        'search_query': search_query, 'cat_id': cat_id,
        'store_reviews': store_reviews, 'has_store_reviewed': has_store_reviewed
    })

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.all().order_by('-created_at')
    has_reviewed = False
    if request.user.is_authenticated:
        has_reviewed = Review.objects.filter(user=request.user, product=product).exists()
    return render(request, 'product-detail.html', {'product': product, 'reviews': reviews, 'has_reviewed': has_reviewed})

@login_required(login_url='/login/')
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        stars = int(request.POST.get('stars', 5))
        comment = request.POST.get('comment', '')
        if not Review.objects.filter(user=request.user, product=product).exists():
            Review.objects.create(user=request.user, product=product, stars=stars, comment=comment)
            messages.success(request, 'Đánh giá đã được ghi nhận!')
        else:
            messages.error(request, 'Bạn đã đánh giá sản phẩm này rồi.')
    return redirect('product_detail', id=product_id)

@login_required(login_url='/login/')
def add_store_review(request):
    if request.method == 'POST':
        stars = int(request.POST.get('stars', 5))
        comment = request.POST.get('comment', '')
        if not StoreReview.objects.filter(user=request.user).exists():
            StoreReview.objects.create(user=request.user, stars=stars, comment=comment)
            messages.success(request, "Cảm ơn bạn đã đánh giá cửa hàng!")
        else:
            messages.error(request, "Bạn đã đánh giá rồi.")
    return redirect('home')

def blog_list(request):
    posts_list = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts_list, 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog.html', {'page_obj': page_obj})

def blog_detail(request, id):
    post = get_object_or_404(Post, id=id)
    return render(request, 'blog_detail.html', {'post': post})

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

def logout_view(request):
    logout(request); return redirect('/login/')

def register(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        
        # KIỂM TRA: Username đã tồn tại chưa?
        if User.objects.filter(username=u).exists():
            messages.error(request, f"Tài khoản '{u}' đã có người sử dụng. Vui lòng chọn tên khác!")
            return render(request, 'register.html')
            
        # KIỂM TRA: Email đã tồn tại chưa?
        if User.objects.filter(email=e).exists():
            messages.error(request, f"Email '{e}' đã được đăng ký. Vui lòng sử dụng email khác!")
            return render(request, 'register.html')

        try:
            # Nếu mọi thứ ổn, tiến hành tạo user (is_active=False để chờ xác minh Mailtrap)
            user = User.objects.create_user(username=u, email=e, password=p)
            user.is_active = False 
            user.save()

            # Tạo mã OTP và gửi Mailtrap như đã hướng dẫn trước đó
            otp_code = str(random.randint(100000, 999999))
            EmailVerification.objects.create(user=user, code=otp_code)

            subject = '[KINGMATE] Mã xác nhận đăng ký tài khoản'
            message = f'Chào {user.username}, mã xác nhận của bạn là: {otp_code}.'
            send_mail(subject, message, 'noreply@kingmate.com', [e])

            request.session['pending_user_id'] = user.id
            messages.info(request, "Vui lòng kiểm tra email Mailtrap để lấy mã xác nhận!")
            return redirect('verify_email')
            
        except Exception as err:
            messages.error(request, f"Có lỗi xảy ra: {err}")
            return render(request, 'register.html')
            
    return render(request, 'register.html')

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
        # 1. Lấy tọa độ lat, lng từ form gửi lên
        lat_raw = request.POST.get('lat')
        lon_raw = request.POST.get('lon') # Chú ý xem frontend HTML của bạn đặt name là 'lng' hay 'lon'
        
        # Xử lý an toàn: ép kiểu sang số thực (float), nếu không có thì để None
        try:
            customer_lat = float(lat_raw) if lat_raw else None
            customer_lon = float(lon_raw) if lon_raw else None
        except ValueError:
            customer_lat = None
            customer_lon = None

        # 2. Tạo Order và lưu kèm TỌA ĐỘ
        order = Order.objects.create(
            user=request.user, 
            shipping_address=request.POST.get('address'), 
            shipping_fee=int(float(request.POST.get('shipping_fee', 0))),
            customer_lat=customer_lat, # Đã fix: Lưu vĩ độ
            customer_lon=customer_lon  # Đã fix: Lưu kinh độ
        )
        
        cart, total = request.session.get('cart', {}), 0
        for p_id, qty in cart.items():
            p = Product.objects.get(id=p_id)
            OrderItem.objects.create(order=order, product=p, quantity=qty, price_at_purchase=p.price)
            total += p.price * qty
            
        order.total_amount = total + order.shipping_fee
        order.save()
        
        # Xóa giỏ hàng
        request.session['cart'] = {}
        
        # 3. Đã fix: Thêm thông báo thành công
        messages.success(request, '🎉 Đặt hàng thành công! Cửa hàng sẽ sớm liên hệ để giao vật liệu cho bạn.')
        
        return redirect('home')
    return redirect('cart')

def about(request):
    return render(request, 'about.html')

@login_required(login_url='/login/')
def profile_view(request):
    # Chỉ lấy dữ liệu để hiển thị
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile_display.html', {'profile': profile})

@login_required(login_url='/login/')
def profile_edit_view(request):
    # Logic xử lý chỉnh sửa
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Đã cập nhật thông tin thành công!')
            return redirect('profile') # Sau khi lưu thì quay về trang hiển thị
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    return render(request, 'profile_edit.html', {'u_form': u_form, 'p_form': p_form})

def register(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        
        # 1. Tạo user nhưng chưa cho hoạt động
        user = User.objects.create_user(username=u, email=e, password=p)
        user.is_active = False 
        user.save()

        # 2. Tạo mã OTP 6 số
        otp_code = str(random.randint(100000, 999999))
        EmailVerification.objects.create(user=user, code=otp_code)

        # 3. Gửi Mail qua Mailtrap
        subject = '[KINGMATE] Mã xác nhận đăng ký tài khoản'
        message = f'Chào {user.username}, mã xác nhận của bạn là: {otp_code}. Mã có hiệu lực trong 5 phút.'
        send_mail(subject, message, 'noreply@kingmate.com', [e])

        # Lưu ID vào session để trang xác nhận biết là ai
        request.session['pending_user_id'] = user.id
        messages.info(request, "Vui lòng kiểm tra email để lấy mã xác nhận!")
        return redirect('verify_email')
        
    return render(request, 'register.html')

def verify_email(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('register')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        user = get_object_or_404(User, id=user_id)
        verify_obj = EmailVerification.objects.filter(user=user, code=otp_input).last()

        if verify_obj and not verify_obj.is_expired():
            user.is_active = True
            user.save()
            verify_obj.delete() # Xóa mã sau khi dùng xong
            messages.success(request, "Kích hoạt tài khoản thành công! Bạn có thể đăng nhập.")
            return redirect('login')
        else:
            messages.error(request, "Mã xác nhận không đúng hoặc đã hết hạn!")
            
    return render(request, 'verify_email.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            otp_code = str(random.randint(100000, 999999))
            EmailVerification.objects.create(user=user, code=otp_code)
            send_mail(
                '[KINGMATE] Khôi phục mật khẩu',
                f'Mã xác minh của bạn là: {otp_code}',
                'noreply@kingmate.com',
                [email]
            )
            request.session['reset_email'] = email
            messages.success(request, "Đã gửi mã OTP vào email!")
            return redirect('verify_reset_otp')
        messages.error(request, "Email không tồn tại trong hệ thống!")
    return render(request, 'forgot_password.html')

def verify_reset_otp(request):
    email = request.session.get('reset_email')
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        
        # SỬA TẠI ĐÂY: Dùng filter().first() để tránh lỗi MultipleObjectsReturned
        user = User.objects.filter(email=email).first()
        
        if not user:
            messages.error(request, "Không tìm thấy người dùng!")
            return redirect('forgot_password')

        otp_obj = EmailVerification.objects.filter(user=user, code=otp_input).last()
        
        if otp_obj and not otp_obj.is_expired():
            request.session['otp_verified'] = True
            return redirect('reset_password_new')
        else:
            messages.error(request, "Mã xác nhận sai hoặc đã hết hạn!")
            
    return render(request, 'verify_reset_otp.html')

def reset_password_new(request):
    if not request.session.get('otp_verified'):
        return redirect('forgot_password')
        
    if request.method == 'POST':
        new_pass = request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password')
        
        if new_pass != confirm_pass:
            messages.error(request, "Mật khẩu nhập lại không khớp!")
            return render(request, 'reset_password_new.html')

        email = request.session.get('reset_email')
        
        # SỬA TẠI ĐÂY: Lấy user một cách an toàn
        user = User.objects.filter(email=email).first()
        
        if user:
            user.set_password(new_pass)
            user.save()
            
            # Xóa session sau khi xong
            del request.session['reset_email']
            del request.session['otp_verified']
            
            messages.success(request, "Mật khẩu đã được đổi thành công!")
            return redirect('login')
        
    return render(request, 'reset_password_new.html')
# ==========================================
# 3. GIS API (BẢN ĐỒ & VẬN CHUYỂN)
# ==========================================

def api_calculate_shipping(request):
    if request.method == 'POST':
        w = Warehouse.objects.first()
        if not w:
            return JsonResponse({'error': 'Chưa có kho hàng'}, status=400)
            
        res = requests.get(f"http://router.project-osrm.org/route/v1/driving/{w.longitude},{w.latitude};{request.POST.get('lng')},{request.POST.get('lat')}?overview=false").json()
        
        if res.get('code') == 'Ok':
            dist = res['routes'][0]['distance'] / 1000
            
            # --- LOGIC TÍNH PHÍ SHIP THEO NẤC KHOẢNG CÁCH ---
            if dist <= 3.0:
                fee = 0  # Miễn phí 3km đầu
            elif dist <= 5.0:
                fee = w.base_fee  # Từ 3km đến 5km tính phí cơ bản
            else:
                extra_km = dist - 5.0  # Lấy đúng số km lẻ vượt quá 5km
                fee = w.base_fee + (extra_km * w.fee_per_km)
            # ------------------------------------------------

            # int(round(fee, -2)) sẽ giúp làm tròn số tiền lẻ đằng sau (VD: 17,234đ -> 17,200đ) cho đẹp
            return JsonResponse({'status': 'success', 'distance': round(dist, 2), 'fee': int(round(fee, -2))})
            
    return JsonResponse({'error': 'Error'}, status=400)
def shipping_page(request): 
    return render(request, 'shipping.html')

# ==========================================
# 4. ADMIN (QUẢN LÝ) - ĐÃ BẢO MẬT TUYỆT ĐỐI
# ==========================================

# Trạm gác kiểm tra quyền Admin
# Trạm gác kiểm tra quyền Admin
def is_admin(user):
    # 1. Nếu chưa đăng nhập -> Trả về False để Django tự đẩy ra trang /login/
    if not user.is_authenticated:
        return False
        
    # 2. Nếu đã đăng nhập và là staff/admin -> Cho phép qua
    if user.is_staff:
        return True
        
    # 3. Nếu đã đăng nhập nhưng là user thường -> Bắn lỗi 403
    raise PermissionDenied
@user_passes_test(is_admin, login_url='/login/')
def dashboard(request): 
    return render(request, 'admin/dashboard.html')

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

        try: price = int(price_raw)
        except ValueError: price = 0
        try: stock = int(stock)
        except ValueError: stock = 0

        if prod_id:
            p = Product.objects.get(id=prod_id)
            p.name, p.price, p.unit, p.stock_quantity, p.category, p.description = name, price, unit, stock, cat, desc
            if main_img: p.image = main_img
            p.save()
        else:
            p = Product.objects.create(name=name, price=price, unit=unit, stock_quantity=stock, category=cat, image=main_img, description=desc)
        
        for img in gallery: ProductImage.objects.create(product=p, image=img)
    return redirect('products')

@user_passes_test(is_admin, login_url='/login/')
def product_delete(request, id): 
    get_object_or_404(Product, id=id).delete()
    return redirect('products')

@user_passes_test(is_admin, login_url='/login/')
def categories_list(request): 
    return render(request, 'admin/categories.html', {'categories': Category.objects.all()})

@user_passes_test(is_admin, login_url='/login/')
def category_form(request): 
    return render(request, 'admin/category-form.html')

@user_passes_test(is_admin, login_url='/login/')
def category_save(request):
    if request.method == 'POST': 
        Category.objects.create(name=request.POST.get('name'))
    return redirect('categories')

@user_passes_test(is_admin, login_url='/login/')
def category_delete(request, id): 
    get_object_or_404(Category, id=id).delete()
    return redirect('categories')

@user_passes_test(is_admin, login_url='/login/')
def warehouse_list(request): 
    return render(request, 'admin/warehouses.html', {'warehouses': Warehouse.objects.all()})

@user_passes_test(is_admin, login_url='/login/')
def orders_list(request): 
    return render(request, 'admin/orders.html', {'orders': Order.objects.all().order_by('-order_date')})

@user_passes_test(is_admin, login_url='/login/')
def order_update_status(request):
    if request.method == 'POST':
        o = get_object_or_404(Order, id=request.POST.get('id'))
        new_status = request.POST.get('status')
        o.status = new_status
        o.save()
        
        # Thêm dòng này để báo cho người dùng biết đã cập nhật thành công
        messages.success(request, f'Đã cập nhật trạng thái đơn hàng #{o.id} thành: {new_status}')
        
    return redirect('orders')

@user_passes_test(is_admin, login_url='/login/')
def users_list(request): 
    return render(request, 'admin/users.html', {'users': User.objects.filter(is_superuser=False)})

@user_passes_test(is_admin, login_url='/login/')
def user_delete(request, id): 
    get_object_or_404(User, id=id).delete()
    return redirect('users')

@user_passes_test(is_admin, login_url='/login/')
def admin_map_view(request): 
    warehouse = Warehouse.objects.first() 
    return render(request, 'admin/map_clustering.html', {'warehouse': warehouse})

@user_passes_test(is_admin, login_url='/login/')
def api_orders_locations(request):
    orders = Order.objects.exclude(status__in=['ĐÃ GIAO', 'ĐÃ HỦY']).exclude(customer_lat__isnull=True)
    
    data = []
    for o in orders:
        data.append({
            'id': o.id,
            # Lấy tên đầy đủ của khách, nếu không có thì dùng username
            'customer': o.user.get_full_name() or o.user.username,
            'lat': o.customer_lat,
            'lon': o.customer_lon,
            'status': o.status,
            'total': o.total_amount, 
            'address': o.shipping_address 
        })
        
    return JsonResponse({'orders': data})

@user_passes_test(is_admin, login_url='/login/')
def inventory_manage(request):
    warehouses = Warehouse.objects.all()
    products = Product.objects.all()
    # Lấy lịch sử 20 giao dịch gần nhất
    transactions = InventoryTransaction.objects.all().order_by('-date')[:20]

    if request.method == 'POST':
        warehouse_id = request.POST.get('warehouse')
        transaction_type = request.POST.get('transaction_type')
        note = request.POST.get('note', '')

        # Lấy danh sách (mảng) các sản phẩm và số lượng từ form đa dòng
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')

        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        try:
            # Dùng transaction.atomic: Cả lô hàng phải thành công, nếu 1 món lỗi thì rollback toàn bộ
            with transaction.atomic():
                # Dùng zip() để duyệt song song mảng ID và mảng Số lượng
                for p_id, qty_str in zip(product_ids, quantities):
                    try:
                        quantity = int(qty_str)
                    except ValueError:
                        messages.error(request, 'Lỗi: Có số lượng không hợp lệ!')
                        raise ValueError("Dừng giao dịch")

                    if quantity <= 0:
                        messages.error(request, 'Lỗi: Số lượng xuất/nhập phải lớn hơn 0!')
                        raise ValueError("Dừng giao dịch")

                    product = get_object_or_404(Product, id=p_id)
                    stock_record, created = Stock.objects.get_or_create(warehouse=warehouse, product=product)

                    if transaction_type == 'IMPORT':
                        stock_record.quantity += quantity
                        product.stock_quantity += quantity 
                    elif transaction_type == 'EXPORT':
                        if stock_record.quantity >= quantity:
                            stock_record.quantity -= quantity
                            product.stock_quantity -= quantity
                        else:
                            messages.error(request, f'Lỗi: Kho {warehouse.name} chỉ còn {stock_record.quantity} {product.unit} {product.name}. KHÔNG ĐỦ ĐỂ XUẤT!')
                            raise ValueError("Dừng giao dịch")

                    # Lưu DB
                    stock_record.save()
                    product.save()

                    # Ghi log
                    InventoryTransaction.objects.create(
                        warehouse=warehouse,
                        product=product,
                        transaction_type=transaction_type,
                        quantity=quantity,
                        note=note,
                        user=request.user
                    )
            
            action_text = "Nhập" if transaction_type == 'IMPORT' else "Xuất"
            messages.success(request, f'Đã {action_text} thành công {len(product_ids)} loại vật liệu tại {warehouse.name}!')
            
        except ValueError:
            # Lỗi đã được xử lý bằng messages.error ở trên, pass để reload trang
            pass 

        return redirect('inventory_manage')

    return render(request, 'admin/inventory_form.html', {
        'warehouses': warehouses,
        'products': products,
        'transactions': transactions
    })
@user_passes_test(is_admin, login_url='/login/')
def print_inventory_receipt(request, transaction_id):
    # Lấy ra giao dịch cụ thể dựa vào ID
    transaction = get_object_or_404(InventoryTransaction, id=transaction_id)
    
    # Render ra một template riêng biệt dành riêng cho việc in ấn
    return render(request, 'admin/inventory_receipt.html', {
        'transaction': transaction
    })

@user_passes_test(is_admin, login_url='/login/')
def warehouse_form(request, id=None):
    # Lấy kho hàng theo ID để sửa (nếu có id)
    warehouse = get_object_or_404(Warehouse, id=id) if id else None
    return render(request, 'admin/warehouse_form.html', {'warehouse': warehouse})

@user_passes_test(is_admin, login_url='/login/')
def warehouse_save(request):
    if request.method == 'POST':
        w_id = request.POST.get('id')
        name = request.POST.get('name')
        address = request.POST.get('address')
        
        # Chuyển đổi an toàn sang float/int
        try:
            lat = float(request.POST.get('latitude', 0))
            lon = float(request.POST.get('longitude', 0))
            base_fee = int(request.POST.get('base_fee', 0))
            fee_per_km = int(request.POST.get('fee_per_km', 0))
        except ValueError:
            messages.error(request, 'Lỗi định dạng số ở tọa độ hoặc chi phí!')
            return redirect('warehouses')

        if w_id:
            # Sửa kho hàng hiện tại
            w = Warehouse.objects.get(id=w_id)
            w.name, w.address = name, address
            w.latitude, w.longitude = lat, lon
            w.base_fee, w.fee_per_km = base_fee, fee_per_km
            w.save()
            messages.success(request, 'Đã cập nhật cấu hình kho hàng thành công!')
        else:
            # Nếu sau này bạn muốn thêm chức năng tạo kho mới
            Warehouse.objects.create(
                name=name, address=address, 
                latitude=lat, longitude=lon, 
                base_fee=base_fee, fee_per_km=fee_per_km
            )
            messages.success(request, 'Đã thêm kho hàng mới!')
            
    return redirect('warehouses')

# Thêm vào cuối file views.py
def custom_catch_all_404(request, *args, **kwargs):
    return render(request, '404.html', status=404)