import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import 'detalle_producto_controller.dart';

class DetalleProductoScreen extends StatefulWidget {
  final ApiClient apiClient;
  final String prendaId;

  const DetalleProductoScreen({
    super.key,
    required this.apiClient,
    required this.prendaId,
  });

  @override
  State<DetalleProductoScreen> createState() => _DetalleProductoScreenState();
}

class _DetalleProductoScreenState extends State<DetalleProductoScreen> {
  late final DetalleProductoController _controller;

  @override
  void initState() {
    super.initState();
    _controller = DetalleProductoController(widget.apiClient);
    _controller.cargarDetalle(widget.prendaId);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final prenda = _controller.prenda;
        return Scaffold(
          appBar: AppBar(
            title: Text(prenda?.nombre ?? 'Detalle de Prenda (CU-14)'),
            actions: [
              IconButton(
                icon: Icon(
                  _controller.esFavorito ? Icons.favorite : Icons.favorite_border,
                  color: _controller.esFavorito ? Colors.red : null,
                ),
                onPressed: _controller.toggleFavorito,
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : prenda == null
                      ? const Center(child: Text('Prenda no encontrada'))
                      : SingleChildScrollView(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                height: 260,
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade100,
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: prenda.imagenUrl != null
                                    ? ClipRRect(
                                        borderRadius: BorderRadius.circular(16),
                                        child: Image.network(
                                          prenda.imagenUrl!,
                                          fit: BoxFit.cover,
                                        ),
                                      )
                                    : const Icon(Icons.checkroom, size: 80, color: Colors.grey),
                              ),
                              const SizedBox(height: 16),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    prenda.codigo,
                                    style: TextStyle(
                                      color: Colors.grey.shade600,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  Text(
                                    'BOB ${prenda.precioBase}',
                                    style: const TextStyle(
                                      fontSize: 22,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.indigo,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                prenda.nombre,
                                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                              ),
                              if (prenda.descripcion != null) ...[
                                const SizedBox(height: 8),
                                Text(
                                  prenda.descripcion!,
                                  style: TextStyle(color: Colors.grey.shade700),
                                ),
                              ],
                              const SizedBox(height: 20),
                              const Text(
                                'Variantes disponibles (Talla / Color):',
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 8),
                              Wrap(
                                spacing: 8,
                                children: prenda.variantes.map((v) {
                                  final isSelected = _controller.varianteSeleccionada?.id == v.id;
                                  return ChoiceChip(
                                    label: Text('${v.tallaNombre ?? "Talla"} - ${v.colorNombre ?? "Color"}'),
                                    selected: isSelected,
                                    onSelected: (_) => _controller.seleccionarVariante(v),
                                  );
                                }).toList(),
                              ),
                            ],
                          ),
                        ),
        );
      },
    );
  }
}

