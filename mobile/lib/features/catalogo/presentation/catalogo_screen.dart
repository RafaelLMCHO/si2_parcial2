import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/routing/role_permissions.dart';
import '../../../core/session/session_controller.dart';
import '../data/catalogo_models.dart';
import 'catalogo_controller.dart';
import 'widgets/filtros_catalogo_sheet.dart';
import 'widgets/prenda_card.dart';

class CatalogoScreen extends StatefulWidget {
  const CatalogoScreen({
    super.key,
    required this.session,
    required this.controller,
  });

  final SessionController session;
  final CatalogoController controller;

  @override
  State<CatalogoScreen> createState() => _CatalogoScreenState();
}

class _CatalogoScreenState extends State<CatalogoScreen> {
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _searchController.addListener(_onSearchTextChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      widget.controller.cargarInicial(widget.session.tenant);
      widget.session.prefetcharCatalogoOfflineSilencioso();
    });
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchTextChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchTextChanged() {
    setState(() {});
  }

  Future<void> _recargar() async {
    await widget.controller.recargar(
      widget.session.tenant,
      refreshAuxiliares: true,
    );
  }

  Future<void> _aplicarFiltros(CatalogoFiltros filtros) async {
    final nextSearch = filtros.search ?? '';
    if (_searchController.text != nextSearch) {
      _searchController.text = nextSearch;
      _searchController.selection = TextSelection.collapsed(
        offset: nextSearch.length,
      );
    }
    await widget.controller.aplicarFiltros(filtros, widget.session.tenant);
  }

  CatalogoFiltros _withSearch(CatalogoFiltros current, String search) {
    return CatalogoFiltros(
      categoriaId: current.categoriaId,
      temporadaId: current.temporadaId,
      coleccionId: current.coleccionId,
      tallaId: current.tallaId,
      colorId: current.colorId,
      precioMin: current.precioMin,
      precioMax: current.precioMax,
      genero: current.genero,
      search: search.trim().isEmpty ? null : search.trim(),
    );
  }

  Future<void> _buscar(String value) async {
    await _aplicarFiltros(_withSearch(widget.controller.filtros, value));
  }

  Future<void> _limpiarFiltros() async {
    _searchController.clear();
    await widget.controller.limpiarFiltros(widget.session.tenant);
  }

  Future<void> _abrirFiltros() async {
    final result = await showModalBottomSheet<CatalogoFiltros>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => FiltrosCatalogoSheet(
        initial: widget.controller.filtros,
        auxiliares: widget.controller.auxiliares,
      ),
    );
    if (!mounted || result == null) {
      return;
    }
    await _aplicarFiltros(result);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        final controller = widget.controller;
        final activeFilters = controller.filtros.activeCount;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Catalogo'),
            actions: [
              if (canAccessRoute(widget.session.user?.rol, '/checkout'))
                IconButton(
                  tooltip: 'Carrito y Checkout',
                  onPressed: () => context.push('/checkout'),
                  icon: const Icon(Icons.shopping_bag_outlined),
                ),
              IconButton(
                tooltip: 'Filtros',
                onPressed: controller.loading ? null : _abrirFiltros,
                icon: Badge.count(
                  count: activeFilters,
                  isLabelVisible: activeFilters > 0,
                  child: const Icon(Icons.tune),
                ),
              ),
            ],
          ),
          body: SafeArea(
            child: Column(
              children: [
                if (controller.loading)
                  const LinearProgressIndicator(minHeight: 2),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                  child: TextField(
                    controller: _searchController,
                    textInputAction: TextInputAction.search,
                    onSubmitted: _buscar,
                    decoration: InputDecoration(
                      hintText: 'Buscar por nombre, codigo o marca',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: _searchController.text.isEmpty
                          ? null
                          : IconButton(
                              tooltip: 'Limpiar busqueda',
                              onPressed: () {
                                _searchController.clear();
                                _buscar('');
                              },
                              icon: const Icon(Icons.close),
                            ),
                      filled: true,
                      fillColor: const Color(0xFFF9FAFB),
                      isDense: true,
                    ),
                  ),
                ),
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: _recargar,
                    child: ListView(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        if (controller.isOffline)
                          _OfflineBanner(
                            lastDownload: controller.cacheUpdatedAt,
                          ),
                        if (controller.sinDatosLocales) const _NoCacheCard(),
                        if (controller.error != null)
                          _ErrorCard(
                            message: controller.error!,
                            onRetry: () {
                              controller.clearError();
                              _recargar();
                            },
                          ),
                        if (!controller.sinDatosLocales &&
                            activeFilters > 0) ...[
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  activeFilters == 1
                                      ? '1 filtro activo'
                                      : '$activeFilters filtros activos',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ),
                              TextButton.icon(
                                onPressed: _limpiarFiltros,
                                icon: const Icon(
                                  Icons.filter_alt_off,
                                  size: 18,
                                ),
                                label: const Text('Limpiar filtros'),
                              ),
                            ],
                          ),
                        ],
                        if (controller.loading && !controller.hasItems)
                          const Padding(
                            padding: EdgeInsets.only(top: 48),
                            child: Center(child: CircularProgressIndicator()),
                          )
                        else if (!controller.hasItems &&
                            !controller.sinDatosLocales) ...[
                          const SizedBox(height: 36),
                          _EmptyCard(hasFilters: activeFilters > 0),
                        ] else ...[
                          const SizedBox(height: 4),
                          Text(
                            controller.total == 1
                                ? '1 prenda'
                                : '${controller.total} prendas',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 8),
                          ...controller.items.map(
                            (prenda) => Padding(
                              padding: const EdgeInsets.only(bottom: 10),
                              child: PrendaCard(
                                prenda: prenda,
                                onTap: () => context.push(
                                  '/catalogo/prenda/${prenda.id}',
                                  extra: prenda,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _OfflineBanner extends StatelessWidget {
  const _OfflineBanner({this.lastDownload});

  final DateTime? lastDownload;

  @override
  Widget build(BuildContext context) {
    final lastDownload = this.lastDownload;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBEB),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFDE68A)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.wifi_off, color: Color(0xFF92400E), size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Modo sin conexión: la información de catálogo y precios corresponde a la última descarga local y podría estar desactualizada.',
                  style: TextStyle(color: Color(0xFF92400E), height: 1.4),
                ),
                if (lastDownload != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Ultima descarga: ${DateFormat('dd/MM/yyyy HH:mm').format(lastDownload.toLocal())}',
                    style: const TextStyle(
                      color: Color(0xFF92400E),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _NoCacheCard extends StatelessWidget {
  const _NoCacheCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFECACA)),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.cloud_off, color: Color(0xFF991B1B), size: 20),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'No hay catalogo descargado en este dispositivo.',
                  style: TextStyle(
                    color: Color(0xFF991B1B),
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 6),
          Text(
            'Conéctese al menos una vez para descargar el catálogo.',
            style: TextStyle(color: Color(0xFF991B1B), height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFECACA)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Color(0xFF991B1B)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: Color(0xFF991B1B)),
            ),
          ),
          TextButton(onPressed: onRetry, child: const Text('Reintentar')),
        ],
      ),
    );
  }
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.hasFilters});

  final bool hasFilters;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const Icon(Icons.search_off, size: 38),
            const SizedBox(height: 10),
            Text(
              hasFilters ? 'No hay prendas que coincidan con los filtros.' : 'El catalogo no tiene prendas registradas para esta tienda.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 6),
            Text(
              'Deslice hacia abajo para actualizar.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
