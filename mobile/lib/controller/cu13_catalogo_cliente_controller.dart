import 'package:flutter/foundation.dart';
import '../features/catalogo/presentation/catalogo_controller.dart';

/// CU-13: Catálogo Cliente (Exploración, Búsqueda y Filtros)
class CU13CatalogoClienteController extends ChangeNotifier {
  final CatalogoController _catalogoController;

  CU13CatalogoClienteController(this._catalogoController) {
    _catalogoController.addListener(notifyListeners);
  }

  bool get loading => _catalogoController.loading;
  String? get error => _catalogoController.error;
  List<dynamic> get prendas => _catalogoController.prendas;
  bool get isOffline => _catalogoController.isOffline;

  Future<void> cargar() => _catalogoController.load();
  Future<void> buscar(String q) => _catalogoController.setQuery(q);

  @override
  void dispose() {
    _catalogoController.removeListener(notifyListeners);
    super.dispose();
  }
}

