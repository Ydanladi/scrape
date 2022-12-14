from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from .forms import CommentForm , UserRegistrationForm
from django.contrib.auth import login, authenticate
from django.db.models import Q
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render
from .models import Product 
from .scraper.jumia import get_jumia_product
from .scraper import jumia, konga
import random

# Create your views here.

def product_detail(request,id,product):
    product = get_object_or_404(
        Product,
        slug=product,
        id = id,
    )

    comments = product.comments.filter(active=True)
    new_comment = None
    platforms = []
    prd = {
        'name':product.name,
        'brand':product.brand,
        'category':product.category
    }
    platforms.append(get_jumia_product(prd))

    if request.method == 'POST':
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.product = product
            new_comment.username = request.user.username
            new_comment.save()
            return HttpResponseRedirect(f'{product.slug}',
                    {
                        'product':product,
                        'comments':comments,
                        'platforms':platforms,
                        'new_comment':new_comment,
                        'comment_form':comment_form
                    },          )
    else:
            comment_form = CommentForm()

    return render(request,'product/detail.html',
                    {
                        'product':product,
                        'comments':comments,
                        'platforms':platforms,
                        'new_comment':new_comment,
                        'comment_form':comment_form
                    },            
    )


class ProductListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'product/list.html'

class SearchResultView(ListView):
    model = Product
    template_name = 'product/search_result.html'
    context_object_name = 'products'
    def get_queryset(self):
        query = self.request.GET.get('search')
        list = Product.objects.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        )
        return list

def register(request):
    if request.method=='POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit = False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return render(request,'registration/register_done.html',{'new_user': user})
    else:
        form=UserRegistrationForm()       
    return render(request,'registration/register.html',{'form':form})


def user_login(request):
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')
        user=authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                
                login(request,user)
                return HttpResponseRedirect('product_detail')
            else:
                return HttpResponse('your Account is Inactive, contact Admin')
def user_search(request):
    if request.GET.get('search'):
        q = request.GET.get('search')
        products = []
        #products.extend(asos.asos_scraper_bot(q))
        #products.extend(ebay.ebay_scraper_bot(q))
        products.extend(jumia.jumia_scraper_bot(q))
        products.extend(konga.konga_scraper_bot(q))
        #products.extend(payporte.payporte_scraper_bot(q))
        random.shuffle(products)

        objects = Product.objects.get_or_create(title=products[0]['name'], price=products[0]['price'], vendor=products[0]['from'])
        objects.save()
        return render(request, 'product/product_list.html', {'products': products})
    
    else:
        products = Product.objects.all()
        return render(request, 'product/product_list.html', {'products': products})
    return render(request,'product/product_list',{'products':products})
       
