from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.bookshelf, name="bookshelf"),
    path("add/", views.add_book, name="add_book"),
    path("preview/", views.book_preview, name="book_preview"),
    path("books/<int:pk>/", views.book_detail, name="book_detail"),
    path("books/<int:pk>/edit/", views.edit_book, name="edit_book"),
    path("books/<int:pk>/delete/", views.delete_book, name="delete_book"),
    path("books/<int:book_id>/quotes/add/", views.add_quote, name="add_quote"),
    path("quotes/<int:pk>/edit/", views.edit_quote, name="edit_quote"),
    path("quotes/<int:pk>/delete/", views.delete_quote, name="delete_quote"),
    path("excerpts/", views.excerpts, name="excerpts"),
    path("excerpts/add/", views.add_excerpt, name="add_excerpt"),
    path("excerpts/<int:pk>/edit/", views.edit_excerpt, name="edit_excerpt"),
    path("excerpts/<int:pk>/delete/", views.delete_excerpt, name="delete_excerpt"),
]
