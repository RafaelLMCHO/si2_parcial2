import 'dart:math' as math;

import 'package:flutter/foundation.dart';

import '../../../controller/cu26_registrar_reserva_offline_controller.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/storage/local_database.dart';
import '../../../core/utils/error_mapper.dart';
import '../../../core/utils/uuid_helper.dart';
import '../../inventario/data/inventario_models.dart';
import '../data/catalogo_models.dart';

/// Controlador para CU-14: Detalle de Producto, Variantes, Carrito y Reservas.
class DetalleProductoController extends ChangeNotifier {
  DetalleProductoController(
    this._apiClient, {
    LocalDatabase? localDatabase,
    SessionController? session,
  }) : _localDatabase = localDatabase ?? session?.database,
       _session = session;

  final ApiClient _apiClient;
  final LocalDatabase? _localDatabase;
  final SessionController? _session;

  bool _loading = false;
  bool _loadingDisponibilidad = false;
  bool _submitting = false;
  bool _stockCargado = false;
  bool _usandoStockLocal = false;
  bool _usuarioEligioVariante = false;
  String? _error;
  String? _actionError;
  Prenda? _prenda;
  VariantePrenda? _varianteSeleccionada;
  List<DisponibilidadSucursal> _sucursales = const [];
  bool _esFavorito = false;
  int _cantidad = 1;

  bool get loading => _loading;
  bool get loadingDisponibilidad => _loadingDisponibilidad;
  bool get submitting => _submitting;
  bool get stockCargado => _stockCargado;
  bool get usandoStockLocal => _usandoStockLocal;
  bool get isOffline => !(_session?.isOnline ?? true) || _usandoStockLocal;
  String? get error => _error;
  String? get actionError => _actionError;
  Prenda? get prenda => _prenda;
  VariantePrenda? get varianteSeleccionada => _varianteSeleccionada;
  List<DisponibilidadSucursal> get sucursales => _sucursales;
  bool get esFavorito => _esFavorito;
  int get cantidad => _cantidad;

  Future<String> _resolveTenant() async {
    final fromSession = _session?.tenant.trim();
    if (fromSession != null && fromSession.isNotEmpty) {
      return fromSession;
    }
    return (await _localDatabase?.readTenant()) ?? 'demo';
  }

  int stockDeVarianteEnSucursal(
    DisponibilidadSucursal sucursal,
    VariantePrenda? variante,
  ) {
    if (variante == null) {
      return sucursal.variantes.fold<int>(
        0,
        (sum, v) => sum + v.stockDisponible,
      );
    }
    for (final v in sucursal.variantes) {
      if (v.varianteId == variante.id ||
          (v.sku.isNotEmpty && v.sku == variante.sku)) {
        return v.stockDisponible;
      }
    }
    return 0;
  }

  int stockEnSucursal(DisponibilidadSucursal sucursal) =>
      stockDeVarianteEnSucursal(sucursal, _varianteSeleccionada);

  int stockTotalParaVariante(VariantePrenda? variante) => _sucursales.fold<int>(
    0,
    (sum, suc) => sum + stockDeVarianteEnSucursal(suc, variante),
  );

  int get stockTotalVarianteSeleccionada =>
      stockTotalParaVariante(_varianteSeleccionada);

  int get _maxCantidadPermitida {
    if (_stockCargado && stockTotalVarianteSeleccionada > 0) {
      return math.min(20, stockTotalVarianteSeleccionada);
    }
    return 20;
  }

  Future<void> cargarDetalle(String prendaId, {Prenda? initialPrenda}) async {
    _error = null;
    _actionError = null;
    _cantidad = 1;
    _usuarioEligioVariante = false;

    if (initialPrenda != null) {
      _prenda = initialPrenda;
      _varianteSeleccionada = _elegirVarianteInicial(initialPrenda.variantes);
      _loading = false;
    } else {
      _loading = true;
    }
    _loadingDisponibilidad = true;
    notifyListeners();

    final isSessionOnline = _session?.isOnline ?? true;
    if (isSessionOnline) {
      try {
        final res = await _apiClient.get('/catalogo/prendas/$prendaId');
        if (res is Map) {
          final refreshed = Prenda.fromJson(Map<String, dynamic>.from(res));
          _prenda = refreshed;
          _varianteSeleccionada = _resolverVarianteTrasRefresco(
            refreshed.variantes,
          );
        }
        _loading = false;
      } catch (e) {
        if (isNetworkError(e)) {
          _session?.handleNetworkLost();
        }
        if (_prenda == null && _localDatabase != null) {
          try {
            final cachedPrenda = await _localDatabase.readPrendaSnapshot(
              await _resolveTenant(),
              prendaId,
            );
            if (cachedPrenda != null) {
              _prenda = cachedPrenda;
              _varianteSeleccionada = _resolverVarianteTrasRefresco(
                cachedPrenda.variantes,
              );
            }
          } catch (_) {}
        }
        _loading = false;
        if (_prenda == null) {
          _error = ApiException.fromObject(
            e,
            fallback: 'No se pudo cargar el detalle de la prenda.',
          ).message;
        }
      }
    } else {
      if (_prenda == null && _localDatabase != null) {
        try {
          final cachedPrenda = await _localDatabase.readPrendaSnapshot(
            await _resolveTenant(),
            prendaId,
          );
          if (cachedPrenda != null) {
            _prenda = cachedPrenda;
            _varianteSeleccionada = _resolverVarianteTrasRefresco(
              cachedPrenda.variantes,
            );
          } else {
            _error =
                'Sin conexion y la prenda no esta en el catalogo local descargado.';
          }
        } catch (_) {
          _error =
              'Sin conexion y la prenda no esta en el catalogo local descargado.';
        }
      }
      _loading = false;
    }
    notifyListeners();

    if (_prenda != null) {
      await cargarDisponibilidad(prendaId);
    } else {
      _loadingDisponibilidad = false;
      notifyListeners();
    }
  }

  Future<void> cargarDisponibilidad(String prendaId) async {
    _loadingDisponibilidad = true;
    notifyListeners();

    final isSessionOnline = _session?.isOnline ?? true;
    if (isSessionOnline) {
      try {
        final dispRes = await _apiClient.get(
          '/inventario/prendas/$prendaId/disponibilidad',
        );
        if (dispRes is Map) {
          final mapRes = Map<String, dynamic>.from(dispRes);
          final disponibilidad = DisponibilidadPrenda.fromJson(mapRes);
          _sucursales = disponibilidad.sucursales;
          _stockCargado = true;
          _usandoStockLocal = false;

          if (_localDatabase != null && mapRes['sucursales'] is List) {
            try {
              await _localDatabase.saveDisponibilidadPrenda(
                await _resolveTenant(),
                prendaId,
                mapRes,
              );
            } catch (_) {}
          }
          _autoPickVariantIfNeeded();
          _loadingDisponibilidad = false;
          notifyListeners();
          return;
        }
      } catch (e) {
        if (isNetworkError(e)) {
          _session?.handleNetworkLost();
        }
      }
    }

    await _cargarDisponibilidadDesdeLocal(prendaId);
    _loadingDisponibilidad = false;
    notifyListeners();
  }

  Future<void> _cargarDisponibilidadDesdeLocal(String prendaId) async {
    final db = _localDatabase;
    if (db == null) return;
    try {
      final localDisp = await db.buildDisponibilidadOffline(
        await _resolveTenant(),
        prendaId,
        prenda: _prenda,
      );
      if (localDisp != null && localDisp.sucursales.isNotEmpty) {
        _sucursales = localDisp.sucursales;
        _stockCargado = true;
        _usandoStockLocal = true;
        _autoPickVariantIfNeeded();
      } else {
        _usandoStockLocal = !(_session?.isOnline ?? true);
      }
    } catch (_) {
      _usandoStockLocal = !(_session?.isOnline ?? true);
    }
  }

  void _autoPickVariantIfNeeded() {
    if (!_usuarioEligioVariante &&
        _prenda != null &&
        _prenda!.variantes.isNotEmpty &&
        stockTotalParaVariante(_varianteSeleccionada) <= 0) {
      for (final v in _prenda!.variantes) {
        if (stockTotalParaVariante(v) > 0) {
          _varianteSeleccionada = v;
          break;
        }
      }
    }
  }

  VariantePrenda? _elegirVarianteInicial(List<VariantePrenda> variantes) {
    if (variantes.isEmpty) {
      return null;
    }
    for (final v in variantes) {
      if (v.estado == 'activa') {
        return v;
      }
    }
    return variantes.first;
  }

  VariantePrenda? _resolverVarianteTrasRefresco(List<VariantePrenda> variantes) {
    if (variantes.isEmpty) {
      return null;
    }
    final currentId = _varianteSeleccionada?.id;
    if (currentId != null) {
      for (final v in variantes) {
        if (v.id == currentId) {
          return v;
        }
      }
    }
    return _elegirVarianteInicial(variantes);
  }

  void seleccionarVariante(VariantePrenda v) {
    _varianteSeleccionada = v;
    _usuarioEligioVariante = true;
    _cantidad = 1;
    _actionError = null;
    notifyListeners();
  }

  void incrementarCantidad() {
    if (_cantidad < _maxCantidadPermitida) {
      _cantidad++;
      notifyListeners();
    }
  }

  void decrementarCantidad() {
    if (_cantidad > 1) {
      _cantidad--;
      notifyListeners();
    }
  }

  void toggleFavorito() {
    _esFavorito = !_esFavorito;
    notifyListeners();
  }

  Future<bool> agregarAlCarrito() async {
    final variante = _varianteSeleccionada;
    if (variante == null) {
      _actionError = 'Seleccione una talla y color antes de continuar.';
      notifyListeners();
      return false;
    }

    _submitting = true;
    _actionError = null;
    notifyListeners();

    try {
      await _apiClient.post('/carrito/items', {
        'variante_id': variante.id,
        'cantidad': _cantidad,
      });
      _submitting = false;
      notifyListeners();
      return true;
    } catch (e) {
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo agregar la prenda al carrito.',
      ).message;
      notifyListeners();
      return false;
    }
  }

  Future<Map<String, dynamic>?> crearReserva({
    required String sucursalId,
    required DateTime fechaVisita,
  }) async {
    final variante = _varianteSeleccionada;
    if (variante == null) {
      _actionError = 'Seleccione una talla y color antes de reservar.';
      notifyListeners();
      return null;
    }

    _submitting = true;
    _actionError = null;
    notifyListeners();

    final onlineAtStart = _session?.isOnline ?? true;
    if (!onlineAtStart && _localDatabase != null) {
      return _registrarReservaOfflineLocal(
        sucursalId: sucursalId,
        fechaVisita: fechaVisita,
        variante: variante,
      );
    }

    try {
      final res = await _apiClient.post(
        '/reservas',
        {
          'sucursal_id': sucursalId,
          'fecha_visita': fechaVisita.toUtc().toIso8601String(),
          'items': [
            {'variante_id': variante.id, 'cantidad': _cantidad},
          ],
        },
        {'Idempotency-Key': generateUuidV4()},
      );
      _submitting = false;
      notifyListeners();
      await cargarDisponibilidad(_prenda?.id ?? variante.prendaId);
      return Map<String, dynamic>.from(res as Map);
    } catch (e) {
      if ((isNetworkError(e) || !(_session?.isOnline ?? true)) &&
          _localDatabase != null) {
        _session?.handleNetworkLost();
        return _registrarReservaOfflineLocal(
          sucursalId: sucursalId,
          fechaVisita: fechaVisita,
          variante: variante,
        );
      }
      _submitting = false;
      _actionError = ApiException.fromObject(
        e,
        fallback: 'No se pudo registrar la reserva.',
      ).message;
      notifyListeners();
      return null;
    }
  }

  Future<Map<String, dynamic>?> _registrarReservaOfflineLocal({
    required String sucursalId,
    required DateTime fechaVisita,
    required VariantePrenda variante,
  }) async {
    final db = _localDatabase;
    if (db == null) {
      _submitting = false;
      _actionError = 'No hay almacenamiento local disponible.';
      notifyListeners();
      return null;
    }

    String? sucursalNombre;
    for (final s in _sucursales) {
      if (s.sucursalId == sucursalId) {
        sucursalNombre = s.nombre;
        break;
      }
    }

    final offlineCtrl = CU26RegistrarReservaOfflineController(db);
    try {
      final uuid = await offlineCtrl.registrarReservaOffline(
        sucursalId: sucursalId,
        sucursalNombre: sucursalNombre,
        fechaVisita: fechaVisita,
        probador: true,
        items: [
          {
            'variante_id': variante.id,
            'cantidad': _cantidad,
            'prenda_nombre': _prenda?.nombre ?? '',
            'talla': variante.tallaNombre ?? '',
            'color': variante.colorNombre ?? '',
            'sku': variante.sku,
          },
        ],
      );
      if (uuid == null) {
        _submitting = false;
        _actionError =
            offlineCtrl.error ?? 'No se pudo guardar la reserva offline.';
        notifyListeners();
        return null;
      }

      await _session?.refreshPendingOperations();
      _usandoStockLocal = true;
      _submitting = false;
      notifyListeners();
      return {
        'id': uuid,
        'codigo': 'RES-OFF-${uuid.substring(0, 6).toUpperCase()}',
        'sucursal_id': sucursalId,
        'sucursal_nombre': sucursalNombre ?? 'Sucursal local',
        'fecha_visita': fechaVisita.toUtc().toIso8601String(),
        'estado': 'pendiente_sync',
        'offline': true,
      };
    } finally {
      offlineCtrl.dispose();
    }
  }
}
