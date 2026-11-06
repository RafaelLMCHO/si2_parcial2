import 'package:flutter/foundation.dart';
import '../../../core/network/api_client.dart';

/// Controlador para CU-08: Facturación SaaS e Historial de Facturas
class FacturacionController extends ChangeNotifier {
  final ApiClient _apiClient;
  bool _loading = false;
  String? _error;
  List<dynamic> _facturas = [];

  FacturacionController(this._apiClient);

  bool get loading => _loading;
  String? get error => _error;
  List<dynamic> get facturas => _facturas;

  Future<void> cargarFacturas() async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _apiClient.get('/saas/facturas');
      _facturas = res is List ? res : (res['items'] ?? []);
      _loading = false;
    } catch (e) {
      _loading = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  Future<String?> descargarFacturaUrl(String facturaId) async {
    try {
      final res = await _apiClient.get('/saas/facturas/$facturaId/pdf');
      return res['pdf_url'];
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    }
  }
}

