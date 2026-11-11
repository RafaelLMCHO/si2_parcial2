import 'package:flutter/material.dart';
import '../../../core/network/api_client.dart';
import '../../../core/utils/prenda_image_helper.dart';
import 'catalogo_admin_controller.dart';

class CatalogoAdminScreen extends StatefulWidget {
  final ApiClient apiClient;

  const CatalogoAdminScreen({super.key, required this.apiClient});

  @override
  State<CatalogoAdminScreen> createState() => _CatalogoAdminScreenState();
}

class _CatalogoAdminScreenState extends State<CatalogoAdminScreen> {
  late final CatalogoAdminController _controller;

  @override
  void initState() {
    super.initState();
    _controller = CatalogoAdminController(widget.apiClient);
    _controller.cargarPrendas();
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
        return Scaffold(
          appBar: AppBar(
            title: const Text('Catálogo Maestro Admin (CU-12)'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _controller.cargarPrendas(),
              ),
            ],
          ),
          body: _controller.loading
              ? const Center(child: CircularProgressIndicator())
              : _controller.error != null
                  ? Center(child: Text('Error: ${_controller.error}'))
                  : _controller.prendas.isEmpty
                      ? const Center(child: Text('No hay prendas en catálogo admin.'))
                      : ListView.separated(
                          itemCount: _controller.prendas.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final p = _controller.prendas[index];
                            final nombre = p['nombre']?.toString() ?? 'Prenda';
                            final categoria = p['categoria_nombre']?.toString();
                            return ListTile(
                              leading: ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: SizedBox(
                                  width: 48,
                                  height: 48,
                                  child: PrendaNetworkImage(
                                    imagenUrl: p['imagen_url']?.toString(),
                                    nombre: nombre,
                                    categoriaNombre: categoria,
                                    iconSize: 22,
                                  ),
                                ),
                              ),
                              title: Text(nombre),
                              subtitle: Text(
                                'Código: ${p['codigo']} | Cat: ${categoria ?? '-'}\nPrecio: BOB ${p['precio_base']}',
                              ),
                            );
                          },
                        ),
        );
      },
    );
  }
}

