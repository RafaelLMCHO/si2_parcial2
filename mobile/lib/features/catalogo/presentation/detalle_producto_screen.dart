import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/network/api_client.dart';
import '../../../core/routing/role_permissions.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/utils/prenda_image_helper.dart';
import '../../inventario/data/inventario_models.dart';
import '../data/catalogo_models.dart';
import 'detalle_producto_controller.dart';

class DetalleProductoScreen extends StatefulWidget {
  final ApiClient apiClient;
  final String prendaId;
  final Prenda? initialPrenda;
  final SessionController? session;

  const DetalleProductoScreen({
    super.key,
    required this.apiClient,
    required this.prendaId,
    this.initialPrenda,
    this.session,
  });

  @override
  State<DetalleProductoScreen> createState() => _DetalleProductoScreenState();
}

class _DetalleProductoScreenState extends State<DetalleProductoScreen> {
  late final DetalleProductoController _controller;

  @override
  void initState() {
    super.initState();
    _controller = DetalleProductoController(
      widget.apiClient,
      localDatabase: widget.session?.database,
      session: widget.session,
    );
    _controller.cargarDetalle(
      widget.prendaId,
      initialPrenda: widget.initialPrenda,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _onAgregarAlCarrito({bool irAlCheckout = false}) async {
    final ok = await _controller.agregarAlCarrito();
    if (!mounted) return;

    if (!ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _controller.actionError ?? 'No se pudo agregar al carrito.',
          ),
        ),
      );
      return;
    }

    if (irAlCheckout) {
      context.push('/checkout');
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Prenda agregada al carrito'),
        action: SnackBarAction(
          label: 'Ver carrito',
          onPressed: () {
            if (mounted) {
              context.push('/checkout');
            }
          },
        ),
      ),
    );
  }

  Future<void> _abrirSheetReserva(Prenda prenda) async {
    if (_controller.sucursales.isEmpty && !_controller.loadingDisponibilidad) {
      await _controller.cargarDisponibilidad(prenda.id);
      if (!mounted) return;
    }

    final sucursales = _controller.sucursales;
    String? selectedSucursalId;
    if (sucursales.isNotEmpty) {
      selectedSucursalId = sucursales
          .firstWhere(
            (s) => _controller.stockEnSucursal(s) >= _controller.cantidad,
            orElse: () => sucursales.first,
          )
          .sucursalId;
    }

    final now = DateTime.now();
    var fechaVisita = DateTime(now.year, now.month, now.day + 1, 15, 0);
    String? sheetError;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (sheetCtx) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                final currentSucursales = _controller.sucursales;
                if (selectedSucursalId == null && currentSucursales.isNotEmpty) {
                  selectedSucursalId = currentSucursales
                      .firstWhere(
                        (s) =>
                            _controller.stockEnSucursal(s) >=
                            _controller.cantidad,
                        orElse: () => currentSucursales.first,
                      )
                      .sucursalId;
                }

                DisponibilidadSucursal? selectedSucursal;
                for (final s in currentSucursales) {
                  if (s.sucursalId == selectedSucursalId) {
                    selectedSucursal = s;
                    break;
                  }
                }
                final stockSucursal = selectedSucursal != null
                    ? _controller.stockEnSucursal(selectedSucursal)
                    : 0;
                final variante = _controller.varianteSeleccionada;

                return SafeArea(
                  child: Padding(
                    padding: EdgeInsets.fromLTRB(
                      20,
                      8,
                      20,
                      MediaQuery.of(ctx).viewInsets.bottom + 20,
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Reservar en tienda',
                          style: Theme.of(ctx).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          '${prenda.nombre} • ${variante?.tallaNombre ?? ''} / ${variante?.colorNombre ?? ''} • Cant: ${_controller.cantidad}',
                          style: Theme.of(ctx).textTheme.bodyMedium?.copyWith(
                            color: Colors.grey.shade700,
                          ),
                        ),
                        const SizedBox(height: 16),
                        if (_controller.loadingDisponibilidad)
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 20),
                            child: Center(child: CircularProgressIndicator()),
                          )
                        else if (currentSucursales.isEmpty)
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.amber.shade50,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.amber.shade200),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _controller.isOffline
                                      ? 'No hay sucursales guardadas en caché local para esta prenda. Conéctese al menos una vez para descargar el catálogo y las sucursales disponibles.'
                                      : 'No se pudo obtener la lista de sucursales disponibles para esta prenda.',
                                ),
                                const SizedBox(height: 8),
                                TextButton.icon(
                                  onPressed: () => _controller
                                      .cargarDisponibilidad(prenda.id),
                                  icon: const Icon(Icons.refresh),
                                  label: const Text('Reintentar'),
                                ),
                              ],
                            ),
                          )
                        else ...[
                          if (_controller.usandoStockLocal)
                            Container(
                              padding: const EdgeInsets.all(10),
                              margin: const EdgeInsets.only(bottom: 12),
                              decoration: BoxDecoration(
                                color: Colors.amber.shade50,
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(color: Colors.amber.shade300),
                              ),
                              child: const Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(
                                    Icons.wifi_off,
                                    size: 18,
                                    color: Colors.brown,
                                  ),
                                  SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      'Modo sin conexión: mostrando sucursales y stock guardados localmente. La reserva se guardará en cola y se confirmará al recuperar conexión.',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Colors.brown,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          DropdownButtonFormField<String>(
                            key: ValueKey('suc-${selectedSucursalId ?? 'none'}'),
                            initialValue: selectedSucursalId,
                            isExpanded: true,
                            decoration: const InputDecoration(
                              labelText: 'Sucursal de visita',
                              border: OutlineInputBorder(),
                            ),
                            items: currentSucursales
                                .map(
                                  (suc) => DropdownMenuItem<String>(
                                    value: suc.sucursalId,
                                    child: Text(
                                      '${suc.nombre} (${suc.ciudad}) • Stock: ${_controller.stockEnSucursal(suc)}',
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                )
                                .toList(growable: false),
                            onChanged: (val) {
                              setSheetState(() {
                                selectedSucursalId = val;
                                sheetError = null;
                              });
                            },
                          ),
                          const SizedBox(height: 12),
                          if (selectedSucursal != null &&
                              stockSucursal < _controller.cantidad)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: Text(
                                _controller.usandoStockLocal
                                    ? 'Stock local estimado: $stockSucursal uds. Al sincronizar se validará la disponibilidad real en tienda (CU-32).'
                                    : 'Esta sucursal no tiene suficiente stock ($stockSucursal disp.) para la variante seleccionada.',
                                style: TextStyle(
                                  color: _controller.usandoStockLocal
                                      ? Colors.brown.shade700
                                      : Colors.red.shade700,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton.icon(
                                  icon: const Icon(Icons.calendar_today),
                                  label: Text(
                                    DateFormat('dd/MM/yyyy').format(fechaVisita),
                                  ),
                                  onPressed: () async {
                                    final pickedDate = await showDatePicker(
                                      context: ctx,
                                      initialDate: fechaVisita,
                                      firstDate: DateTime.now(),
                                      lastDate: DateTime.now().add(
                                        const Duration(days: 30),
                                      ),
                                    );
                                    if (!ctx.mounted) return;
                                    if (pickedDate != null) {
                                      setSheetState(() {
                                        fechaVisita = DateTime(
                                          pickedDate.year,
                                          pickedDate.month,
                                          pickedDate.day,
                                          fechaVisita.hour,
                                          fechaVisita.minute,
                                        );
                                        sheetError = null;
                                      });
                                    }
                                  },
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: OutlinedButton.icon(
                                  icon: const Icon(Icons.access_time),
                                  label: Text(
                                    DateFormat('HH:mm').format(fechaVisita),
                                  ),
                                  onPressed: () async {
                                    final pickedTime = await showTimePicker(
                                      context: ctx,
                                      initialTime: TimeOfDay.fromDateTime(
                                        fechaVisita,
                                      ),
                                    );
                                    if (!ctx.mounted) return;
                                    if (pickedTime != null) {
                                      setSheetState(() {
                                        fechaVisita = DateTime(
                                          fechaVisita.year,
                                          fechaVisita.month,
                                          fechaVisita.day,
                                          pickedTime.hour,
                                          pickedTime.minute,
                                        );
                                        sheetError = null;
                                      });
                                    }
                                  },
                                ),
                              ),
                            ],
                          ),
                        ],
                        if (sheetError != null) ...[
                          const SizedBox(height: 10),
                          Text(
                            sheetError!,
                            style: TextStyle(
                              color: Colors.red.shade700,
                              fontSize: 13,
                            ),
                          ),
                        ],
                        const SizedBox(height: 16),
                        FilledButton.icon(
                          onPressed:
                              _controller.submitting ||
                                  selectedSucursalId == null ||
                                  (!_controller.usandoStockLocal &&
                                      stockSucursal < _controller.cantidad)
                              ? null
                              : () async {
                                  if (!fechaVisita.isAfter(DateTime.now())) {
                                    setSheetState(() {
                                      sheetError =
                                          'La fecha y hora de visita debe ser posterior al momento actual.';
                                    });
                                    return;
                                  }

                                  final reserva = await _controller.crearReserva(
                                    sucursalId: selectedSucursalId!,
                                    fechaVisita: fechaVisita,
                                  );
                                  if (!mounted) return;
                                  if (reserva == null) {
                                    if (!ctx.mounted) return;
                                    setSheetState(() {
                                      sheetError =
                                          _controller.actionError ??
                                          'No se pudo completar la reserva.';
                                    });
                                    return;
                                  }

                                  if (sheetCtx.mounted) {
                                    Navigator.of(sheetCtx).pop();
                                  }
                                  final isOfflineRes = reserva['offline'] == true;
                                  await showDialog<void>(
                                    context: this.context,
                                    builder: (dialogCtx) => AlertDialog(
                                      title: Text(
                                        isOfflineRes
                                            ? 'Reserva Guardada Offline'
                                            : 'Reserva Confirmada',
                                      ),
                                      content: Text(
                                        'Código${isOfflineRes ? ' local' : ''}: ${reserva['codigo'] ?? '-'}\n'
                                        'Sucursal: ${reserva['sucursal_nombre'] ?? selectedSucursal?.nombre ?? '-'}\n'
                                        'Visita: ${DateFormat('dd/MM/yyyy HH:mm').format(fechaVisita)}'
                                        '${isOfflineRes ? '\n\nGuardada en la cola local del dispositivo. Se sincronizará automáticamente al recuperar conexión.' : ''}',
                                      ),
                                      actions: [
                                        TextButton(
                                          onPressed: () =>
                                              Navigator.of(dialogCtx).pop(),
                                          child: const Text('Cerrar'),
                                        ),
                                        FilledButton(
                                          onPressed: () {
                                            Navigator.of(dialogCtx).pop();
                                            context.push('/reservas');
                                          },
                                          child: const Text('Ver mis reservas'),
                                        ),
                                      ],
                                    ),
                                  );
                                },
                          icon: _controller.submitting
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Icon(Icons.event_available),
                          label: Text(
                            _controller.submitting
                                ? 'Registrando reserva...'
                                : 'Confirmar reserva',
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  Color? _parseHexColor(String? raw) {
    final text = raw?.trim().replaceFirst('#', '');
    if (text == null || (text.length != 6 && text.length != 8)) {
      return null;
    }
    final value = int.tryParse(text, radix: 16);
    if (value == null) {
      return null;
    }
    return Color(text.length == 6 ? 0xFF000000 | value : value);
  }

  @override
  Widget build(BuildContext context) {
    final rol = widget.session?.user?.rol;
    final allowCheckout =
        widget.session == null || canAccessRoute(rol, '/checkout');
    final allowReservar =
        widget.session == null ||
        ((rol == 'cliente' || rol == 'administrador') &&
            canAccessRoute(rol, '/reservas'));
    final allowDisponibilidad =
        widget.session == null || canAccessRoute(rol, '/disponibilidad');

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final prenda = _controller.prenda;
        final variante = _controller.varianteSeleccionada;
        final precioMostrar = variante != null && variante.precioVenta > 0
            ? variante.precioVenta
            : (prenda?.precioBase ?? 0);

        return Scaffold(
          appBar: AppBar(
            title: Text(prenda?.nombre ?? 'Detalle de Prenda'),
            actions: [
              if (allowCheckout)
                IconButton(
                  tooltip: 'Carrito y Checkout',
                  onPressed: () => context.push('/checkout'),
                  icon: const Icon(Icons.shopping_bag_outlined),
                ),
              IconButton(
                tooltip: 'Favorito',
                icon: Icon(
                  _controller.esFavorito
                      ? Icons.favorite
                      : Icons.favorite_border,
                  color: _controller.esFavorito ? Colors.red : null,
                ),
                onPressed: _controller.toggleFavorito,
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null && prenda == null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          _controller.error!,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: () => _controller.cargarDetalle(
                            widget.prendaId,
                            initialPrenda: widget.initialPrenda,
                          ),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Reintentar'),
                        ),
                      ],
                    ),
                  ),
                )
              : prenda == null
              ? const Center(child: Text('Prenda no encontrada'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: SizedBox(
                          height: 260,
                          width: double.infinity,
                          child: PrendaNetworkImage(
                            imagenUrl: prenda.imagenUrl,
                            nombre: prenda.nombre,
                            categoriaNombre: prenda.categoriaNombre,
                            iconSize: 72,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Flexible(
                            child: Text(
                              [
                                    prenda.codigo,
                                    prenda.marca,
                                    prenda.categoriaNombre,
                                  ]
                                  .where((e) => e != null && e.isNotEmpty)
                                  .join(' • '),
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${prenda.moneda} ${precioMostrar.toStringAsFixed(2)}',
                            style: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        prenda.nombre,
                        style: const TextStyle(
                          fontSize: 21,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (prenda.descripcion != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          prenda.descripcion!,
                          style: TextStyle(color: Colors.grey.shade700),
                        ),
                      ],
                      const SizedBox(height: 18),
                      const Text(
                        'Variantes disponibles (Talla / Color):',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      if (prenda.variantes.isEmpty)
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.amber.shade50,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Text(
                            'No hay variantes disponibles para esta prenda.',
                          ),
                        )
                      else ...[
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: prenda.variantes
                              .map((v) {
                                final isSelected = variante?.id == v.id;
                                final parsedColor = _parseHexColor(v.colorHex);
                                return ChoiceChip(
                                  avatar: parsedColor != null
                                      ? CircleAvatar(
                                          radius: 7,
                                          backgroundColor: parsedColor,
                                        )
                                      : null,
                                  label: Text(
                                    '${v.tallaNombre ?? "Talla"} - ${v.colorNombre ?? "Color"}',
                                  ),
                                  selected: isSelected,
                                  onSelected: (_) =>
                                      _controller.seleccionarVariante(v),
                                );
                              })
                              .toList(growable: false),
                        ),
                        if (variante != null) ...[
                          const SizedBox(height: 10),
                          Wrap(
                            spacing: 10,
                            runSpacing: 6,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              Text(
                                'SKU: ${variante.sku}',
                                style: TextStyle(
                                  color: Colors.grey.shade700,
                                  fontSize: 13,
                                ),
                              ),
                              if (_controller.stockCargado)
                                Chip(
                                  visualDensity: VisualDensity.compact,
                                  label: Text(
                                    _controller.stockTotalVarianteSeleccionada > 0
                                        ? 'Stock ${_controller.usandoStockLocal ? "local" : "en tiendas"}: ${_controller.stockTotalVarianteSeleccionada} uds'
                                        : (_controller.usandoStockLocal
                                              ? 'Sin stock en caché local'
                                              : 'Sin stock en tiendas'),
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                      color:
                                          _controller
                                                  .stockTotalVarianteSeleccionada >
                                              0
                                          ? Colors.green.shade800
                                          : Colors.red.shade800,
                                    ),
                                  ),
                                  backgroundColor:
                                      _controller
                                              .stockTotalVarianteSeleccionada >
                                          0
                                      ? Colors.green.shade50
                                      : Colors.red.shade50,
                                ),
                            ],
                          ),
                        ],
                        const SizedBox(height: 16),
                        if (allowCheckout || allowReservar)
                          Row(
                            children: [
                              const Text(
                                'Cantidad:',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(width: 12),
                              IconButton.outlined(
                                onPressed: _controller.cantidad > 1 &&
                                        !_controller.submitting
                                    ? _controller.decrementarCantidad
                                    : null,
                                icon: const Icon(Icons.remove),
                              ),
                              Padding(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 14,
                                ),
                                child: Text(
                                  '${_controller.cantidad}',
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                              IconButton.outlined(
                                onPressed: !_controller.submitting
                                    ? _controller.incrementarCantidad
                                    : null,
                                icon: const Icon(Icons.add),
                              ),
                            ],
                          ),
                        const SizedBox(height: 16),
                        if (allowCheckout)
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton.icon(
                                  onPressed: _controller.submitting ||
                                          variante == null
                                      ? null
                                      : () => _onAgregarAlCarrito(),
                                  icon: const Icon(Icons.add_shopping_cart),
                                  label: const Text('Agregar al carrito'),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: FilledButton.icon(
                                  onPressed: _controller.submitting ||
                                          variante == null
                                      ? null
                                      : () => _onAgregarAlCarrito(
                                          irAlCheckout: true,
                                        ),
                                  icon: const Icon(Icons.payment),
                                  label: const Text('Comprar ahora'),
                                ),
                              ),
                            ],
                          ),
                        if (allowReservar) ...[
                          const SizedBox(height: 10),
                          SizedBox(
                            width: double.infinity,
                            child: FilledButton.tonalIcon(
                              onPressed:
                                  _controller.submitting || variante == null
                                  ? null
                                  : () => _abrirSheetReserva(prenda),
                              icon: const Icon(Icons.event_available),
                              label: const Text('Reservar en tienda'),
                            ),
                          ),
                        ],
                      ],
                      if (allowDisponibilidad) ...[
                        const SizedBox(height: 8),
                        SizedBox(
                          width: double.infinity,
                          child: TextButton.icon(
                            onPressed: () => context.push(
                              '/disponibilidad?prenda_id=${Uri.encodeComponent(prenda.id)}&nombre=${Uri.encodeComponent(prenda.nombre)}',
                            ),
                            icon: const Icon(Icons.storefront_outlined),
                            label: const Text('Ver disponibilidad por tienda'),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
        );
      },
    );
  }
}
