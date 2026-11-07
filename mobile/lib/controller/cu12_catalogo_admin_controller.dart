import 'package:flutter/foundation.dart';
import '../core/network/api_client.dart';

/// CU-12: Catálogo Admin (Prendas, Categorías y Variantes)
class CU12CatalogoAdminController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _prendas = [];

  CU12CatalogoAdminController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get prendas => _prendas;

  Future<void> cargarPrendas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/catalogo/admin/prendas');
      _prendas = res is List ? res : (res['items'] ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }
}

