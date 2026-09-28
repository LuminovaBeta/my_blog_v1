from django.urls import path

from . import views


app_name = 'library'

urlpatterns = [
    path('', views.bookshelf, name='bookshelf'),
    path('preview/', views.book_preview, name='book_preview'),
    path('add/', views.add_book_preview, name='add_book'),
]
