import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_client.dart';
import '../../../core/session/session_controller.dart';
import '../../../core/utils/prenda_image_helper.dart';
import 'checkout_controller.dart';

class CheckoutScreen extends StatefulWidget {
  final ApiClient apiClient;
  final SessionController? session;

  const CheckoutScreen({super.key, required this.apiClient, this.session});

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  late final CheckoutController _controller;
  final _cuponCtrl = TextEditingController();
  final _direccionCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _controller = CheckoutController(widget.apiClient);
    _cargar();
  }

  @override
  void dispose() {
    _controller.dispose();
    _cuponCtrl.dispose();
    _direccionCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    await _controller.cargarCarrito(
      empresaSlug: widget.session?.tenant ?? 'demo',
    );
  }

  double _toDouble(dynamic value, [double fallback = 0]) {
    if (value == null) return fallback;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString().replaceAll(',', '.')) ?? fallback;
  }

  Future<void> _onPagar() async {
    final resultado = await _controller.realizarPago(
      cupon: _cuponCtrl.text,
      direccionId: _direccionCtrl.text,
    );
    if (!mounted) return;

    if (resultado == null) {
      if (_controller.actionError != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_controller.actionError!)),
        );
      }
      return;
    }

    if (resultado.requiereAccionExterna) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            resultado.mensaje ??
                'Orden ${resultado.numero} generada pendiente de confirmación.',
          ),
        ),
      );
      return;
    }

    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('¡Compra Confirmada!'),
        content: Text(
          'Orden N° ${resultado.numero} confirmada.\n'
          'Total pagado: BOB ${resultado.totalAPagar.toStringAsFixed(2)}\n'
          'El inventario fue actualizado correctamente.',
        ),
        actions: [
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _cuponCtrl.clear();
              _cargar();
            },
            child: const Text('Aceptar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final items = _controller.items;
        final validacion = _controller.validacion;
        final faltantes =
            (validacion?['lineas_faltantes'] as List<dynamic>? ?? const []);

        final subtotal = validacion != null
            ? _toDouble(validacion['subtotal'], _controller.subtotalCarrito)
            : _controller.subtotalCarrito;
        final descuento = validacion != null
            ? _toDouble(validacion['descuento'])
            : 0.0;
        final impuesto = validacion != null
            ? _toDouble(validacion['impuesto'])
            : double.parse((subtotal * 0.13).toStringAsFixed(2));
        final costoEnvio = validacion != null
            ? _toDouble(validacion['costo_envio'])
            : (_controller.tipoEntrega == 'envio' ? 20.0 : 0.0);
        final totalEstimado = validacion != null
            ? _toDouble(validacion['total_a_pagar'])
            : (subtotal - descuento + costoEnvio + impuesto);

        return Scaffold(
          appBar: AppBar(
            title: const Text('Carrito y Checkout'),
            actions: [
              IconButton(
                tooltip: 'Actualizar',
                onPressed: _controller.loading ? null : _cargar,
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_controller.error!, textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: _cargar,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Reintentar'),
                        ),
                      ],
                    ),
                  ),
                )
              : items.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.shopping_bag_outlined,
                          size: 64,
                          color: Colors.grey.shade400,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Tu carrito de compras está vacío.',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Explora el catálogo y selecciona una prenda para agregarla o comprarla.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                        const SizedBox(height: 16),
                        FilledButton.icon(
                          onPressed: () => context.push('/catalogo'),
                          icon: const Icon(Icons.checkroom),
                          label: const Text('Ir al catálogo'),
                        ),
                      ],
                    ),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_controller.pendingOrderNotice != null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.amber.shade300),
                        ),
                        child: Text(
                          _controller.pendingOrderNotice!,
                          style: TextStyle(
                            color: Colors.amber.shade900,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                    if (_controller.actionError != null &&
                        _controller.pendingOrderNotice == null) ...[
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Text(
                          _controller.actionError!,
                          style: TextStyle(
                            color: Colors.red.shade900,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                    ...items.map((raw) {
                      final it = Map<String, dynamic>.from(raw as Map);
                      final itemId = it['id']?.toString() ?? '';
                      final qty = (it['cantidad'] as num?)?.toInt() ?? 1;
                      final subtotalItem = _toDouble(it['subtotal']);
                      final nombre = it['prenda_nombre']?.toString() ?? 'Prenda';
                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        child: Padding(
                          padding: const EdgeInsets.all(10),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: SizedBox(
                                  width: 64,
                                  height: 76,
                                  child: PrendaNetworkImage(
                                    imagenUrl: it['imagen_url']?.toString(),
                                    nombre: nombre,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      nombre,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${it['talla'] ?? '-'} / ${it['color'] ?? '-'} • SKU: ${it['sku'] ?? '-'}',
                                      style: TextStyle(
                                        color: Colors.grey.shade600,
                                        fontSize: 12,
                                      ),
                                    ),
                                    const SizedBox(height: 6),
                                    Row(
                                      children: [
                                        IconButton(
                                          visualDensity: VisualDensity.compact,
                                          onPressed: _controller.submitting ||
                                                  itemId.isEmpty
                                              ? null
                                              : () => _controller
                                                  .actualizarCantidadItem(
                                                    itemId,
                                                    qty - 1,
                                                  ),
                                          icon: const Icon(
                                            Icons.remove_circle_outline,
                                          ),
                                        ),
                                        Text(
                                          '$qty',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                        IconButton(
                                          visualDensity: VisualDensity.compact,
                                          onPressed: _controller.submitting ||
                                                  itemId.isEmpty
                                              ? null
                                              : () => _controller
                                                  .actualizarCantidadItem(
                                                    itemId,
                                                    qty + 1,
                                                  ),
                                          icon: const Icon(
                                            Icons.add_circle_outline,
                                          ),
                                        ),
                                        const Spacer(),
                                        Text(
                                          'BOB ${subtotalItem.toStringAsFixed(2)}',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                tooltip: 'Quitar del carrito',
                                onPressed:
                                    _controller.submitting || itemId.isEmpty
                                    ? null
                                    : () => _controller.eliminarItem(itemId),
                                icon: const Icon(
                                  Icons.delete_outline,
                                  color: Colors.red,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                    const SizedBox(height: 8),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Opciones de Entrega',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            RadioGroup<String>(
                              groupValue: _controller.tipoEntrega,
                              onChanged: (val) {
                                if (val != null) {
                                  _controller.setTipoEntrega(val);
                                  if (val == 'recojo' &&
                                      _controller.sucursalRetiroId != null) {
                                    _controller.validarCheckout(
                                      cupon: _cuponCtrl.text,
                                      direccionId: _direccionCtrl.text,
                                      silent: true,
                                    );
                                  }
                                }
                              },
                              child: const Column(
                                children: [
                                  RadioListTile<String>(
                                    contentPadding: EdgeInsets.zero,
                                    title: Text(
                                      'Recojo en sucursal física (Gratis)',
                                    ),
                                    value: 'recojo',
                                  ),
                                  RadioListTile<String>(
                                    contentPadding: EdgeInsets.zero,
                                    title: Text('Envío a domicilio (+20 BOB)'),
                                    value: 'envio',
                                  ),
                                ],
                              ),
                            ),
                            if (_controller.tipoEntrega == 'recojo') ...[
                              const SizedBox(height: 8),
                              if (_controller.sucursales.isNotEmpty)
                                DropdownButtonFormField<String>(
                                  initialValue: _controller.sucursalRetiroId,
                                  isExpanded: true,
                                  decoration: const InputDecoration(
                                    labelText: 'Sucursal de recojo',
                                    border: OutlineInputBorder(),
                                  ),
                                  items: _controller.sucursales
                                      .map(
                                        (s) => DropdownMenuItem<String>(
                                          value: s.sucursalId,
                                          child: Text(
                                            '${s.nombre} (${s.ciudad}) • Stock ref: ${_controller.stockPorSucursal[s.sucursalId] ?? 0}',
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      )
                                      .toList(growable: false),
                                  onChanged: _controller.submitting
                                      ? null
                                      : (val) async {
                                          _controller.setSucursalRetiro(val);
                                          if (val != null) {
                                            await _controller.validarCheckout(
                                              cupon: _cuponCtrl.text,
                                              direccionId: _direccionCtrl.text,
                                              silent: true,
                                            );
                                          }
                                        },
                                )
                              else
                                const Text(
                                  'Cargando sucursales disponibles...',
                                  style: TextStyle(color: Colors.grey),
                                ),
                            ] else ...[
                              const SizedBox(height: 8),
                              TextField(
                                controller: _direccionCtrl,
                                onChanged: _controller.setDireccionId,
                                decoration: const InputDecoration(
                                  labelText: 'UUID de dirección de envío',
                                  hintText:
                                      'El envío requiere dirección UUID; usa Recojo si aún no registraste una',
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ],
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                Expanded(
                                  child: TextField(
                                    controller: _cuponCtrl,
                                    onChanged: _controller.setCupon,
                                    decoration: const InputDecoration(
                                      labelText: 'Cupón de descuento',
                                      hintText: 'Opcional (ej. BIENVENIDO10)',
                                      border: OutlineInputBorder(),
                                      isDense: true,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                OutlinedButton(
                                  onPressed: _controller.submitting
                                      ? null
                                      : () => _controller.validarCheckout(
                                          cupon: _cuponCtrl.text,
                                          direccionId: _direccionCtrl.text,
                                        ),
                                  child: const Text('Validar'),
                                ),
                              ],
                            ),
                            if (faltantes.isNotEmpty) ...[
                              const SizedBox(height: 10),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: Colors.red.shade50,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(
                                    color: Colors.red.shade200,
                                  ),
                                ),
                                child: Text(
                                  'Hay ${faltantes.length} producto(s) sin stock suficiente en esta sucursal. Cambia de sucursal o ajusta cantidades.',
                                  style: TextStyle(
                                    color: Colors.red.shade900,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            ],
                            const Divider(height: 24),
                            _SummaryRow(
                              label: 'Subtotal',
                              value: 'BOB ${subtotal.toStringAsFixed(2)}',
                            ),
                            if (descuento > 0)
                              _SummaryRow(
                                label: 'Descuento cupón',
                                value: '-BOB ${descuento.toStringAsFixed(2)}',
                                valueColor: Colors.green.shade700,
                              ),
                            _SummaryRow(
                              label: 'Envío',
                              value: costoEnvio > 0
                                  ? 'BOB ${costoEnvio.toStringAsFixed(2)}'
                                  : 'Gratis',
                            ),
                            _SummaryRow(
                              label: 'IVA (13%)',
                              value: 'BOB ${impuesto.toStringAsFixed(2)}',
                            ),
                            const SizedBox(height: 6),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Total Estimado:',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                Text(
                                  'BOB ${totalEstimado.toStringAsFixed(2)}',
                                  style: TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.primary,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: _controller.submitting ? null : _onPagar,
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      icon: _controller.submitting
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.credit_card),
                      label: Text(
                        _controller.pendingOrder != null
                            ? 'REINTENTAR PAGO (${_controller.pendingOrder!['numero']})'
                            : 'PAGAR CON TARJETA (STRIPE SANDBOX)',
                      ),
                    ),
                  ],
                ),
        );
      },
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({
    required this.label,
    required this.value,
    this.valueColor,
  });

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey.shade700)),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: valueColor,
            ),
          ),
        ],
      ),
    );
  }
}
