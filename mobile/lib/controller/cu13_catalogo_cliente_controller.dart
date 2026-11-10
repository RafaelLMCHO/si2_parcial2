import 'package:flutter/foundation.dart';
import '../features/catalogo/data/catalogo_models.dart';
import '../features/catalogo/presentation/catalogo_controller.dart';

/// CU-13: Catálogo Cliente (Exploración, Búsqueda y Filtros)
class CU13CatalogoClienteController extends ChangeNotifier {
  final CatalogoController _catalogoController;
  final String? _empresaSlug;

  CU13CatalogoClienteController(this._catalogoController, {this._empresaSlug}) {
    _catalogoController.addListener(notifyListeners);
  }

  String get _slug => _empresaSlug ?? _catalogoController.empresaSlug ?? 'demo';

  bool get loading => _catalogoController.loading;
  String? get error => _catalogoController.error;
  List<Prenda> get prendas => _catalogoController.items;
  bool get isOffline => _catalogoController.isOffline;

  Future<void> cargar({String? empresaSlug}) =>
      _catalogoController.recargar(empresaSlug ?? _slug, refreshAuxiliares: true);
  Future<void> buscar(String q, {String? empresaSlug}) => _catalogoController
      .aplicarFiltros(CatalogoFiltros(search: q), empresaSlug ?? _slug);

  @override
  void dispose() {
    _catalogoController.removeListener(notifyListeners);
    super.dispose();
  }
}

