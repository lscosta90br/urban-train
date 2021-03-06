# coding=utf-8
import json
from datetime import date, timedelta

import pandas as pd
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView, CreateView, TemplateView, UpdateView, DeleteView

from utils import change_comma_by_dot
from vendor.cruds_adminlte.crud import CRUDView
from .forms import (
    SegmentoForm, GastoForm, RabbiitForm,
    PecasForm, ComercioForm, ItensPecasForm, ItemPecasFormSet,
    HoraTrabalhadaForm
)
from .models import (
    Segmento, Gasto, Rabbiit, HoraTrabalhada, City,
    Pecas, Itenspecas, Comercio
)


class GastoCRUD(CRUDView):
    model = Gasto
    template_name_base = 'ccruds'
    # template_name_base = 'website/gasto/gasto_list.html'
    namespace = None
    check_perms = True
    views_available = ['list', 'create', 'delete', 'update']
    fields = ['name', 'slug', 'valor', 'nro_da_parcela', 'valor_da_parcela', 'parcelas', 'datagasto', ]
    list_fields = ('name', 'parcelas', 'nro_da_parcela', 'valor_da_parcela', 'valor', 'datagasto', 'segmento',)
    search_fields = ('name__icontains',)
    paginate_by = 10
    paginate_template = 'cruds/pagination/prev_next.html'

    add_form = GastoForm
    update_form = GastoForm

    def get_create_view(self):
        View = super(GastoCRUD, self).get_create_view()

        class UCreateView(View):

            def form_valid(self, form):
                self.object = form.save(commit=False)
                # self.object.save()
                dados = self.object
                quantidades_parcelas_faltantes = 1
                numero_da_parcela = self.object.nro_da_parcela
                # form.cleaned_data
                while self.object.parcelas >= quantidades_parcelas_faltantes:
                    # for dado in range(form.cleaned_data.parcelas):
                    day = 30 * quantidades_parcelas_faltantes - 30
                    gasto = Gasto()
                    gasto.name = self.object.name
                    gasto.slug = self.object.slug
                    gasto.nro_da_parcela = numero_da_parcela
                    gasto.valor = self.object.valor
                    gasto.valor_da_parcela = self.object.valor_da_parcela
                    gasto.datagasto = self.object.datagasto + timedelta(days=day)
                    gasto.segmento = self.object.segmento
                    gasto.nro_da_parcela = quantidades_parcelas_faltantes
                    gasto.parcelas = self.object.parcelas
                    self.object.save()
                    quantidades_parcelas_faltantes += 1
                    numero_da_parcela += 1

                return HttpResponseRedirect(self.get_success_url())

        return UCreateView


class SegmentoCRUD(CRUDView):
    model = Segmento
    template_name_base = 'ccruds'
    namespace = None
    check_perms = True
    views_available = ['create', 'list', 'delete', 'update']
    list_fields = ['name', ]
    search_fields = ['name__icontains']
    split_space_search = ' '  # default False
    add_form = SegmentoForm
    update_form = SegmentoForm


class RabbiitCRUD(CRUDView):
    model = Rabbiit
    template_name_base = 'ccruds'
    namespace = None
    check_perms = True
    views_available = ['create', 'list', 'delete', 'update']
    list_fields = [
        'created_at', 'description', 'time_start',
        'time_end', 'time_total', 'rate_hour',
        'rate_total',
    ]
    search_fields = ['description__icontains']
    add_form = RabbiitForm
    update_form = RabbiitForm


class HoraTrabalhadaListView(TemplateView):
    model = HoraTrabalhada
    template_name = 'website/horatrabalhada/horatrabalhada_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset_list = HoraTrabalhada.objects.all()
        query = self.request.GET.get("q")
        if query:
            queryset_list = queryset_list.filter(
                Q(comercio__icontains=query) |
                Q(data__icontains=query)
            ).distinct()

        paginator = Paginator(queryset_list, 5)  # Show 5 pecas per page
        page = self.request.GET.get('page')
        try:
            queryset_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            queryset_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 999), deliver last page of results.
            queryset_list = paginator.page(paginator.num_pages)

        return queryset_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_pecas = HoraTrabalhada.objects.order_by('-id')
        # queryset_list = Pecas.objects.all()
        query = self.request.GET.get("q")
        if query:
            list_pecas = list_pecas.filter(
                Q(comercio__description__icontains=query) |
                Q(data__icontains=query)
            ).distinct()
        paginator = Paginator(list_pecas, self.paginate_by)

        page = self.request.GET.get('page')

        try:
            object_list = paginator.page(page)
        except PageNotAnInteger:
            object_list = paginator.page(1)
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages)
        context['object_list'] = object_list
        return context


class HoraTrabalhadaCreateView(CreateView):
    model = HoraTrabalhada
    template_name = 'website/horatrabalhada/horatrabalhada_form.html'
    form_class = HoraTrabalhadaForm

    def get_context_data(self, **kwargs):
        context = super(HoraTrabalhadaCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context['forms'] = HoraTrabalhadaForm(self.request.POST)
        else:
            context['forms'] = HoraTrabalhadaForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        forms = context['forms']
        if forms.is_valid():
            self.object = form.save()
            forms.instance = self.object
            forms.save()
            return redirect('website_horatrabalhada_list')
        else:
            return self.render_to_response(self.get_context_data(form=form))


class HoraTrabalhadaEditView(UpdateView):
    model = HoraTrabalhada
    template_name = 'website/horatrabalhada/horatrabalhada_form.html'
    form_class = HoraTrabalhadaForm

    def get_context_data(self, **kwargs):
        context = super(HoraTrabalhadaEditView, self).get_context_data(**kwargs)
        if self.request.POST:
            context['forms'] = HoraTrabalhadaForm(self.request.POST, instance=self.object)
        else:
            context['forms'] = HoraTrabalhadaForm(instance=self.object)
        return context

    # def form_valid(self, form):
    #     context = self.get_context_data()
    #     form = context['forms']
    #     formset = context['formset']
    #     if form.is_valid():
    #         sizeIensPecas = len(formset.cleaned_data)
    #         try:
    #             form.cleaned_data['total'] = str(total)
    #         except Exception as err:
    #             form.cleaned_data['total'] = 0
    #             print(f'Err.: {err}')
    #         # form = form.save(commit=False)
    #         # form.total = str(total)
    #         form.save()
    #         formset.save()
    #     return redirect('website_horatrabalhada_list')
    #     else:
    #         return self.render_to_response(self.get_context_data(form=form))


class HoraTrabalhadaDeleteView(DeleteView):
    success_url = reverse_lazy("website_horatrabalhada_list")
    model = HoraTrabalhada
    template_name_suffix = '/horatrabalhada_confirm_delete'

    # def get(self, request, *args, **kwargs):
    #     try:
    #         self.get_queryset().get(id=kwargs['pk']).delete()
    #     except Exception as err:
    #         print(err)
    #     return self.post(request, *args, **kwargs)
    #
    # def get_queryset(self):
    #     return HoraTrabalhada.objects.filter(id=self.kwargs['pk'])


class CityCRUD(CRUDView):
    model = City
    template_name_base = 'ccruds'
    namespace = None
    check_perms = True
    views_available = ['create', 'list', 'delete', 'update']
    fields = ['id', 'description', ]
    list_fields = ['id', 'description', ]


class PecasListView(TemplateView):
    model = Pecas
    template_name = 'website/pecas_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset_list = Pecas.objects.all()
        query = self.request.GET.get("q")
        if query:
            queryset_list = queryset_list.filter(
                Q(comercio__icontains=query) |
                Q(data__icontains=query)
            ).distinct()

        paginator = Paginator(queryset_list, 5)  # Show 5 pecas per page
        page = self.request.GET.get('page')
        try:
            queryset_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            queryset_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 999), deliver last page of results.
            queryset_list = paginator.page(paginator.num_pages)

        return queryset_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_pecas = Pecas.objects.order_by('-id')
        # queryset_list = Pecas.objects.all()
        query = self.request.GET.get("q")
        if query:
            list_pecas = list_pecas.filter(
                Q(comercio__description__icontains=query) |
                Q(data__icontains=query)
            ).distinct()
        paginator = Paginator(list_pecas, self.paginate_by)

        page = self.request.GET.get('page')

        try:
            object_list = paginator.page(page)
        except PageNotAnInteger:
            object_list = paginator.page(1)
        except EmptyPage:
            object_list = paginator.page(paginator.num_pages)
        context['object_list'] = object_list
        # context['object_list'] = Pecas.objects.order_by('-id')
        return context


class PecasCreateView(CreateView):
    model = Pecas
    template_name = 'website/pecas_create.html'
    form_class = PecasForm

    def get_context_data(self, **kwargs):
        context = super(PecasCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context['forms'] = PecasForm(self.request.POST)
            context['formset'] = ItemPecasFormSet(self.request.POST)
        else:
            context['forms'] = PecasForm()
            context['formset'] = ItemPecasFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        forms = context['forms']
        formset = context['formset']
        if forms.is_valid() and formset.is_valid():
            self.object = form.save()
            forms.instance = self.object
            formset.instance = self.object
            forms.save()
            formset.save()
            return redirect('website_pecas_list')
        else:
            return self.render_to_response(self.get_context_data(form=form))


class PecasEditView(UpdateView):
    model = Pecas
    template_name = 'website/pecas_create.html'
    form_class = PecasForm

    def get_context_data(self, **kwargs):
        context = super(PecasEditView, self).get_context_data(**kwargs)
        if self.request.POST:
            context['forms'] = PecasForm(self.request.POST, instance=self.object)
            context['formset'] = ItemPecasFormSet(self.request.POST, instance=self.object)
        else:
            context['forms'] = PecasForm(instance=self.object)
            context['formset'] = ItemPecasFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        form = context['forms']
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            sizeIensPecas = len(formset.cleaned_data)
            total = 0.00
            for chave in range(sizeIensPecas):
                try:
                    total += float(formset.cleaned_data[chave]['subtotal'])
                except:
                    ...
            try:
                form.cleaned_data['total'] = str(total)
            except Exception as err:
                form.cleaned_data['total'] = 0
                print(f'Err.: {err}')
            # form = form.save(commit=False)
            # form.total = str(total)
            form.save()
            formset.save()
            return redirect('website_pecas_list')
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ItensPecasCRUD(CRUDView):
    model = Itenspecas
    template_name_base = 'ccruds'
    form_class = PecasForm
    namespace = None
    check_perms = True
    views_available = ['create', 'list', 'delete', 'update']
    fields = ['description', 'pecas', 'price', 'quantity', 'subtotal', ]
    list_fields = ['id', 'description', 'pecas', 'price', 'quantity', 'subtotal', ]
    # inlines = [Itenspecas_AjaxCRUD, ]
    add_form = ItensPecasForm
    update_form = ItensPecasForm
    paginate_by = 40


class ComercioCRUD(CRUDView):
    model = Comercio
    template_name_base = 'ccruds'  # customer cruds => ccruds
    namespace = None
    # search_fields = ('head__name__icontains', 'head__email__icontains')
    check_perms = True
    views_available = ['create', 'list', 'update', 'delete', ]
    fields = ['description']
    list_fields = ('id', 'description',)
    add_form = ComercioForm
    update_form = ComercioForm


class GastoSegmentoListView(ListView):
    template_name = "website/gastosPorSegmento.html"
    context_object_name = "gastos"
    paginate_by = 5

    def get_queryset(self):
        slug = 'supermercados'
        resultado = Gasto.objects.filter(segmento__slug=slug)
        # resultado = Gasto.objects.filter(segmento__slug=self.kwargs['slug'])
        return resultado

    def get_context_data(self, **kwargs):
        context = super(GastoSegmentoListView, self).get_context_data(**kwargs)
        list_exam = Gasto.objects.all()
        context['current_segmento'] = list_exam
        return context


# RELATÓRIO DE GASTOS POR MÊS
# ----------------------------------------------

def gastosPorMesView(request):
    template = "website/gastosPorMes.html"
    qs = Gasto.objects.all()  # Use the Pandas Manager
    segmentos = Segmento.objects.all()
    if request.method == 'POST':
        segmento_id = int(request.POST.get('segmento_id'))
        dtInicial = request.POST.get('dtInicial')
        dtFinal = request.POST.get('dtFinal')
        valor = request.POST.get('valor')
        if dtInicial == '':
            dtInicial = '2018-01-01'
        if dtFinal == '':
            dtFinal = date.today()
        df = qs.filter(segmento_id=segmento_id) \
            .to_dataframe(
            ['id', 'name', 'datagasto', 'valor', 'segmento_id'],
            index='segmento_id'
        )
        if valor:
            if not ',' in valor:
                valor = ''.join((valor, ',00'))
            df = df.loc[(df['valor'] == str(valor))]
            # df = df.loc[df['valor'] == '50,00']
        df['valor'] = [change_comma_by_dot(e) for e in df['valor']]
        # df['valor'] = [e.replace(",", ".") for e in df['valor']]
        df['valor'] = df['valor'].astype('float')
        df['datagasto'] = pd.to_datetime(df['datagasto'])
        df = df.loc[(df['datagasto'] >= dtInicial) & (df['datagasto'] <= dtFinal)]
        # df['valor'].loc[(df['datagasto'] >= dtInicial) & (df['datagasto'] <= dtFinal)].sum()
        """Format the column headers for the Bootstrap table, 
        they're just a list of field names,
        duplicated and turned into dicts like this: {'field': 'foo', 'title: 'foo'}
        columns = [{'field': f, 'title': f} for f in Gasto._Meta.fields]
        columns = [{'field': f['_verbose_name'], 'title': f} for f in Gasto._meta.fields]
        """
        col = [f for f in Gasto._meta.get_fields()]
        columns = [{'field': f, 'title': f} for f in df.columns]
        """Write the DataFrame to JSON (as easy as can be)
            output just the records (no fieldnames) as a collection of tuples
            Proceed to create your context object containing the columns and the data"""

        # data = df.to_json(orient='records', lines=True)
        context = {
            'data': df.itertuples(),
            'segmentos': segmentos
        }
    else:
        context = {
            'segmentos': segmentos
        }
    return render(request, template, context)


# CADASTRAMENTO DE GASTOS
# ----------------------------------------------


class AutoCompleteView(FormView):
    def get(self, request):
        q = request.GET.get('term', '').capitalize()
        if q:
            gastos = Gasto.objects.filter(name__icontains=q).order_by('name').distinct('name')
            # gastos = Gasto.objects.filter(name__icontains=q).distinct('name')
        else:
            gastos = Gasto.objects.all()
        results = []
        for gasto in gastos:
            if results:
                if gasto.name not in results[0]['name']:
                    gasto_json = {}
                    gasto_json['name'] = gasto.name
                    results.append(gasto_json)
            else:
                gasto_json = {}
                gasto_json['name'] = gasto.name
                results.append(gasto_json)
        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)


class AutoResponseView(ListView):
    ...
