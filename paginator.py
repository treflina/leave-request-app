from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger


class PaginationMixin:
    def paginate(self, qs, page_name):
        paginator = Paginator(qs, self.paginate_by)
        page = self.request.GET.get(page_name)
        try:
            qs = paginator.page(page)
        except PageNotAnInteger:
            qs = paginator.page(1)
        except EmptyPage:
            qs = paginator.page(paginator.num_pages)
        return qs
