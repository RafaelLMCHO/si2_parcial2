import 'package:flutter/foundation.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/storage/local_database.dart';
import '../../../core/utils/error_mapper.dart';
import '../../../core/utils/network_status.dart';
import '../data/catalogo_models.dart';
import '../data/catalogo_repository.dart';

class CatalogoController extends ChangeNotifier {
  CatalogoController(this._repository, this._database, this._networkStatus) {
    _networkStatus.addListener(_onNetworkChanged);
  }

  final CatalogoRepository _repository;
  final LocalDatabase _database;
  final NetworkStatus _networkStatus;

  List<Prenda> _items = const [];
  AuxiliaresCatalogo _auxiliares = const AuxiliaresCatalogo();
  CatalogoFiltros _filtros = const CatalogoFiltros();
  bool _loading = false;
  bool _isOffline = false;
  bool _sinDatosLocales = false;
  String? _error;
  int _total = 0;
  int _versionCatalogo = 0;
  DateTime? _cacheUpdatedAt;
  String? _empresaSlug;

  List<Prenda> get items => _items;
  AuxiliaresCatalogo get auxiliares => _auxiliares;
  CatalogoFiltros get filtros => _filtros;
  bool get loading => _loading;
  bool get isOffline => _isOffline;
  bool get sinDatosLocales => _sinDatosLocales;
  bool get isOnline => _networkStatus.value;
  String? get error => _error;
  int get total => _total;
  int get versionCatalogo => _versionCatalogo;
  DateTime? get cacheUpdatedAt => _cacheUpdatedAt;
  String? get empresaSlug => _empresaSlug;
  bool get hasItems => _items.isNotEmpty;

  Future<void> cargarInicial(String empresaSlug) async {
    _empresaSlug = empresaSlug;
    _filtros = const CatalogoFiltros();
    _items = const [];
    _auxiliares = const AuxiliaresCatalogo();
    _total = 0;
    _versionCatalogo = 0;
    _cacheUpdatedAt = null;
    _isOffline = false;
    _sinDatosLocales = false;
    _error = null;
    await recargar(empresaSlug, refreshAuxiliares: true);
  }

  Future<void> recargar(
    String empresaSlug, {
    bool refreshAuxiliares = false,
  }) async {
    _empresaSlug = empresaSlug;
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      if (_networkStatus.value) {
        await _cargarOnline(empresaSlug, refreshAuxiliares: refreshAuxiliares);
      } else {
        await _cargarOffline(empresaSlug);
      }
    } catch (error) {
      if (isNetworkError(error)) {
        _networkStatus.markOffline();
        await _cargarOffline(empresaSlug);
      } else {
        _error = ApiException.fromObject(
          error,
          fallback: 'No se pudo cargar el catalogo.',
        ).message;
        await _cargarOffline(empresaSlug);
      }
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> aplicarFiltros(
    CatalogoFiltros filtros,
    String empresaSlug,
  ) async {
    _filtros = filtros;
    await recargar(empresaSlug, refreshAuxiliares: false);
  }

  Future<void> limpiarFiltros(String empresaSlug) async {
    _filtros = const CatalogoFiltros();
    await recargar(empresaSlug, refreshAuxiliares: false);
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> _cargarOnline(
    String empresaSlug, {
    required bool refreshAuxiliares,
  }) async {
    if (refreshAuxiliares || _auxiliares.isEmpty) {
      await _cargarAuxiliares(empresaSlug);
    }

    final response = await _repository.listarPrendas(
      empresaSlug: empresaSlug,
      filtros: _filtros,
    );

    _items = response.items;
    _total = response.total;
    _versionCatalogo = response.versionCatalogo;
    _isOffline = false;
    _sinDatosLocales = false;
    _cacheUpdatedAt = null;

    if (_auxiliares.isEmpty && _items.isNotEmpty) {
      _auxiliares = AuxiliaresCatalogo.fromPrendas(_items);
    }

    if (!_filtros.hasFilters) {
      await _database.saveCatalogoSnapshot(
        empresaSlug: empresaSlug,
        version: response.versionCatalogo,
        items: response.items,
      );
      await _database.saveCatalogoAuxiliares(
        empresaSlug: empresaSlug,
        auxiliares: _auxiliares,
      );
    }
  }

  Future<void> _cargarAuxiliares(String empresaSlug) async {
    try {
      final remote = await _repository.obtenerAuxiliares(empresaSlug);
      if (!remote.isEmpty) {
        _auxiliares = remote;
        await _database.saveCatalogoAuxiliares(
          empresaSlug: empresaSlug,
          auxiliares: remote,
        );
        return;
      }
    } catch (_) {
      // Si falla, se intenta con el cache local o con los datos del catalogo.
    }

    final cached = await _database.readCatalogoAuxiliares(empresaSlug);
    if (cached != null && !cached.isEmpty) {
      _auxiliares = cached;
      return;
    }

    final snapshot = await _database.readCatalogoSnapshot(empresaSlug);
    if (snapshot != null) {
      _auxiliares = AuxiliaresCatalogo.fromPrendas(snapshot.items);
    }
  }

  Future<void> _cargarOffline(String empresaSlug) async {
    final snapshot = await _database.readCatalogoSnapshot(empresaSlug);
    if (snapshot == null) {
      _items = const [];
      _total = 0;
      _versionCatalogo = 0;
      _isOffline = true;
      _sinDatosLocales = true;
      _cacheUpdatedAt = null;
      return;
    }

    final filtered = filtrarPrendasLocal(snapshot.items, _filtros);
    _items = filtered;
    _total = filtered.length;
    _versionCatalogo = snapshot.version;
    _isOffline = true;
    _sinDatosLocales = false;
    _cacheUpdatedAt = snapshot.updatedAt;

    if (_auxiliares.isEmpty) {
      _auxiliares =
          await _database.readCatalogoAuxiliares(empresaSlug) ??
          AuxiliaresCatalogo.fromPrendas(snapshot.items);
    }
  }

  void _onNetworkChanged() {
    notifyListeners();
  }

  @override
  void dispose() {
    _networkStatus.removeListener(_onNetworkChanged);
    super.dispose();
  }
}
